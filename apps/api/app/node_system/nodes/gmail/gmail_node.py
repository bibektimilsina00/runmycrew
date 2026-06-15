"""Gmail action node.

Operation-driven node with one credential type (`google_oauth`) and a
condition-driven field set. Mirrors the consolidated Meta nodes — one
trigger node per surface, one action node per surface.

Operations
----------
- `send_email`   — to + subject + body + optional attachments (media field)
- `reply`        — thread_id + body (preserves Re: subject + In-Reply-To)
- `forward`      — message_id + to + optional body
- `search`       — Gmail query string, paginated up to `max_results`
- `get_email`    — fetch full message by id
- `list_labels`  — list every label in the mailbox
- `add_label`    — attach a label to a message
- `remove_label` — detach a label from a message
- `create_label` — make a new label by name
- `mark_read`    — remove the UNREAD system label
- `mark_unread`  — add the UNREAD system label
- `trash`        — move a message to Trash
- `untrash`      — restore from Trash
- `delete`       — permanent delete (`gmail.modify` only allows trash;
                   permanent delete needs `gmail` full scope which is
                   gated behind App Verification — surfaced as an error
                   when the scope is missing)
- `get_profile`  — return the user's Gmail profile (email + counts)
"""

from __future__ import annotations

import base64
import mimetypes
from email.message import EmailMessage
from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

GMAIL_API = "https://gmail.googleapis.com/gmail/v1"


GMAIL_OPS: tuple[str, ...] = (
    "send_email",
    "reply",
    "forward",
    "search",
    "get_email",
    "list_labels",
    "create_label",
    "add_label",
    "remove_label",
    "mark_read",
    "mark_unread",
    "trash",
    "untrash",
    "delete",
    "get_profile",
)


