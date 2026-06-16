"""Google Drive trigger node — pageToken-driven polling.

Fires once per added / modified / trashed file in the user's Drive
that matches the node's filters.

The OAuth credential is currently scoped to `drive.file`, so the
visible delta is restricted to files Fuse itself created (uploads
done via the Drive action node, or downstream effects on those
files). Expanding to the full Drive surface needs `drive.readonly`
and a Google verification pass — out of scope here.

Cursor mechanics mirror Gmail / Calendar:

  1. First poll calls `changes/startPageToken` to learn the current
     boundary, persists it, emits nothing — fresh triggers fire on
     what arrives next, not the backlog.
  2. Subsequent polls hit `changes/list?pageToken=<token>&includeRemoved=true`
     and walk every `change`. Each is classified (added / modified /
     trashed) by combining `removed` with file timestamps + trashed
     state, filtered by user-set `mime_type` / `parent_folder_id` /
     `name_contains`, normalised, and dispatched.
  3. The response always returns a `newStartPageToken` — that becomes
     the next cursor in the same transaction that dispatches the
     matches, so a crash between dispatch and persist re-emits the
     same change at worst, never skips.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.features.triggers.models import IntegrationTriggerState
from apps.api.app.features.triggers.repository import IntegrationTriggerStateRepository
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

GDRIVE_API = "https://www.googleapis.com/drive/v3"
PROVIDER = "gdrive"
DEFAULT_POLL_INTERVAL_SECONDS = 60

EVENT_FILTERS = ("any", "added", "modified", "trashed")

# Common Drive MIME types — surfaced in the trigger + action UIs as a
# searchable dropdown with allowCustom so power users can paste a
# bespoke MIME string when the preset list doesn't cover it.
_MIME_TYPE_OPTIONS: list[dict[str, str]] = [
    {"label": "Any file type", "value": ""},
    {"label": "Folder", "value": "application/vnd.google-apps.folder"},
    {"label": "Google Doc", "value": "application/vnd.google-apps.document"},
    {"label": "Google Sheet", "value": "application/vnd.google-apps.spreadsheet"},
    {"label": "Google Slides", "value": "application/vnd.google-apps.presentation"},
    {"label": "Google Form", "value": "application/vnd.google-apps.form"},
    {"label": "Google Drawing", "value": "application/vnd.google-apps.drawing"},
    {"label": "PDF", "value": "application/pdf"},
    {"label": "Plain text", "value": "text/plain"},
    {"label": "CSV", "value": "text/csv"},
    {"label": "JSON", "value": "application/json"},
    {"label": "ZIP", "value": "application/zip"},
    {"label": "JPEG image", "value": "image/jpeg"},
    {"label": "PNG image", "value": "image/png"},
    {"label": "GIF image", "value": "image/gif"},
    {"label": "MP4 video", "value": "video/mp4"},
    {"label": "MP3 audio", "value": "audio/mpeg"},
    {
        "label": "Word (.docx)",
        "value": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    },
    {
        "label": "Excel (.xlsx)",
        "value": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    },
    {
        "label": "PowerPoint (.pptx)",
        "value": "application/vnd.openxmlformats-officedocument.presentationml.presentation",
    },
]

# Fields we request on every change. Slim list so we don't pay the
# round-trip cost of fetching a full file resource per change just to
# discard most of it.
_CHANGE_FIELDS = (
    "nextPageToken,newStartPageToken,changes("
    "fileId,time,removed,changeType,"
    "file(id,name,mimeType,trashed,createdTime,modifiedTime,"
    "webViewLink,iconLink,parents,owners(emailAddress),size)"
    ")"
)


class GDriveTriggerProperties(BaseModel):
    credential: str | None = None
    event_filter: str = "any"
    # Drive returns the full MIME type ("application/pdf",
    # "application/vnd.google-apps.document"). Empty matches anything.
    mime_type: str = ""
    # Limit to one folder. The Picker field emits `{id, name}` so the
    # editor can show the folder's name back to the user, but the
    # runtime only cares about the id — the validator coerces both
    # shapes into the id string.
    parent_folder_id: str = ""
    # Case-insensitive substring filter on file.name.
    name_contains: str = ""
    max_changes_per_poll: int = 25
    poll_interval_seconds: int = DEFAULT_POLL_INTERVAL_SECONDS

    @field_validator("parent_folder_id", mode="before")
    @classmethod
    def _coerce_folder_id(cls, value: Any) -> str:
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) else ""
        return str(value) if value is not None else ""


class GDriveTriggerNode(BaseNode[GDriveTriggerProperties]):
    @classmethod
    def get_properties_model(cls):
        return GDriveTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.gdrive_change",
            name="Google Drive",
            category="trigger",
            description=(
                "Fires once per added / modified / trashed file matching your "
                "filters. Uses Drive's `pageToken` cursor — each poll only "
                "surfaces what changed since the last run. Visibility is "
                "restricted to files Fuse can see (drive.file scope)."
            ),
            icon="si:SiGoogledrive",
            color="#4285f4",
            properties=[
                {
                    "name": "credential",
                    "label": "Google Account",
                    "type": "credential",
                    "credentialType": "google_oauth",
                    "required": True,
                },
                {
                    "name": "event_filter",
                    "label": "Event type",
                    "type": "options",
                    "default": "any",
                    "options": [
                        {"label": "Any change", "value": "any"},
                        {"label": "File added", "value": "added"},
                        {"label": "File modified", "value": "modified"},
                        {"label": "File trashed", "value": "trashed"},
                    ],
                },
                {
                    "name": "mime_type",
                    "label": "File type",
                    "type": "options",
                    "default": "",
                    "searchable": True,
                    "allowCustom": True,
                    "typeOptions": {"searchable": True, "allowCustom": True},
                    "options": _MIME_TYPE_OPTIONS,
                    "description": (
                        "Optional file-type filter. Pick a common type from "
                        "the dropdown or type a custom MIME string."
                    ),
                },
                {
                    "name": "parent_folder_id",
                    "label": "Folder to watch",
                    "type": "gdrive-folder",
                    "default": "",
                    "description": (
                        "Pick a Drive folder via Google's Picker. Drive's "
                        "`drive.file` scope only surfaces files Fuse created "
                        "OR files inside a folder the user explicitly picked "
                        "here — that's how Fuse stays inside the non-sensitive "
                        "scope that doesn't need Google's security review. "
                        "Leave blank to fall back to whatever Fuse created."
                    ),
                },
                {
                    "name": "name_contains",
                    "label": "Name contains",
                    "type": "string",
                    "default": "",
                    "placeholder": "report",
                    "description": "Case-insensitive substring match on filename.",
                },
                {
                    "name": "max_changes_per_poll",
                    "label": "Max changes per poll",
                    "type": "number",
                    "default": 25,
                    "mode": "advanced",
                    "description": (
                        "Hard cap on how many changes a single poll emits. "
                        "Protects against backlog spikes after downtime."
                    ),
                },
                {
                    "name": "poll_interval_seconds",
                    "label": "Poll interval (seconds)",
                    "type": "number",
                    "default": DEFAULT_POLL_INTERVAL_SECONDS,
                    "mode": "advanced",
                    "description": (
                        "How often the background scheduler asks Drive for "
                        "changes. Minimum 30s to stay inside Google's quota."
                    ),
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "name", "type": "string"},
                {"label": "mime_type", "type": "string"},
                {"label": "web_view_link", "type": "string"},
                {"label": "icon_link", "type": "string"},
                {"label": "parent_ids", "type": "array"},
                {"label": "owner_email", "type": "string"},
                {"label": "size", "type": "string"},
                {"label": "modified_time", "type": "string"},
                {"label": "change_type", "type": "string"},
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
        if isinstance(input_data, dict) and input_data.get("id") and input_data.get("payload"):
            return NodeResult(success=True, output_data=input_data)

        token = self._get_token()
        if not token:
            return NodeResult(success=False, error="Google OAuth credential required.")

        workflow_id = getattr(context, "workflow_id", None)
        node_id = getattr(context, "node_id", None)
        workspace_id = getattr(context, "workspace_id", None)
        db = getattr(context, "db", None)
        wf_uuid = _safe_uuid(workflow_id)
        ws_uuid = _safe_uuid(workspace_id)
        if wf_uuid is None or ws_uuid is None or db is None or not node_id:
            return await self._stateless_first_match(token)

        repo = IntegrationTriggerStateRepository(db)
        state = await repo.get(wf_uuid, node_id)
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                headers = {"Authorization": f"Bearer {token}"}
                if state is None:
                    page_token = await self._snapshot_page_token(client, headers)
                    await repo.upsert(
                        workflow_id=wf_uuid,
                        workspace_id=ws_uuid,
                        node_id=node_id,
                        provider=PROVIDER,
                        cursor={"page_token": page_token},
                        next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
                        last_error=None,
                    )
                    await db.commit()
                    return NodeResult(
                        success=True,
                        output_data={
                            "matched": 0,
                            "changes": [],
                            "cursor_initialised": True,
                            "page_token": page_token,
                        },
                        handled_successors=True,
                    )
                changes, new_page_token = await self._poll_changes(client, headers, state)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Drive API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GDriveTriggerNode poll failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))

        await repo.upsert(
            workflow_id=wf_uuid,
            workspace_id=ws_uuid,
            node_id=node_id,
            provider=PROVIDER,
            cursor={"page_token": new_page_token},
            next_poll_at=_next_poll_at(self.props.poll_interval_seconds),
            last_error=None,
        )
        await db.commit()

        if not changes:
            return NodeResult(
                success=True,
                output_data={
                    "matched": 0,
                    "changes": [],
                    "page_token": new_page_token,
                },
                handled_successors=True,
            )
        return NodeResult(success=True, output_data=changes[0])

    # ── public poll API ──────────────────────────────────────────────

    async def poll(
        self, token: str, cursor: dict[str, Any] | None
    ) -> tuple[list[dict[str, Any]], str]:
        headers = {"Authorization": f"Bearer {token}"}
        async with httpx.AsyncClient(timeout=30) as client:
            if not cursor or not cursor.get("page_token"):
                page_token = await self._snapshot_page_token(client, headers)
                return [], page_token
            return await self._poll_changes(client, headers, cursor)

    async def _snapshot_page_token(self, client: httpx.AsyncClient, headers: dict[str, str]) -> str:
        resp = await client.get(f"{GDRIVE_API}/changes/startPageToken", headers=headers)
        resp.raise_for_status()
        return str(resp.json().get("startPageToken") or "")

    async def _poll_changes(
        self,
        client: httpx.AsyncClient,
        headers: dict[str, str],
        cursor_or_state: IntegrationTriggerState | dict[str, Any],
    ) -> tuple[list[dict[str, Any]], str]:
        """Pull every change since the cursor, filter, normalise.
        Returns `(matches, new_page_token)`."""
        cursor = (
            cursor_or_state.cursor
            if isinstance(cursor_or_state, IntegrationTriggerState)
            else cursor_or_state
        )
        page_token = str((cursor or {}).get("page_token") or "")
        if not page_token:
            return [], await self._snapshot_page_token(client, headers)

        event_filter = (self.props.event_filter or "any").lower()
        if event_filter not in EVENT_FILTERS:
            event_filter = "any"
        mime_type = (self.props.mime_type or "").strip()
        parent_id = _folder_id(self.props.parent_folder_id)
        name_substr = (self.props.name_contains or "").strip().lower()
        max_take = max(1, min(self.props.max_changes_per_poll, 100))

        matches: list[dict[str, Any]] = []
        new_page_token = page_token
        current_token: str | None = page_token

        while current_token:
            resp = await client.get(
                f"{GDRIVE_API}/changes",
                headers=headers,
                params={
                    "pageToken": current_token,
                    "includeRemoved": "true",
                    "pageSize": 100,
                    "fields": _CHANGE_FIELDS,
                },
            )
            resp.raise_for_status()
            body = resp.json()
            for change in body.get("changes") or []:
                if change.get("changeType") != "file":
                    continue
                file = change.get("file") or {}
                change_type = _classify_change(change, file)
                if event_filter != "any" and change_type != event_filter:
                    continue
                if mime_type and (file.get("mimeType") or "") != mime_type:
                    continue
                if parent_id and parent_id not in (file.get("parents") or []):
                    continue
                if name_substr and name_substr not in (file.get("name") or "").lower():
                    continue
                matches.append(_normalize(change, file, change_type))
                if len(matches) >= max_take:
                    break
            new_page_token = str(
                body.get("newStartPageToken") or body.get("nextPageToken") or new_page_token
            )
            current_token = body.get("nextPageToken")
            if len(matches) >= max_take:
                break
        return matches, new_page_token

    async def _stateless_first_match(self, token: str) -> NodeResult:
        """Preview path — return the most recently modified file the
        cred can see. Drive has no equivalent of Gmail's `messages.list`
        for "the latest one", so we do `files.list` with orderBy."""
        headers = {"Authorization": f"Bearer {token}"}
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                params: dict[str, Any] = {
                    "orderBy": "modifiedTime desc",
                    "pageSize": 1,
                    "fields": (
                        "files(id,name,mimeType,trashed,createdTime,"
                        "modifiedTime,webViewLink,iconLink,parents,"
                        "owners(emailAddress),size)"
                    ),
                }
                resp = await client.get(f"{GDRIVE_API}/files", headers=headers, params=params)
                resp.raise_for_status()
                files = resp.json().get("files") or []
                if not files:
                    return NodeResult(
                        success=True,
                        output_data={"matched": 0, "changes": []},
                        handled_successors=True,
                    )
                return NodeResult(
                    success=True,
                    output_data=_normalize({}, files[0], "modified"),
                )
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Drive API error {exc.response.status_code}: {exc.response.text[:200]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GDriveTriggerNode stateless poll failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── helpers ──────────────────────────────────────────────────────────────


def _folder_id(value: Any) -> str:
    """Drive folder fields accept either a bare id string (legacy) or a
    Picker-emitted `{id, name}` dict (current). Normalise to the id
    string so downstream code can stay shape-agnostic. Empty string
    means "no folder filter"."""
    if isinstance(value, dict):
        v = value.get("id")
        return str(v).strip() if isinstance(v, str) else ""
    if isinstance(value, str):
        return value.strip()
    return ""


def _safe_uuid(value: Any) -> UUID | None:
    if value is None:
        return None
    try:
        return UUID(str(value))
    except (ValueError, TypeError):
        return None


def _next_poll_at(interval_seconds: int) -> datetime:
    seconds = max(30, min(int(interval_seconds or DEFAULT_POLL_INTERVAL_SECONDS), 60 * 60))
    return datetime.now(UTC) + timedelta(seconds=seconds)


def _classify_change(change: dict[str, Any], file: dict[str, Any]) -> str:
    """Drive's `changes.list` doesn't tag adds vs modifies. Combine:
    - `removed: true` OR `file.trashed: true` → trashed
    - `createdTime == modifiedTime` (within 1s) → added
    - else → modified
    """
    if change.get("removed") or (file.get("trashed") is True):
        return "trashed"
    created = file.get("createdTime")
    modified = file.get("modifiedTime")
    if created and modified:
        try:
            c = datetime.fromisoformat(created.replace("Z", "+00:00"))
            m = datetime.fromisoformat(modified.replace("Z", "+00:00"))
            if abs((m - c).total_seconds()) <= 1:
                return "added"
        except ValueError:
            pass
    return "modified"


def _normalize(change: dict[str, Any], file: dict[str, Any], change_type: str) -> dict[str, Any]:
    """Flatten the Drive change into the shape outputs_schema advertises."""
    owners = file.get("owners") or []
    owner_email = ""
    if owners and isinstance(owners[0], dict):
        owner_email = owners[0].get("emailAddress") or ""
    return {
        "id": file.get("id") or change.get("fileId"),
        "name": file.get("name") or "",
        "mime_type": file.get("mimeType") or "",
        "web_view_link": file.get("webViewLink") or "",
        "icon_link": file.get("iconLink") or "",
        "parent_ids": file.get("parents") or [],
        "owner_email": owner_email,
        "size": file.get("size") or "",
        "modified_time": file.get("modifiedTime") or change.get("time") or "",
        "change_type": change_type,
        "payload": {"change": change, "file": file},
    }


# ── scheduler integration ────────────────────────────────────────────────


async def _poll_for_scheduler(
    token: str,
    cursor: dict[str, Any] | None,
    props: dict[str, Any],
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    node = GDriveTriggerNode.__new__(GDriveTriggerNode)
    node.props = GDriveTriggerProperties(
        credential=None,
        event_filter=str(props.get("event_filter") or "any"),
        mime_type=str(props.get("mime_type") or ""),
        parent_folder_id=_folder_id(props.get("parent_folder_id")),
        name_contains=str(props.get("name_contains") or ""),
        max_changes_per_poll=int(props.get("max_changes_per_poll") or 25),
        poll_interval_seconds=int(
            props.get("poll_interval_seconds") or DEFAULT_POLL_INTERVAL_SECONDS
        ),
    )
    changes, new_page_token = await node.poll(token, cursor)
    return changes, {"page_token": new_page_token}


def _register() -> None:
    try:
        from apps.api.app.execution_engine.scheduler.integration_polling import (
            register_poller,
        )
    except Exception:  # noqa: BLE001
        return
    register_poller(
        node_type="trigger.gdrive_change",
        provider=PROVIDER,
        poller=_poll_for_scheduler,
    )


_register()
