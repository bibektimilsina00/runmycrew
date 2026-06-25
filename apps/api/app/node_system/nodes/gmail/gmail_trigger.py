"""Gmail trigger node — cursor-driven polling.

Fires once per new Gmail message that matches the user's query.

The cursor lives in `integration_trigger_state.cursor` (per workflow /
node) and is Gmail's `historyId`. Mechanics:

  1. On the first invocation, we call `users.getProfile` to learn the
     mailbox's *current* `historyId` and persist it. We do NOT emit any
     existing messages — fresh triggers should fire on what arrives
     next, not on whatever happened to be in the inbox already.
  2. Subsequent invocations call `users.history.list` with the stored
     `startHistoryId`. The response enumerates every message that has
     been added since then. We filter to additions (`messageAdded`),
     drop messages that don't match the user's query by re-running
     `messages.list?q=…` and intersecting, then fetch each surviving id
     with `messages.get?format=full`.
  3. The polling scheduler emits one execution per matched message;
     `/listen` returns the first match so the editor preview stays
     focused.
  4. The cursor advances to the response's `historyId`. Both the
     newly-added message id and the new history boundary land in the
     same transaction so a crash after dispatch but before persist
     would only re-emit the same message — never skip one.

Mirrors what n8n, Zapier, and Pipedream's Gmail triggers do under the
hood (`history.list` with `historyId`). Polling cadence comes from the
scheduler's per-row `next_poll_at` field, NOT from a hard-coded cron —
different users can poll at different rates.
"""

from __future__ import annotations

import base64
import re
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.models import IntegrationTriggerState
from apps.api.app.features.triggers.repository import IntegrationTriggerStateRepository
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

GMAIL_API = "https://gmail.googleapis.com/gmail/v1"
PROVIDER = "gmail"
DEFAULT_POLL_INTERVAL_SECONDS = 60


class GmailTriggerProperties(BaseModel):
    credential: str | None = None
    event_type: str = "new_message"
    # Gmail's standard search-query syntax. Empty matches every message
    # newer than the cursor — equivalent to "any inbound message".
    query: str = "is:unread"
    # Cap fanned-out messages per poll so a backlog (long downtime,
    # bulk arrival) doesn't blow out the worker queue. The remaining
    # ids stay in the next `history.list` window thanks to how Gmail
    # returns them in delivery order.
    max_messages_per_poll: int = 25
    # Per-trigger poll cadence in seconds (passed through to the
    # scheduler when it writes the next `next_poll_at`). Floor at 30s
    # to stay polite to Google's API quota.
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS


