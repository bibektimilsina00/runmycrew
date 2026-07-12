"""Google Drive action node — consolidated CRUD over the user's Drive
via OAuth.

One node, seven operations:
  - `upload_file`   / `create_folder`
  - `list_files`    / `get_file`
  - `share_file`    / `rename_file`
  - `delete_file`   (trashes; permanent delete needs `drive` scope)

Same shape as `GmailNode` and `GCalNode` — top-level `operation`
dropdown with per-op fields gated by `condition`.

All operations work inside the `drive.file` scope, which means RunMyCrew
can only touch files it created (or that the user explicitly opened
with RunMyCrew). Listing / reading other Drive content requires expanding
the OAuth scope to `drive.readonly`, which is a Google-reviewed
sensitive scope. Documented in the node description so users aren't
surprised when `list_files` returns an empty result for files they
created outside RunMyCrew.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel, field_validator

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.google.gdrive import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.nodes.google.gdrive.gdrive_trigger import _MIME_TYPE_OPTIONS

logger = get_logger(__name__)

GDRIVE_API = "https://www.googleapis.com/drive/v3"
GDRIVE_UPLOAD_API = "https://www.googleapis.com/upload/drive/v3"


# Google-native conversion targets for `upload_file → target_mime_type`.
# Drive lets us hand it a PDF / Word doc and convert into a Google Doc,
# etc — we surface the four supported conversions as a friendly dropdown
# plus "Keep original" so the user doesn't have to memorise MIME strings.
_CONVERSION_OPTIONS: list[dict[str, str]] = [
    {"label": "Keep original format", "value": ""},
    {"label": "Convert to Google Doc", "value": "application/vnd.google-apps.document"},
    {"label": "Convert to Google Sheet", "value": "application/vnd.google-apps.spreadsheet"},
    {"label": "Convert to Google Slides", "value": "application/vnd.google-apps.presentation"},
    {"label": "Convert to Google Drawing", "value": "application/vnd.google-apps.drawing"},
]


_ORDER_BY_OPTIONS: list[dict[str, str]] = [
    {"label": "Modified time (newest)", "value": "modifiedTime desc"},
    {"label": "Modified time (oldest)", "value": "modifiedTime"},
    {"label": "Created time (newest)", "value": "createdTime desc"},
    {"label": "Created time (oldest)", "value": "createdTime"},
    {"label": "Name (A → Z)", "value": "name"},
    {"label": "Name (Z → A)", "value": "name desc"},
    {"label": "File size (largest)", "value": "quotaBytesUsed desc"},
    {"label": "File size (smallest)", "value": "quotaBytesUsed"},
    {"label": "Recently viewed", "value": "viewedByMeTime desc"},
]

# File-resource fields we always pull back. Slim list so the action
# response stays template-friendly without hauling the full Drive
# metadata bag through downstream JSONata.
_FILE_FIELDS = "id,name,mimeType,trashed,createdTime,modifiedTime,webViewLink,iconLink,parents,size"


class GDriveProperties(BaseModel):
    credential: str | None = None
    operation: str = "upload_file"

    # common
    file_id: str | None = None
    name: str | None = None
    mime_type: str | None = None
    parent_folder_id: str | None = None

    @field_validator("parent_folder_id", mode="before")
    @classmethod
    def _coerce_folder_id(cls, value: Any) -> str | None:
        # Same coercion as `GDriveTriggerProperties` — accept either the
        # bare id string or the Picker-emitted `{id, name}` dict.
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) else None
        if value in (None, ""):
            return None
        return str(value)

    # upload — `content` holds the value the MediaRenderer emits:
    # either a plain URL string (legacy / typed) OR a dict
    # `{"type": "url"|"asset", ...}`. `resolve_media_field` collapses
    # both into a fetchable public URL so the handler can stream bytes
    # to Drive uniformly.
    content: Any = None
    target_mime_type: str | None = None  # for Google-doc conversions

    # share
    share_email: str | None = None
    share_role: str = "reader"  # reader / commenter / writer
    share_type: str = "user"  # user / group / domain / anyone
    send_notification_email: bool = False

    # list
    query: str | None = None
    max_results: int = 25
    order_by: str = "modifiedTime desc"


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GDriveNode(BaseNode[GDriveProperties]):
    @classmethod
    def get_properties_model(cls):
        return GDriveProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gdrive",
            name=NAME,
            category="integration",
            description=(
                "Upload, list, share, rename, and trash Google Drive files via "
                "OAuth. Operates within the `drive.file` scope — only files RunMyCrew "
                "created or the user explicitly opened with RunMyCrew are visible."
            ),
            icon=ICON_SLUG,
            color=COLOR,
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
                    "default": "upload_file",
                    "options": [
                        {"label": "Upload File", "value": "upload_file"},
                        {"label": "Create Folder", "value": "create_folder"},
                        {"label": "List Files", "value": "list_files"},
                        {"label": "Get File", "value": "get_file"},
                        {"label": "Share File", "value": "share_file"},
                        {"label": "Rename File", "value": "rename_file"},
                        {"label": "Delete (Trash) File", "value": "delete_file"},
                    ],
                },
                # ── upload ──────────────────────────────────────────
                {
                    "name": "name",
                    "label": "File name",
                    "type": "string",
                    "required": True,
                    "placeholder": "report.pdf",
                    "condition": _cond_any("upload_file", "create_folder"),
                },
                {
                    "name": "parent_folder_id",
                    "label": "Parent folder",
                    "type": "string",
                    "remote": {
                        "provider": "google",
                        "resource": "drive_folders",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                    "condition": _cond_any("upload_file", "create_folder"),
                },
                {
                    "name": "content",
                    "label": "File",
                    "type": "media",
                    "required": True,
                    "typeOptions": {"accept": "*/*", "nameField": "name"},
                    "condition": _cond("upload_file"),
                },
                {
                    "name": "mime_type",
                    "label": "File type",
                    "type": "options",
                    "default": "application/octet-stream",
                    "searchable": True,
                    "allowCustom": True,
                    "typeOptions": {"searchable": True, "allowCustom": True},
                    "options": _MIME_TYPE_OPTIONS,
                    "description": "Auto-detected if blank.",
                    "condition": _cond("upload_file"),
                    "mode": "advanced",
                },
                {
                    "name": "target_mime_type",
                    "label": "Convert to",
                    "type": "options",
                    "default": "",
                    "options": _CONVERSION_OPTIONS,
                    "condition": _cond("upload_file"),
                    "mode": "advanced",
                },
                # ── id-driven ops ───────────────────────────────────
                {
                    "name": "file_id",
                    "label": "File ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $step.id }}",
                    "condition": _cond_any("get_file", "share_file", "rename_file", "delete_file"),
                },
                # ── share ───────────────────────────────────────────
                {
                    "name": "share_email",
                    "label": "Email",
                    "type": "string",
                    "required": True,
                    "placeholder": "person@example.com",
                    "condition": _cond("share_file"),
                },
                {
                    "name": "share_role",
                    "label": "Role",
                    "type": "options",
                    "default": "reader",
                    "options": [
                        {"label": "Reader", "value": "reader"},
                        {"label": "Commenter", "value": "commenter"},
                        {"label": "Writer", "value": "writer"},
                    ],
                    "condition": _cond("share_file"),
                },
                {
                    "name": "share_type",
                    "label": "Share type",
                    "type": "options",
                    "default": "user",
                    "options": [
                        {"label": "User", "value": "user"},
                        {"label": "Group", "value": "group"},
                        {"label": "Domain", "value": "domain"},
                        {"label": "Anyone (link share)", "value": "anyone"},
                    ],
                    "condition": _cond("share_file"),
                    "mode": "advanced",
                },
                {
                    "name": "send_notification_email",
                    "label": "Send notification email",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("share_file"),
                    "mode": "advanced",
                },
                # ── rename ──────────────────────────────────────────
                {
                    "name": "name",
                    "label": "New name",
                    "type": "string",
                    "required": True,
                    "placeholder": "renamed.pdf",
                    "condition": _cond("rename_file"),
                },
                # ── list ────────────────────────────────────────────
                {
                    "name": "query",
                    "label": "Search query",
                    "type": "string",
                    "placeholder": "name contains 'report' and mimeType='application/pdf'",
                    "description": (
                        "Drive search-query syntax. Examples: "
                        "`name contains 'foo'`, "
                        "`mimeType='application/pdf'`, "
                        "`'<folder_id>' in parents`."
                    ),
                    "condition": _cond("list_files"),
                },
                {
                    "name": "max_results",
                    "label": "Max results",
                    "type": "number",
                    "default": 25,
                    "condition": _cond("list_files"),
                },
                {
                    "name": "order_by",
                    "label": "Order by",
                    "type": "options",
                    "default": "modifiedTime desc",
                    "options": _ORDER_BY_OPTIONS,
                    "condition": _cond("list_files"),
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
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

        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        try:
            async with httpx.AsyncClient(timeout=60) as client:
                headers = {"Authorization": f"Bearer {token}"}
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Drive API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GDriveNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── operation handlers ──────────────────────────────────────────────────


async def _upload_file(
    node: GDriveNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.name:
        return NodeResult(success=False, error="`name` is required.")
    if not node.props.content:
        return NodeResult(success=False, error="`content` is required.")

    # The `media` field renderer hands back either a plain URL string
    # (legacy / typed-in) or `{"type": "url"|"asset", ...}`.
    # `resolve_media_field` collapses both into a fetchable URL — for
    # `asset` it mints a short-lived HMAC-signed link so we can pull
    # the bytes from the Library through the same code path that
    # handles URLs.
    from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

    source_url = resolve_media_field(node.props.content)
    if not source_url:
        return NodeResult(
            success=False,
            error="`content` could not be resolved to a fetchable URL.",
        )

    inferred_mime = node.props.mime_type or "application/octet-stream"
    async with httpx.AsyncClient(timeout=60) as fetch:
        f_resp = await fetch.get(source_url)
        f_resp.raise_for_status()
        raw_bytes = f_resp.content
        ct = f_resp.headers.get("content-type")
        if ct and not node.props.mime_type:
            inferred_mime = ct.split(";")[0].strip()

    metadata: dict[str, Any] = {"name": node.props.name}
    if node.props.parent_folder_id:
        metadata["parents"] = [node.props.parent_folder_id.strip()]
    if node.props.target_mime_type:
        metadata["mimeType"] = node.props.target_mime_type.strip()

    # Drive's multipart upload protocol — JSON metadata part + binary
    # data part inside one POST. We hand-write the boundary so the
    # metadata part lands as `application/json` (httpx's `files=` would
    # use `multipart/form-data` instead, which Drive rejects).
    import json as _json

    boundary = "runmycrew-drive-upload-boundary"
    body_bytes = (
        (
            f"--{boundary}\r\n"
            f"Content-Type: application/json; charset=UTF-8\r\n\r\n"
            f"{_json.dumps(metadata)}\r\n"
            f"--{boundary}\r\n"
            f"Content-Type: {inferred_mime}\r\n\r\n"
        ).encode()
        + raw_bytes
        + f"\r\n--{boundary}--".encode()
    )

    upload_headers = {
        **headers,
        "Content-Type": f"multipart/related; boundary={boundary}",
    }
    resp = await client.post(
        f"{GDRIVE_UPLOAD_API}/files",
        headers=upload_headers,
        params={"uploadType": "multipart", "fields": _FILE_FIELDS},
        content=body_bytes,
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


async def _create_folder(
    node: GDriveNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.name:
        return NodeResult(success=False, error="`name` is required.")
    body: dict[str, Any] = {
        "name": node.props.name,
        "mimeType": "application/vnd.google-apps.folder",
    }
    if node.props.parent_folder_id:
        body["parents"] = [node.props.parent_folder_id.strip()]
    resp = await client.post(
        f"{GDRIVE_API}/files",
        headers=headers,
        params={"fields": _FILE_FIELDS},
        json=body,
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


async def _get_file(
    node: GDriveNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.file_id:
        return NodeResult(success=False, error="`file_id` is required.")
    resp = await client.get(
        f"{GDRIVE_API}/files/{node.props.file_id.strip()}",
        headers=headers,
        params={"fields": _FILE_FIELDS},
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


async def _list_files(
    node: GDriveNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    params: dict[str, Any] = {
        "pageSize": max(1, min(int(node.props.max_results or 25), 1000)),
        "fields": f"nextPageToken,files({_FILE_FIELDS})",
        "orderBy": node.props.order_by or "modifiedTime desc",
    }
    if node.props.query:
        params["q"] = node.props.query.strip()
    resp = await client.get(f"{GDRIVE_API}/files", headers=headers, params=params)
    resp.raise_for_status()
    body = resp.json()
    files = body.get("files") or []
    return NodeResult(
        success=True,
        output_data={"files": files, "count": len(files)},
    )


async def _share_file(
    node: GDriveNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.file_id:
        return NodeResult(success=False, error="`file_id` is required.")
    share_type = (node.props.share_type or "user").lower()
    body: dict[str, Any] = {
        "role": (node.props.share_role or "reader").lower(),
        "type": share_type,
    }
    if share_type in ("user", "group"):
        if not node.props.share_email:
            return NodeResult(
                success=False, error="`share_email` is required for user / group shares."
            )
        body["emailAddress"] = node.props.share_email.strip()
    params: dict[str, Any] = {
        "sendNotificationEmail": "true" if node.props.send_notification_email else "false",
    }
    resp = await client.post(
        f"{GDRIVE_API}/files/{node.props.file_id.strip()}/permissions",
        headers=headers,
        params=params,
        json=body,
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


async def _rename_file(
    node: GDriveNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.file_id:
        return NodeResult(success=False, error="`file_id` is required.")
    if not node.props.name:
        return NodeResult(success=False, error="`name` (new name) is required.")
    resp = await client.patch(
        f"{GDRIVE_API}/files/{node.props.file_id.strip()}",
        headers=headers,
        params={"fields": _FILE_FIELDS},
        json={"name": node.props.name},
    )
    resp.raise_for_status()
    return NodeResult(success=True, output_data=resp.json())


async def _delete_file(
    node: GDriveNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.file_id:
        return NodeResult(success=False, error="`file_id` is required.")
    # `drive.file` scope can't issue a permanent DELETE — we trash via
    # PATCH instead so the operation works under the OAuth grant RunMyCrew
    # currently asks for.
    resp = await client.patch(
        f"{GDRIVE_API}/files/{node.props.file_id.strip()}",
        headers=headers,
        params={"fields": _FILE_FIELDS},
        json={"trashed": True},
    )
    resp.raise_for_status()
    return NodeResult(
        success=True,
        output_data={"trashed": True, "file_id": node.props.file_id, "file": resp.json()},
    )


_HANDLERS = {
    "upload_file": _upload_file,
    "create_folder": _create_folder,
    "get_file": _get_file,
    "list_files": _list_files,
    "share_file": _share_file,
    "rename_file": _rename_file,
    "delete_file": _delete_file,
}