class GmailProperties(BaseModel):
    credential: str | None = None
    operation: str = "send_email"

    # send_email / reply / forward
    to: str | None = None
    cc: str | None = None
    bcc: str | None = None
    subject: str | None = None
    body: str | None = None
    body_type: str = "plain"
    # `attachments` is a `list[media-field-value]` — each item is the
    # discriminated `{type: 'url'|'asset', ...}` dict the MediaRenderer
    # writes, identical to the publish_post media we already resolve in
    # the Meta nodes.
    attachments: Any = None

    # reply / forward source
    thread_id: str | None = None
    message_id: str | None = None

    # search
    query: str | None = None
    max_results: int = 10

    # labels
    label_id: str | None = None
    label_name: str | None = None


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GmailNode(BaseNode[GmailProperties]):
    @classmethod
    def get_properties_model(cls):
        return GmailProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gmail",
            name="Gmail",
            category="integration",
            description=(
                "Send, reply, search, label, and manage Gmail messages via OAuth. "
                "Attachments accept URLs, uploaded files, or items from your Library."
            ),
            icon="si:SiGmail",
            color="#ea4335",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "send_email",
                    "options": [
                        {"label": "Send Email", "value": "send_email"},
                        {"label": "Reply to Thread", "value": "reply"},
                        {"label": "Forward Email", "value": "forward"},
                        {"label": "Search Emails", "value": "search"},
                        {"label": "Get Email", "value": "get_email"},
                        {"label": "List Labels", "value": "list_labels"},
                        {"label": "Create Label", "value": "create_label"},
                        {"label": "Add Label", "value": "add_label"},
                        {"label": "Remove Label", "value": "remove_label"},
                        {"label": "Mark Read", "value": "mark_read"},
                        {"label": "Mark Unread", "value": "mark_unread"},
                        {"label": "Trash", "value": "trash"},
                        {"label": "Untrash", "value": "untrash"},
                        {"label": "Delete (permanent)", "value": "delete"},
                        {"label": "Get Profile", "value": "get_profile"},
                    ],
                },
                # ── send_email / forward — recipient + content ───────
                {
                    "name": "to",
                    "label": "To",
                    "type": "string",
                    "required": True,
                    "placeholder": "person@example.com, {{ $step.from_email }}",
                    "condition": _cond_any("send_email", "forward"),
                },
                {
                    "name": "subject",
                    "label": "Subject",
                    "type": "string",
                    "condition": _cond("send_email"),
                },
                {
                    "name": "body",
                    "label": "Body",
                    "type": "string",
                    "multiline": True,
                    "condition": _cond_any("send_email", "reply", "forward"),
                },
                {
                    "name": "body_type",
                    "label": "Body Format",
                    "type": "options",
                    "default": "plain",
                    "options": [
                        {"label": "Plain Text", "value": "plain"},
                        {"label": "HTML", "value": "html"},
                    ],
                    "mode": "advanced",
                    "condition": _cond_any("send_email", "reply", "forward"),
                },
                {
                    "name": "cc",
                    "label": "CC",
                    "type": "string",
                    "mode": "advanced",
                    "condition": _cond_any("send_email", "forward"),
                },
                {
                    "name": "bcc",
                    "label": "BCC",
                    "type": "string",
                    "mode": "advanced",
                    "condition": _cond_any("send_email", "forward"),
                },
                {
                    "name": "attachments",
                    "label": "Attachments",
                    "type": "list",
                    "description": (
                        "One or more files to attach. Each item is a media "
                        "field — URL, upload, or pick from your Library."
                    ),
                    "typeOptions": {
                        "addButtonText": "Add attachment",
                        "itemType": "media",
                        "accept": "*/*",
                    },
                    "mode": "advanced",
                    "condition": _cond_any("send_email", "reply", "forward"),
                },
                # ── reply — needs source thread + optional message id ─
                {
                    "name": "thread_id",
                    "label": "Thread ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $step.threadId }}",
                    "condition": _cond("reply"),
                },
                {
                    "name": "message_id",
                    "label": "Message ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $step.id }}",
                    "condition": _cond_any(
                        "forward",
                        "get_email",
                        "add_label",
                        "remove_label",
                        "mark_read",
                        "mark_unread",
                        "trash",
                        "untrash",
                        "delete",
                    ),
                },
                # ── search ───────────────────────────────────────────
                {
                    "name": "query",
                    "label": "Search Query",
                    "type": "string",
                    "placeholder": "is:unread from:boss@company.com",
                    "description": ("Standard Gmail search syntax. Empty = recent messages."),
                    "condition": _cond("search"),
                },
                {
                    "name": "max_results",
                    "label": "Max Results",
                    "type": "number",
                    "default": 10,
                    "mode": "advanced",
                    "condition": _cond("search"),
                },
                # ── label ops ────────────────────────────────────────
                {
                    "name": "label_id",
                    "label": "Label ID",
                    "type": "string",
                    "required": True,
                    "description": "Gmail label id (use List Labels first to discover).",
                    "condition": _cond_any("add_label", "remove_label"),
                },
                {
                    "name": "label_name",
                    "label": "Label Name",
                    "type": "string",
                    "required": True,
                    "placeholder": "Followups",
                    "condition": _cond("create_label"),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "threadId", "type": "string"},
                {"label": "messages", "type": "array"},
                {"label": "labelIds", "type": "array"},
                {"label": "snippet", "type": "string"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")
        headers = {"Authorization": f"Bearer {token}"}
        op = self.props.operation
        if op not in GMAIL_OPS:
            return NodeResult(success=False, error=f"Unknown operation: {op}")
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                handler = getattr(self, f"_op_{op}")
                return await handler(client, headers)
        except httpx.HTTPStatusError as e:
            return _http_error(e)
        except Exception as e:  # noqa: BLE001
            logger.error(f"GmailNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    # ── operation handlers ───────────────────────────────────────────

    async def _op_send_email(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> NodeResult:
        if not self.props.to:
            return NodeResult(success=False, error="`to` is required for send_email")
        msg = self._build_message(
            to=self.props.to,
            subject=self.props.subject or "",
            body=self.props.body or "",
            body_type=self.props.body_type or "plain",
            cc=self.props.cc,
            bcc=self.props.bcc,
        )
        await self._attach_files(msg)
        return await self._send_raw(client, headers, msg, thread_id=None)

    async def _op_reply(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        if not self.props.thread_id:
            return NodeResult(success=False, error="`thread_id` is required for reply")
        # Fetch the latest message in the thread to lift Subject / Message-Id
        # for the Re: + In-Reply-To headers Gmail uses to thread the reply.
        meta = await client.get(
            f"{GMAIL_API}/users/me/threads/{self.props.thread_id}",
            headers=headers,
            params={"format": "metadata", "metadataHeaders": ["Subject", "Message-ID", "From"]},
        )
        meta.raise_for_status()
        thread = meta.json()
        last = (thread.get("messages") or [])[-1]
        headers_list = ((last.get("payload") or {}).get("headers")) or []
        h = {h["name"].lower(): h["value"] for h in headers_list if isinstance(h, dict)}
        reply_to = h.get("from") or self.props.to or ""
        original_subject = h.get("subject", "")
        subject = (
            original_subject
            if original_subject.lower().startswith("re:")
            else f"Re: {original_subject}"
        )
        msg = self._build_message(
            to=reply_to,
            subject=subject,
            body=self.props.body or "",
            body_type=self.props.body_type or "plain",
            extra_headers={
                "In-Reply-To": h.get("message-id", ""),
                "References": h.get("message-id", ""),
            },
        )
        await self._attach_files(msg)
        return await self._send_raw(client, headers, msg, thread_id=self.props.thread_id)

    async def _op_forward(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        if not self.props.message_id or not self.props.to:
            return NodeResult(success=False, error="`message_id` and `to` are required for forward")
        # Pull the original raw RFC822 source so the forwarded email retains
        # its full body + attachments verbatim instead of asking the Gmail
        # client to render a Re-encoded copy.
        raw_resp = await client.get(
            f"{GMAIL_API}/users/me/messages/{self.props.message_id}",
            headers=headers,
            params={"format": "raw"},
        )
        raw_resp.raise_for_status()
        original_raw = raw_resp.json().get("raw") or ""
        original_bytes = base64.urlsafe_b64decode(original_raw.encode()) if original_raw else b""
        intro = (self.props.body or "").strip()
        # Compose a new MIME message that quotes the original. Gmail itself
        # does this same wrap-and-attach when you hit Forward.
        fwd = EmailMessage()
        fwd["To"] = self.props.to
        if self.props.cc:
            fwd["Cc"] = self.props.cc
        if self.props.bcc:
            fwd["Bcc"] = self.props.bcc
        fwd["Subject"] = "Fwd: " + (self.props.subject or "")
        body_type = self.props.body_type or "plain"
        if intro:
            if body_type == "html":
                fwd.set_content(intro, subtype="html")
            else:
                fwd.set_content(intro)
        else:
            fwd.set_content("")
        # Attach the original as an RFC822 part — Gmail unpacks it inline.
        if original_bytes:
            fwd.add_attachment(
                original_bytes, maintype="message", subtype="rfc822", filename="forwarded.eml"
            )
        await self._attach_files(fwd)
        return await self._send_raw(client, headers, fwd, thread_id=None)

    async def _op_search(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        params = {
            "q": self.props.query or "",
            "maxResults": max(1, min(self.props.max_results, 500)),
        }
        r = await client.get(f"{GMAIL_API}/users/me/messages", headers=headers, params=params)
        r.raise_for_status()
        data = r.json()
        return NodeResult(
            success=True,
            output_data={
                "messages": data.get("messages", []),
                "count": data.get("resultSizeEstimate", 0),
                "nextPageToken": data.get("nextPageToken"),
            },
        )

    async def _op_get_email(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        if not self.props.message_id:
            return NodeResult(success=False, error="`message_id` is required for get_email")
        r = await client.get(
            f"{GMAIL_API}/users/me/messages/{self.props.message_id}", headers=headers
        )
        r.raise_for_status()
        return NodeResult(success=True, output_data=r.json())

    async def _op_list_labels(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> NodeResult:
        r = await client.get(f"{GMAIL_API}/users/me/labels", headers=headers)
        r.raise_for_status()
        return NodeResult(success=True, output_data={"labels": r.json().get("labels", [])})

    async def _op_create_label(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> NodeResult:
        if not self.props.label_name:
            return NodeResult(success=False, error="`label_name` is required for create_label")
        r = await client.post(
            f"{GMAIL_API}/users/me/labels",
            headers=headers,
            json={
                "name": self.props.label_name,
                "labelListVisibility": "labelShow",
                "messageListVisibility": "show",
            },
        )
        r.raise_for_status()
        return NodeResult(success=True, output_data=r.json())

    async def _op_add_label(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        return await self._modify_labels(client, headers, add=[self.props.label_id or ""])

    async def _op_remove_label(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> NodeResult:
        return await self._modify_labels(client, headers, remove=[self.props.label_id or ""])

    async def _op_mark_read(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        return await self._modify_labels(client, headers, remove=["UNREAD"])

    async def _op_mark_unread(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> NodeResult:
        return await self._modify_labels(client, headers, add=["UNREAD"])

    async def _op_trash(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        if not self.props.message_id:
            return NodeResult(success=False, error="`message_id` is required for trash")
        r = await client.post(
            f"{GMAIL_API}/users/me/messages/{self.props.message_id}/trash", headers=headers
        )
        r.raise_for_status()
        return NodeResult(success=True, output_data=r.json())

    async def _op_untrash(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        if not self.props.message_id:
            return NodeResult(success=False, error="`message_id` is required for untrash")
        r = await client.post(
            f"{GMAIL_API}/users/me/messages/{self.props.message_id}/untrash", headers=headers
        )
        r.raise_for_status()
        return NodeResult(success=True, output_data=r.json())

    async def _op_delete(self, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
        # Permanent delete needs the full `gmail` scope. Our default scope
        # set requests `gmail.modify` only — surface a clear error rather
        # than silently 403 from the API.
        if not self.props.message_id:
            return NodeResult(success=False, error="`message_id` is required for delete")
        r = await client.delete(
            f"{GMAIL_API}/users/me/messages/{self.props.message_id}", headers=headers
        )
        if r.status_code == 403:
            return NodeResult(
                success=False,
                error=(
                    "Permanent delete needs the full Gmail scope. Either Trash this "
                    "message instead (works with the default `gmail.modify` scope) "
                    "or re-connect the credential after granting the broader scope."
                ),
            )
        r.raise_for_status()
        return NodeResult(success=True, output_data={"id": self.props.message_id, "deleted": True})

    async def _op_get_profile(
        self, client: httpx.AsyncClient, headers: dict[str, str]
    ) -> NodeResult:
        r = await client.get(f"{GMAIL_API}/users/me/profile", headers=headers)
        r.raise_for_status()
        return NodeResult(success=True, output_data=r.json())

    # ── helpers ──────────────────────────────────────────────────────

    def _build_message(
        self,
        *,
        to: str,
        subject: str,
        body: str,
        body_type: str = "plain",
        cc: str | None = None,
        bcc: str | None = None,
        extra_headers: dict[str, str] | None = None,
    ) -> EmailMessage:
        msg = EmailMessage()
        msg["To"] = to
        if cc:
            msg["Cc"] = cc
        if bcc:
            msg["Bcc"] = bcc
        msg["Subject"] = subject
        if body_type == "html":
            msg.set_content(body, subtype="html")
        else:
            msg.set_content(body)
        for k, v in (extra_headers or {}).items():
            if v:
                msg[k] = v
        return msg

    async def _attach_files(self, msg: EmailMessage) -> None:
        """Resolve every attachments[] entry (URL / Library asset) into raw
        bytes and bolt it onto the EmailMessage. Uses the same resolver +
        signed-URL infra as the Meta media field."""
        from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

        items = self.props.attachments or []
        if not isinstance(items, list):
            return
        async with httpx.AsyncClient(timeout=60.0, follow_redirects=True) as fetcher:
            for item in items:
                url = resolve_media_field(item)
                if not url:
                    continue
                try:
                    resp = await fetcher.get(url)
                    resp.raise_for_status()
                except Exception as exc:  # noqa: BLE001
                    logger.warning(f"Skipping attachment that failed to fetch: {exc}")
                    continue
                content_type = (
                    resp.headers.get("content-type")
                    or mimetypes.guess_type(url)[0]
                    or "application/octet-stream"
                )
                maintype, _, subtype = content_type.partition("/")
                filename = url.rstrip("/").rsplit("/", 1)[-1].split("?")[0] or "attachment"
                msg.add_attachment(
                    resp.content,
                    maintype=maintype or "application",
                    subtype=subtype or "octet-stream",
                    filename=filename,
                )

    async def _send_raw(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        msg: EmailMessage,
        *,
        thread_id: str | None,
    ) -> NodeResult:
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        body: dict[str, Any] = {"raw": raw}
        if thread_id:
            body["threadId"] = thread_id
        r = await client.post(f"{GMAIL_API}/users/me/messages/send", headers=headers, json=body)
        r.raise_for_status()
        return NodeResult(success=True, output_data=r.json())

    async def _modify_labels(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        *,
        add: list[str] | None = None,
        remove: list[str] | None = None,
    ) -> NodeResult:
        if not self.props.message_id:
            return NodeResult(success=False, error="`message_id` is required for label ops")
        body: dict[str, Any] = {}
        if add:
            body["addLabelIds"] = [x for x in add if x]
        if remove:
            body["removeLabelIds"] = [x for x in remove if x]
        if not body.get("addLabelIds") and not body.get("removeLabelIds"):
            return NodeResult(success=False, error="No label ids supplied to modify")
        r = await client.post(
            f"{GMAIL_API}/users/me/messages/{self.props.message_id}/modify",
            headers=headers,
            json=body,
        )
        r.raise_for_status()
        return NodeResult(success=True, output_data=r.json())


def _http_error(e: httpx.HTTPStatusError) -> NodeResult:
    """Surface Gmail's structured error payload instead of a raw 400."""
    try:
        body = e.response.json()
    except Exception:  # noqa: BLE001
        return NodeResult(
            success=False,
            error=f"Gmail API error {e.response.status_code}: {e.response.text[:200]}",
        )
    err = (body or {}).get("error") or {}
    parts = [err.get("message") or f"Gmail API error {e.response.status_code}"]
    if err.get("code") is not None:
        parts.append(f"code={err.get('code')}")
    if err.get("status"):
        parts.append(f"status={err.get('status')}")
    return NodeResult(success=False, error=" | ".join(parts))