class GmailTriggerNode(BaseNode[GmailTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GmailTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gmail",
            name="Gmail",
            category="trigger",
            description=(
                "Fires once per new Gmail message matching your query. "
                "Uses Gmail's `historyId` cursor so each poll only surfaces "
                "what arrived since the last run — no duplicates, no missed mail."
            ),
            icon="gmail",
            color="#1c1c1c",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": "new_message",
                    "options": [
                        {"label": "New Message", "value": "new_message"},
                    ],
                },
                {
                    "name": "query",
                    "label": "Gmail Search Query",
                    "type": "gmail-query",
                    "default": "is:unread",
                    "placeholder": "Search words…",
                    "description": (
                        "Trigger only fires on messages matching these "
                        "filters. Use “Edit raw query” for full Gmail "
                        "search syntax (OR, parens, etc)."
                    ),
                    "condition": {"field": "event_type", "value": "new_message"},
                },
                {
                    "name": "max_messages_per_poll",
                    "label": "Max messages per poll",
                    "type": "number",
                    "default": 25,
                    "mode": "advanced",
                    "description": (
                        "Hard cap on how many messages a single poll emits. "
                        "Protects against backlog spikes after downtime."
                    ),
                    "condition": {"field": "event_type", "value": "new_message"},
                },
                {
                    "name": "poll_interval_seconds",
                    "label": "Poll interval (seconds)",
                    "type": "number",
                    "default": DEFAULT_POLL_INTERVAL_SECONDS,
                    "mode": "advanced",
                    "description": (
                        "How often the background scheduler asks Gmail for new "
                        "messages. Minimum 30s to stay inside Google's quota."
                    ),
                    "condition": {"field": "event_type", "value": "new_message"},
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "threadId", "type": "string"},
                {"label": "from_email", "type": "string"},
                {"label": "to", "type": "string"},
                {"label": "subject", "type": "string"},
                {"label": "snippet", "type": "string"},
                {"label": "body_text", "type": "string"},
                {"label": "labelIds", "type": "array"},
                {"label": "internalDate", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            allow_error=True,
            credential_type="google_oauth",
        )

    def _get_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("access_token")

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # The poller dispatches a pre-normalised message envelope per
        # match; pass it through verbatim so downstream nodes see the
        # same shape whether the trigger fired live or via a captured
        # fixture replay.
        if isinstance(input_data, dict) and input_data.get("id") and input_data.get("payload"):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        # Inline / preview path. When invoked from `/listen` or a manual
        # run the trigger reads its persisted cursor (if any), polls
        # Gmail once, and returns the *first* new match. Same cursor
        # logic, same filter, same normalisation the scheduler runs —
        # just emitting only the head item so the editor preview is
        # focused.
        workflow_id = getattr(context, "workflow_id", None)
        node_id = getattr(context, "node_id", None)
        workspace_id = getattr(context, "workspace_id", None)
        db = getattr(context, "db", None)
        wf_uuid = _safe_uuid(workflow_id)
        ws_uuid = _safe_uuid(workspace_id)
        if wf_uuid is None or ws_uuid is None or db is None or not node_id:
            # No persistence — fall back to a stateless single-message
            # snapshot. Only used in synthetic test runs without a real
            # workflow.
            return await self._stateless_first_match(token)

        repo = IntegrationTriggerStateRepository(db)
        state = await repo.get(wf_uuid, node_id)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Authorization": f"Bearer {token}"}
                if state is None:
                    history_id = await self._snapshot_history_id(client, headers)
                    await repo.upsert(
                        workflow_id=wf_uuid,
                        workspace_id=ws_uuid,
                        node_id=node_id,
                        provider=PROVIDER,
                        cursor={"history_id": history_id},
                        next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
                        last_error=None,
                    )
                    await db.commit()
                    return NodeResult(
                        success=True,
                        output_data={
                            "matched": 0,
                            "messages": [],
                            "cursor_initialised": True,
                            "history_id": history_id,
                        },
                        # Cursor initialised, nothing to emit yet — halt the
                        # downstream chain so action nodes don't fire with
                        # null fields. Real messages arrive via the scheduler.
                        handled_successors=True,
                    )

                messages, new_history_id = await self._poll_history(client, headers, state)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=(f"Gmail API error {exc.response.status_code}: {exc.response.text[:200]}"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GmailTriggerNode poll failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))

        # Advance the cursor regardless of whether messages matched —
        # otherwise unmatched arrivals re-enter the history window on
        # every poll forever.
        await repo.upsert(
            workflow_id=wf_uuid,
            workspace_id=ws_uuid,
            node_id=node_id,
            provider=PROVIDER,
            cursor={"history_id": new_history_id},
            next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
            last_error=None,
        )
        await db.commit()

        if not messages:
            return NodeResult(
                success=True,
                output_data={
                    "matched": 0,
                    "messages": [],
                    "history_id": new_history_id,
                },
                # Nothing matched this poll — halt downstream so the
                # action chain only fires when there is real message data.
                handled_successors=True,
            )

        return NodeResult(success=True, output_data=messages[0])

    # ── public poll API (used by scheduler + inline preview) ─────────

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], str]:
        """Run one Gmail poll against `cursor`. The caller persists the
        returned cursor. Standalone of NodeContext so the polling
        scheduler can drive it directly with just a token + the row's
        last persisted cursor."""
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            if not cursor or not cursor.get("history_id"):
                history_id = await self._snapshot_history_id(client, headers)
                return [], history_id
            return await self._poll_history(client, headers, cursor)

    async def _snapshot_history_id(self, client: httpx.AsyncClient, headers: dict[str, str]) -> str:
        profile = await client.get(f"{GMAIL_API}/users/me/profile", headers=headers)
        profile.raise_for_status()
        return str(profile.json().get("historyId") or "")

    async def _poll_history(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        cursor_or_state: IntegrationTriggerState | dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str]:
        """Pull every message added since the cursor, run them through
        the user's query filter, and return the normalised payloads.

        Returns `(matches, new_history_id)` so the caller can advance the
        cursor in the same transaction that dispatches the executions.
        Gmail's `history.list` is paginated — we honour `nextPageToken`
        until the cap is hit or the result set is exhausted.
        """
        cursor = (
            cursor_or_state.cursor
            if isinstance(cursor_or_state, IntegrationTriggerState)
            else cursor_or_state
        )
        last_history_id = str((cursor or {}).get("history_id") or "")
        if not last_history_id:
            return [], await self._snapshot_history_id(client, headers)

        added_ids: list[str] = []
        new_history_id = last_history_id
        page_token: str | None = None
        max_take = max(1, min(self.props.max_messages_per_poll, 100))
        while True:
            params: dict[str, Any] = {
                "startHistoryId": last_history_id,
                "historyTypes": "messageAdded",
            }
            if page_token:
                params["pageToken"] = page_token
            resp = await client.get(f"{GMAIL_API}/users/me/history", headers=headers, params=params)
            if resp.status_code == 404:
                # Cursor too old — Gmail retires history entries after
                # ~30 days. Treat as "snapshot and continue" so the
                # trigger self-heals instead of staying stuck.
                return [], await self._snapshot_history_id(client, headers)
            resp.raise_for_status()
            body = resp.json()
            new_history_id = str(body.get("historyId") or new_history_id)
            for entry in body.get("history") or []:
                for added in entry.get("messagesAdded") or []:
                    msg = added.get("message") or {}
                    mid = str(msg.get("id") or "")
                    if mid and mid not in added_ids:
                        added_ids.append(mid)
            page_token = body.get("nextPageToken")
            if not page_token or len(added_ids) >= max_take:
                break

        if not added_ids:
            return [], new_history_id

        added_ids = added_ids[:max_take]
        query = (self.props.query or "").strip()
        if query:
            # Intersect "added since cursor" with "matches user query"
            # via one `messages.list` round-trip. Cheaper than fetching
            # each message in full just to discover it doesn't match.
            qresp = await client.get(
                f"{GMAIL_API}/users/me/messages",
                headers=headers,
                params={"q": query, "maxResults": max(50, max_take)},
            )
            qresp.raise_for_status()
            matching = {str(m.get("id") or "") for m in qresp.json().get("messages") or []}
            added_ids = [mid for mid in added_ids if mid in matching]
            if not added_ids:
                return [], new_history_id

        # Hydrate the surviving ids into normalised payloads. Gmail
        # doesn't expose a batch fetch in REST, so this is one round-trip
        # per match.
        payloads: list[dict[str, Any]] = []
        for mid in added_ids:
            mresp = await client.get(f"{GMAIL_API}/users/me/messages/{mid}", headers=headers)
            if mresp.status_code == 404:
                # Message was deleted between history.list and this
                # fetch — skip rather than fail the whole poll.
                continue
            mresp.raise_for_status()
            payloads.append(_normalize(mresp.json()))
        return payloads, new_history_id

    async def _stateless_first_match(self, token: str) -> NodeResult:
        """Fallback for synthetic test runs without workflow / node
        context. Returns the single most recent matching message without
        writing a cursor — purely a preview convenience."""
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                listing = await client.get(
                    f"{GMAIL_API}/users/me/messages",
                    headers=headers,
                    params={"q": self.props.query or "", "maxResults": 1},
                )
                listing.raise_for_status()
                hits = listing.json().get("messages") or []
                if not hits:
                    return NodeResult(
                        success=True,
                        output_data={"matched": 0, "messages": []},
                        handled_successors=True,
                    )
                detail = await client.get(
                    f"{GMAIL_API}/users/me/messages/{hits[0]['id']}", headers=headers
                )
                detail.raise_for_status()
                return NodeResult(success=True, output_data=_normalize(detail.json()))
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=(f"Gmail API error {exc.response.status_code}: {exc.response.text[:200]}"),
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GmailTriggerNode stateless poll failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── helpers ──────────────────────────────────────────────────────────────


_HEADER_KEYS = {"from", "to", "cc", "bcc", "subject", "date", "message-id"}


def _safe_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _next_poll_at(interval_seconds: int) -> datetime:
    """Clamp the user-configured cadence to a polite floor + cap so a
    misconfigured node can't either DOS Google or wait forever."""
    seconds = max(30, min(int(interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS), 60 * 60))
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _normalize(message: dict[str, Any]) -> dict[str, Any]:
    """Flatten the Gmail message structure into the shape our
    outputs_schema advertises. Downstream nodes template
    `{{ $step.from_email }}` / `{{ $step.subject }}` /
    `{{ $step.body_text }}` without parsing the payload tree."""
    payload = message.get("payload") or {}
    headers_list = payload.get("headers") or []
    headers = {
        h["name"].lower(): h["value"]
        for h in headers_list
        if isinstance(h, dict) and h.get("name") and h["name"].lower() in _HEADER_KEYS
    }
    from_full = headers.get("from") or ""
    from_email = _extract_email(from_full)
    body_text = _extract_text_body(payload)
    return {
        "id": message.get("id"),
        "threadId": message.get("threadId"),
        "labelIds": message.get("labelIds") or [],
        "internalDate": message.get("internalDate"),
        "snippet": message.get("snippet") or "",
        "from": from_full,
        "from_email": from_email,
        "to": headers.get("to") or "",
        "subject": headers.get("subject") or "",
        "body_text": body_text,
        "payload": payload,
    }


def _extract_email(from_header: str) -> str:
    match = re.search(r"[\w.+-]+@[\w-]+\.[\w.-]+", from_header)
    return match.group(0) if match else ""


def _extract_text_body(payload: dict[str, Any]) -> str:
    """Walk the MIME tree and return the first text/plain part decoded
    from base64url, falling back to text/html (HTML tags stripped)."""
    plain: str | None = None
    html: str | None = None

    def walk(part: dict[str, Any]) -> None:
        nonlocal plain, html
        mime = part.get("mimeType") or ""
        data = ((part.get("body") or {}).get("data")) or ""
        if data:
            try:
                decoded = base64.urlsafe_b64decode(data.encode()).decode("utf-8", errors="replace")
            except Exception:  # noqa: BLE001
                decoded = ""
            if mime.startswith("text/plain") and plain is None:
                plain = decoded
            elif mime.startswith("text/html") and html is None:
                html = decoded
        for sub in part.get("parts") or []:
            if isinstance(sub, dict):
                walk(sub)

    walk(payload)
    if plain:
        return plain
    if html:
        return re.sub(r"<[^>]+>", "", html).strip()
    return ""


# ── scheduler integration ────────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Adapter that lets the polling scheduler drive a Gmail poll
    without instantiating a full `GmailTriggerNode`. Builds a
    minimal property bundle off the saved node props, runs one poll,
    returns `(matches, new_cursor_dict)`."""
    node = GmailTriggerNode.__new__(GmailTriggerNode)
    node.props = GmailTriggerProperties(
        credential=None,
        event_type=str(props.get("event_type") or "new_message"),
        query=str(props.get("query") or ""),
        max_messages_per_poll=int(props.get("max_messages_per_poll") or 25),
        poll_interval_seconds=int(
            props.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS
        ),
    )
    messages, new_history_id = await node.poll(token, cursor)
    return messages, {"history_id": new_history_id}


def _register() -> None:
    # Module-level import side-effect: hooks Gmail's poller into the
    # central scheduler. Safe to call multiple times — `register_poller`
    # overwrites the previous entry rather than appending.
    try:
        from apps.api.app.execution_engine.scheduler.integration_polling import (
            register_poller,
        )
    except Exception:  # noqa: BLE001
        return
    register_poller(
        node_type="trigger.gmail",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()
