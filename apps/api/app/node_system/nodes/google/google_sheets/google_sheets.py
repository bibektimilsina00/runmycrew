"""Google Sheets action node — full CRUD over a user's spreadsheets via
OAuth. One node, twelve operations.

Read & write
  - `get_spreadsheet`  / `get_values`
  - `update_values`    / `append_values`
  - `clear_values`

Create
  - `create_spreadsheet` (title + initial sheets[])
  - `create_sheet`       (add a tab to an existing spreadsheet)
  - `duplicate_sheet`    (copy a tab in-place)

Modify
  - `find_replace`       (string search + replace, optionally scoped to one sheet)
  - `batch_update`       (raw `requests[]` for power users)

Delete
  - `delete_sheet`       (remove a tab from a spreadsheet)
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
from apps.api.app.node_system.nodes.google.google_sheets import COLOR, ICON_SLUG, NAME

logger = get_logger(__name__)
SHEETS_API = "https://sheets.googleapis.com/v4/spreadsheets"


class GoogleSheetsProperties(BaseModel):
    credential: str | None = None
    operation: str = "get_values"

    spreadsheet_id: str | None = None
    range_name: str | None = None

    # update / append
    value_input_option: str = "USER_ENTERED"
    values: Any = None  # list[list[Any]] when literal; Any allows templates

    # create_spreadsheet
    title: str | None = None
    initial_sheets: Any = None  # list[str] of sheet titles for the new spreadsheet

    # create_sheet / duplicate_sheet / delete_sheet
    sheet_title: str | None = None
    source_sheet_id: int | None = None
    sheet_id_num: int | None = None

    # find_replace
    find: str | None = None
    replace: str | None = None
    sheet_name: str | None = None  # optional scope
    match_case: bool = False
    match_entire_cell: bool = False

    # batch_update — raw API requests array
    requests: Any = None

    # lookup_row / add_row / update_row / delete_row — row-level CRUD
    # ergonomics on top of values.get / append / update.
    lookup_column: str | None = None  # e.g. "Email" (header name) — picker emits string
    lookup_value: str | None = None
    row_index: int | None = None  # 1-based row index for update_row / delete_row
    row_data: Any = None  # dict {column_header: value} for add_row / update_row

    # rename_sheet
    new_sheet_title: str | None = None

    # share — Drive ACL
    share_email: str | None = None
    share_role: str = "reader"  # reader / commenter / writer
    share_send_notification: bool = False

    # export — Drive export
    export_format: str = "pdf"  # pdf / xlsx / csv / ods / html

    # sort_range
    sort_column_index: int = 0  # zero-based column index inside the range
    sort_order: str = "ASCENDING"  # ASCENDING / DESCENDING

    # format_range — pick common knobs; power users still have batch_update
    format_bold: bool = False
    format_italic: bool = False
    format_background_color: str | None = None  # "#rrggbb"
    format_text_color: str | None = None
    format_number_format: str | None = None  # e.g. "0.00", "yyyy-mm-dd", "$#,##0.00"

    @field_validator("spreadsheet_id", mode="before")
    @classmethod
    def _coerce_spreadsheet_id(cls, value: Any) -> str | None:
        # The picker emits `{id, name}` so the editor can show the picked
        # spreadsheet's name back — runtime only cares about the id.
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) and v else None
        if value in (None, ""):
            return None
        return str(value)

    @field_validator("source_sheet_id", "sheet_id_num", mode="before")
    @classmethod
    def _coerce_sheet_numeric_id(cls, value: Any) -> int | None:
        # Tab picker may emit `{sheet_id, title}` — collapse to the numeric id.
        if isinstance(value, dict):
            v = value.get("sheet_id")
            try:
                return int(v) if v is not None else None
            except (TypeError, ValueError):
                return None
        if value in (None, ""):
            return None
        try:
            return int(value)
        except (TypeError, ValueError):
            return None

    @field_validator("sheet_name", mode="before")
    @classmethod
    def _coerce_sheet_name(cls, value: Any) -> str | None:
        # Tab picker (`valueAs="title"`) emits a plain string title;
        # accept dict form too for forward-compat.
        if isinstance(value, dict):
            v = value.get("title")
            return str(v) if isinstance(v, str) and v else None
        if value in (None, ""):
            return None
        return str(value)


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GoogleSheetsNode(BaseNode[GoogleSheetsProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleSheetsProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.google_sheets",
            name=NAME,
            category="integration",
            description=(
                "Read, write, create, and modify Google Sheets via OAuth — "
                "values, sheets, find/replace, and raw batch requests."
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
                    "default": "get_values",
                    "options": [
                        {"label": "Read Values", "value": "get_values"},
                        {"label": "Update Values", "value": "update_values"},
                        {"label": "Append Values", "value": "append_values"},
                        {"label": "Clear Values", "value": "clear_values"},
                        {"label": "Get Spreadsheet Metadata", "value": "get_spreadsheet"},
                        {"label": "Create Spreadsheet", "value": "create_spreadsheet"},
                        {"label": "Add Sheet (Tab)", "value": "create_sheet"},
                        {"label": "Duplicate Sheet", "value": "duplicate_sheet"},
                        {"label": "Delete Sheet", "value": "delete_sheet"},
                        {"label": "Find & Replace", "value": "find_replace"},
                        {"label": "Lookup Row", "value": "lookup_row"},
                        {"label": "Add Row", "value": "add_row"},
                        {"label": "Update Row", "value": "update_row"},
                        {"label": "Delete Row", "value": "delete_row"},
                        {"label": "Rename Sheet", "value": "rename_sheet"},
                        {"label": "Share Spreadsheet", "value": "share"},
                        {"label": "Export Spreadsheet", "value": "export"},
                        {"label": "Sort Range", "value": "sort_range"},
                        {"label": "Format Range", "value": "format_range"},
                        {"label": "Auto-resize Columns", "value": "auto_resize_columns"},
                        {"label": "Batch Update (Raw)", "value": "batch_update"},
                    ],
                },
                # spreadsheet_id — required for everything except create_spreadsheet
                {
                    "name": "spreadsheet_id",
                    "label": "Spreadsheet",
                    "type": "string",
                    "remote": {
                        "provider": "google",
                        "resource": "drive_files",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                    "required": True,
                    "typeOptions": {
                        "mimeType": "application/vnd.google-apps.spreadsheet",
                        "placeholder": "Pick a spreadsheet…",
                        "searchPlaceholder": "Search your spreadsheets…",
                        "createPlaceholder": "Create new spreadsheet…",
                    },
                    "condition": _cond_any(
                        "get_spreadsheet",
                        "get_values",
                        "update_values",
                        "append_values",
                        "clear_values",
                        "create_sheet",
                        "duplicate_sheet",
                        "delete_sheet",
                        "find_replace",
                        "batch_update",
                        "lookup_row",
                        "add_row",
                        "update_row",
                        "delete_row",
                        "rename_sheet",
                        "share",
                        "export",
                        "sort_range",
                        "format_range",
                        "auto_resize_columns",
                    ),
                },
                # range_name — used by value-based ops + sort / format / auto-resize
                {
                    "name": "range_name",
                    "label": "Range",
                    "type": "string",
                    "placeholder": "Sheet1!A1:D10",
                    "required": True,
                    "condition": _cond_any(
                        "get_values",
                        "update_values",
                        "append_values",
                        "clear_values",
                        "sort_range",
                        "format_range",
                    ),
                },
                # update / append shared options
                {
                    "name": "value_input_option",
                    "label": "Value parsing",
                    "type": "options",
                    "default": "USER_ENTERED",
                    "options": [
                        {"label": "User Entered (parses formulas, dates)", "value": "USER_ENTERED"},
                        {"label": "Raw (no parsing)", "value": "RAW"},
                    ],
                    "condition": _cond_any("update_values", "append_values"),
                    "mode": "advanced",
                },
                {
                    "name": "values",
                    "label": "Values",
                    "type": "json",
                    "placeholder": '[["Header1", "Header2"], ["Val1", "Val2"]]',
                    "description": "Array of rows. Each row is an array of cell values.",
                    "required": True,
                    "condition": _cond_any("update_values", "append_values"),
                },
                # create_spreadsheet
                {
                    "name": "title",
                    "label": "Spreadsheet title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Q1 Reports",
                    "condition": _cond("create_spreadsheet"),
                },
                {
                    "name": "initial_sheets",
                    "label": "Initial sheets",
                    "type": "json",
                    "placeholder": '["Summary", "Details"]',
                    "description": "Optional array of sheet titles. Defaults to one sheet named Sheet1.",
                    "condition": _cond("create_spreadsheet"),
                    "mode": "advanced",
                },
                # create_sheet
                {
                    "name": "sheet_title",
                    "label": "Sheet title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Q2",
                    "condition": _cond_any("create_sheet", "duplicate_sheet"),
                },
                # duplicate_sheet / delete_sheet — picker emits the numeric sheetId
                {
                    "name": "source_sheet_id",
                    "label": "Source sheet",
                    "type": "string",
                    "remote": {
                        "provider": "google",
                        "resource": "sheet_tabs",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                    "required": True,
                    "typeOptions": {"valueAs": "sheet_id"},
                    "condition": _cond("duplicate_sheet"),
                },
                {
                    "name": "sheet_id_num",
                    "label": "Sheet",
                    "type": "string",
                    "remote": {
                        "provider": "google",
                        "resource": "sheet_tabs",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                    "required": True,
                    "typeOptions": {"valueAs": "sheet_id"},
                    "condition": _cond_any("delete_sheet", "rename_sheet"),
                },
                # rename_sheet — new tab title
                {
                    "name": "new_sheet_title",
                    "label": "New title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Renamed",
                    "condition": _cond("rename_sheet"),
                },
                # find_replace
                {
                    "name": "find",
                    "label": "Find",
                    "type": "string",
                    "required": True,
                    "placeholder": "old text",
                    "condition": _cond("find_replace"),
                },
                {
                    "name": "replace",
                    "label": "Replace with",
                    "type": "string",
                    "placeholder": "new text",
                    "condition": _cond("find_replace"),
                },
                {
                    "name": "sheet_name",
                    "label": "Scope to sheet",
                    "type": "string",
                    "remote": {
                        "provider": "google",
                        "resource": "sheet_tabs",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                    "typeOptions": {"valueAs": "title"},
                    "description": "Leave blank to search every sheet.",
                    "condition": _cond("find_replace"),
                    "mode": "advanced",
                },
                {
                    "name": "match_case",
                    "label": "Match case",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("find_replace"),
                    "mode": "advanced",
                },
                {
                    "name": "match_entire_cell",
                    "label": "Match entire cell",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("find_replace"),
                    "mode": "advanced",
                },
                # lookup_row / add_row / update_row / delete_row — row-level CRUD
                # Tab + header-aware. Headers are read live so the user types
                # the column NAME, not the letter — matches n8n / Zapier UX.
                {
                    "name": "sheet_name",
                    "label": "Sheet (tab)",
                    "type": "string",
                    "remote": {
                        "provider": "google",
                        "resource": "sheet_tabs",
                        "params": {},
                        "depends_on": [],
                        "allow_manual": True,
                    },
                    "typeOptions": {"valueAs": "title"},
                    "required": True,
                    "condition": _cond_any(
                        "lookup_row",
                        "add_row",
                        "update_row",
                        "delete_row",
                        "auto_resize_columns",
                    ),
                },
                {
                    "name": "lookup_column",
                    "label": "Look up by column",
                    "type": "string",
                    "required": True,
                    "placeholder": "Email",
                    "description": "Column header name to search in (row 1 holds headers).",
                    "condition": _cond("lookup_row"),
                },
                {
                    "name": "lookup_value",
                    "label": "Match this value",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $step.email }}",
                    "condition": _cond("lookup_row"),
                },
                {
                    "name": "row_data",
                    "label": "Row data",
                    "type": "json",
                    "required": True,
                    "placeholder": '{"Name": "Alice", "Email": "a@b.com"}',
                    "description": "Object keyed by header name. Missing headers get blank cells.",
                    "condition": _cond_any("add_row", "update_row"),
                },
                {
                    "name": "row_index",
                    "label": "Row number",
                    "type": "number",
                    "required": True,
                    "placeholder": "2",
                    "description": "1-based row number (row 1 is the header).",
                    "condition": _cond_any("update_row", "delete_row"),
                },
                # share — via Drive ACL API
                {
                    "name": "share_email",
                    "label": "Share with email",
                    "type": "string",
                    "required": True,
                    "placeholder": "person@example.com",
                    "condition": _cond("share"),
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
                    "condition": _cond("share"),
                },
                {
                    "name": "share_send_notification",
                    "label": "Send notification email",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("share"),
                    "mode": "advanced",
                },
                # export — Drive export
                {
                    "name": "export_format",
                    "label": "Format",
                    "type": "options",
                    "default": "pdf",
                    "options": [
                        {"label": "PDF", "value": "pdf"},
                        {"label": "Excel (.xlsx)", "value": "xlsx"},
                        {"label": "CSV", "value": "csv"},
                        {"label": "OpenDocument (.ods)", "value": "ods"},
                        {"label": "HTML (zip)", "value": "html"},
                    ],
                    "condition": _cond("export"),
                },
                # sort_range
                {
                    "name": "sort_column_index",
                    "label": "Sort by column index",
                    "type": "number",
                    "default": 0,
                    "description": "Zero-based column position inside the range.",
                    "condition": _cond("sort_range"),
                },
                {
                    "name": "sort_order",
                    "label": "Order",
                    "type": "options",
                    "default": "ASCENDING",
                    "options": [
                        {"label": "Ascending (A → Z)", "value": "ASCENDING"},
                        {"label": "Descending (Z → A)", "value": "DESCENDING"},
                    ],
                    "condition": _cond("sort_range"),
                },
                # format_range
                {
                    "name": "format_bold",
                    "label": "Bold",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("format_range"),
                },
                {
                    "name": "format_italic",
                    "label": "Italic",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("format_range"),
                },
                {
                    "name": "format_background_color",
                    "label": "Background colour",
                    "type": "string",
                    "placeholder": "#fff3a3",
                    "description": "Hex like `#rrggbb`.",
                    "condition": _cond("format_range"),
                },
                {
                    "name": "format_text_color",
                    "label": "Text colour",
                    "type": "string",
                    "placeholder": "#111111",
                    "description": "Hex like `#rrggbb`.",
                    "condition": _cond("format_range"),
                },
                {
                    "name": "format_number_format",
                    "label": "Number format",
                    "type": "string",
                    "placeholder": "0.00 or $#,##0.00 or yyyy-mm-dd",
                    "description": "Google Sheets number-format pattern.",
                    "condition": _cond("format_range"),
                    "mode": "advanced",
                },
                # batch_update
                {
                    "name": "requests",
                    "label": "Requests (raw)",
                    "type": "json",
                    "required": True,
                    "placeholder": '[{"updateSheetProperties": {"properties": {"sheetId": 0, "title": "Renamed"}, "fields": "title"}}]',
                    "description": "Raw Sheets API `requests[]` array. See Sheets API docs.",
                    "condition": _cond("batch_update"),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "spreadsheetId", "type": "string"},
                {"label": "values", "type": "array"},
                {"label": "updatedRange", "type": "string"},
                {"label": "updatedRows", "type": "number"},
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

        op = self.props.operation
        handler = _HANDLERS.get(op)
        if handler is None:
            return NodeResult(success=False, error=f"Unknown operation: {op}")

        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }

        try:
            async with httpx.AsyncClient(timeout=30) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Google Sheets API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleSheetsNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── operation handlers ──────────────────────────────────────────────────


def _require_spreadsheet_id(node: GoogleSheetsNode) -> str | NodeResult:
    sid = (node.props.spreadsheet_id or "").strip()
    if not sid:
        return NodeResult(success=False, error="Spreadsheet ID required.")
    return sid


def _require_range(node: GoogleSheetsNode) -> str | NodeResult:
    rng = (node.props.range_name or "").strip()
    if not rng:
        return NodeResult(success=False, error="Range is required.")
    return rng


async def _get_spreadsheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    r = await client.get(f"{SHEETS_API}/{sid}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_values(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    r = await client.get(f"{SHEETS_API}/{sid}/values/{rng}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _update_values(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    body = {
        "range": rng,
        "majorDimension": "ROWS",
        "values": node.props.values or [],
    }
    r = await client.put(
        f"{SHEETS_API}/{sid}/values/{rng}",
        headers=headers,
        json=body,
        params={"valueInputOption": node.props.value_input_option},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _append_values(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    body = {
        "range": rng,
        "majorDimension": "ROWS",
        "values": node.props.values or [],
    }
    r = await client.post(
        f"{SHEETS_API}/{sid}/values/{rng}:append",
        headers=headers,
        json=body,
        params={
            "valueInputOption": node.props.value_input_option,
            "insertDataOption": "INSERT_ROWS",
        },
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _clear_values(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    r = await client.post(f"{SHEETS_API}/{sid}/values/{rng}:clear", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _create_spreadsheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    title = (node.props.title or "").strip()
    if not title:
        return NodeResult(success=False, error="Title is required.")
    body: dict[str, Any] = {"properties": {"title": title}}
    raw_sheets = node.props.initial_sheets
    sheet_titles: list[str] = []
    if isinstance(raw_sheets, list):
        sheet_titles = [str(t) for t in raw_sheets if str(t).strip()]
    if sheet_titles:
        body["sheets"] = [{"properties": {"title": t}} for t in sheet_titles]
    r = await client.post(SHEETS_API, headers=headers, json=body)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _batch_update_request(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    sid: str,
    requests: list[dict[str, Any]],
) -> dict[str, Any]:
    r = await client.post(
        f"{SHEETS_API}/{sid}:batchUpdate",
        headers=headers,
        json={"requests": requests},
    )
    r.raise_for_status()
    return r.json()


async def _create_sheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    title = (node.props.sheet_title or "").strip()
    if not title:
        return NodeResult(success=False, error="Sheet title is required.")
    result = await _batch_update_request(
        client,
        headers,
        sid,
        [{"addSheet": {"properties": {"title": title}}}],
    )
    return NodeResult(success=True, output_data=result)


async def _duplicate_sheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    if node.props.source_sheet_id is None:
        return NodeResult(success=False, error="Source sheet ID is required.")
    title = (node.props.sheet_title or "").strip()
    req: dict[str, Any] = {"duplicateSheet": {"sourceSheetId": int(node.props.source_sheet_id)}}
    if title:
        req["duplicateSheet"]["newSheetName"] = title
    result = await _batch_update_request(client, headers, sid, [req])
    return NodeResult(success=True, output_data=result)


async def _delete_sheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    if node.props.sheet_id_num is None:
        return NodeResult(success=False, error="Sheet ID is required.")
    result = await _batch_update_request(
        client,
        headers,
        sid,
        [{"deleteSheet": {"sheetId": int(node.props.sheet_id_num)}}],
    )
    return NodeResult(success=True, output_data=result)


async def _find_replace(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    find = node.props.find or ""
    if find == "":
        return NodeResult(success=False, error="Find value is required.")
    body: dict[str, Any] = {
        "find": find,
        "replacement": node.props.replace or "",
        "matchCase": bool(node.props.match_case),
        "matchEntireCell": bool(node.props.match_entire_cell),
    }
    sheet_name = (node.props.sheet_name or "").strip()
    if sheet_name:
        # Resolve sheet name → numeric sheetId so we can target it precisely.
        # `find_replace` accepts either a `range` or a `sheetId`; pick sheetId
        # because the user gave us a name, not a range.
        meta = await client.get(
            f"{SHEETS_API}/{sid}",
            headers=headers,
            params={"fields": "sheets.properties(sheetId,title)"},
        )
        meta.raise_for_status()
        sheet_id_num: int | None = None
        for sh in meta.json().get("sheets") or []:
            props = (sh or {}).get("properties") or {}
            if str(props.get("title") or "") == sheet_name:
                sheet_id_num = int(props.get("sheetId"))
                break
        if sheet_id_num is None:
            return NodeResult(
                success=False, error=f"Sheet '{sheet_name}' not found in spreadsheet."
            )
        body["sheetId"] = sheet_id_num
    else:
        body["allSheets"] = True
    result = await _batch_update_request(client, headers, sid, [{"findReplace": body}])
    return NodeResult(success=True, output_data=result)


async def _batch_update(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    requests = node.props.requests
    if not isinstance(requests, list) or not requests:
        return NodeResult(
            success=False,
            error="`requests` must be a non-empty array of Sheets API request objects.",
        )
    result = await _batch_update_request(client, headers, sid, requests)
    return NodeResult(success=True, output_data=result)


# ── row-level helpers ───────────────────────────────────────────────────


def _require_sheet_name(node: GoogleSheetsNode) -> str | NodeResult:
    name = (node.props.sheet_name or "").strip()
    if not name:
        return NodeResult(success=False, error="Sheet (tab) is required.")
    return name


def _column_letter(n: int) -> str:
    """Convert a zero-based column index to A1 letters (0 → A, 25 → Z, 26 → AA)."""
    letters = ""
    n += 1
    while n > 0:
        n, rem = divmod(n - 1, 26)
        letters = chr(65 + rem) + letters
    return letters


async def _fetch_headers(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    sid: str,
    sheet_name: str,
) -> list[str]:
    """Read row 1 of the sheet — headers used to map dict → row array."""
    r = await client.get(
        f"{SHEETS_API}/{sid}/values/{sheet_name}!1:1",
        headers=headers,
    )
    r.raise_for_status()
    rows = r.json().get("values") or []
    return [str(c) for c in (rows[0] if rows else [])]


def _row_dict_to_values(row_data: dict[str, Any], headers_list: list[str]) -> list[Any]:
    """Slot a dict-of-cells into a positional row matching the headers.

    Unknown keys are dropped — silently mapping a typo to an arbitrary
    column would corrupt user data. We log them at the row payload level
    instead by surfacing them in the response output (`ignored_keys`)."""
    return [row_data.get(h, "") for h in headers_list]


# ── new operation handlers ──────────────────────────────────────────────


async def _lookup_row(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    sheet_name = _require_sheet_name(node)
    if isinstance(sheet_name, NodeResult):
        return sheet_name
    column = (node.props.lookup_column or "").strip()
    if not column:
        return NodeResult(success=False, error="`lookup_column` is required.")
    target = node.props.lookup_value if node.props.lookup_value is not None else ""

    headers_list = await _fetch_headers(client, headers, sid, sheet_name)
    if column not in headers_list:
        return NodeResult(
            success=False,
            error=f"Column header {column!r} not found in row 1 of {sheet_name!r}.",
        )
    col_idx = headers_list.index(column)
    # Pull every populated row from row 2 onwards.
    r = await client.get(
        f"{SHEETS_API}/{sid}/values/{sheet_name}!A2:{_column_letter(len(headers_list) - 1)}",
        headers=headers,
    )
    r.raise_for_status()
    rows = r.json().get("values") or []
    for offset, row in enumerate(rows):
        if col_idx < len(row) and str(row[col_idx]) == str(target):
            return NodeResult(
                success=True,
                output_data={
                    "row_index": 2 + offset,
                    "values": row,
                    "row": dict(
                        zip(headers_list, row + [""] * (len(headers_list) - len(row)), strict=False)
                    ),
                    "matched": True,
                },
            )
    return NodeResult(
        success=True,
        output_data={"matched": False, "row_index": None, "values": [], "row": {}},
    )


async def _add_row(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    sheet_name = _require_sheet_name(node)
    if isinstance(sheet_name, NodeResult):
        return sheet_name
    if not isinstance(node.props.row_data, dict):
        return NodeResult(success=False, error="`row_data` must be a JSON object.")

    headers_list = await _fetch_headers(client, headers, sid, sheet_name)
    if not headers_list:
        return NodeResult(
            success=False,
            error=f"Sheet {sheet_name!r} has no header row. Add column headers in row 1 first.",
        )
    row_values = _row_dict_to_values(node.props.row_data, headers_list)
    ignored = [k for k in node.props.row_data if k not in headers_list]

    body = {"range": sheet_name, "majorDimension": "ROWS", "values": [row_values]}
    r = await client.post(
        f"{SHEETS_API}/{sid}/values/{sheet_name}:append",
        headers=headers,
        json=body,
        params={
            "valueInputOption": node.props.value_input_option,
            "insertDataOption": "INSERT_ROWS",
        },
    )
    r.raise_for_status()
    data = r.json()
    data["ignored_keys"] = ignored
    return NodeResult(success=True, output_data=data)


async def _update_row(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    sheet_name = _require_sheet_name(node)
    if isinstance(sheet_name, NodeResult):
        return sheet_name
    if node.props.row_index is None or node.props.row_index < 1:
        return NodeResult(success=False, error="`row_index` is required (1-based).")
    if not isinstance(node.props.row_data, dict):
        return NodeResult(success=False, error="`row_data` must be a JSON object.")

    headers_list = await _fetch_headers(client, headers, sid, sheet_name)
    if not headers_list:
        return NodeResult(
            success=False,
            error=f"Sheet {sheet_name!r} has no header row. Add column headers in row 1 first.",
        )
    row_values = _row_dict_to_values(node.props.row_data, headers_list)
    ignored = [k for k in node.props.row_data if k not in headers_list]

    last_col = _column_letter(len(headers_list) - 1)
    rng = f"{sheet_name}!A{node.props.row_index}:{last_col}{node.props.row_index}"
    r = await client.put(
        f"{SHEETS_API}/{sid}/values/{rng}",
        headers=headers,
        json={"range": rng, "majorDimension": "ROWS", "values": [row_values]},
        params={"valueInputOption": node.props.value_input_option},
    )
    r.raise_for_status()
    data = r.json()
    data["ignored_keys"] = ignored
    return NodeResult(success=True, output_data=data)


async def _delete_row(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    sheet_name = _require_sheet_name(node)
    if isinstance(sheet_name, NodeResult):
        return sheet_name
    if node.props.row_index is None or node.props.row_index < 1:
        return NodeResult(success=False, error="`row_index` is required (1-based).")

    # `deleteDimension` needs the numeric sheetId. Look it up by name.
    meta = await client.get(
        f"{SHEETS_API}/{sid}",
        headers=headers,
        params={"fields": "sheets.properties(sheetId,title)"},
    )
    meta.raise_for_status()
    sheet_id_num: int | None = None
    for sh in meta.json().get("sheets") or []:
        props = (sh or {}).get("properties") or {}
        if str(props.get("title") or "") == sheet_name:
            sheet_id_num = int(props.get("sheetId"))
            break
    if sheet_id_num is None:
        return NodeResult(success=False, error=f"Sheet {sheet_name!r} not found.")

    result = await _batch_update_request(
        client,
        headers,
        sid,
        [
            {
                "deleteDimension": {
                    "range": {
                        "sheetId": sheet_id_num,
                        "dimension": "ROWS",
                        "startIndex": node.props.row_index - 1,
                        "endIndex": node.props.row_index,
                    }
                }
            }
        ],
    )
    return NodeResult(success=True, output_data=result)


async def _rename_sheet(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    if node.props.sheet_id_num is None:
        return NodeResult(success=False, error="Sheet is required.")
    new_title = (node.props.new_sheet_title or "").strip()
    if not new_title:
        return NodeResult(success=False, error="`new_sheet_title` is required.")
    result = await _batch_update_request(
        client,
        headers,
        sid,
        [
            {
                "updateSheetProperties": {
                    "properties": {
                        "sheetId": int(node.props.sheet_id_num),
                        "title": new_title,
                    },
                    "fields": "title",
                }
            }
        ],
    )
    return NodeResult(success=True, output_data=result)


async def _share(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    email = (node.props.share_email or "").strip()
    if not email:
        return NodeResult(success=False, error="`share_email` is required.")
    role = node.props.share_role or "reader"
    body = {"type": "user", "role": role, "emailAddress": email}
    r = await client.post(
        f"https://www.googleapis.com/drive/v3/files/{sid}/permissions",
        headers=headers,
        json=body,
        params={
            "sendNotificationEmail": ("true" if node.props.share_send_notification else "false"),
            "supportsAllDrives": "true",
        },
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


_EXPORT_MIME: dict[str, str] = {
    "pdf": "application/pdf",
    "xlsx": "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    "csv": "text/csv",
    "ods": "application/vnd.oasis.opendocument.spreadsheet",
    "html": "application/zip",  # Drive ships HTML exports as a zip
}


async def _export(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    import base64

    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    fmt = (node.props.export_format or "pdf").lower()
    mime = _EXPORT_MIME.get(fmt)
    if not mime:
        return NodeResult(success=False, error=f"Unsupported export format: {fmt}")
    r = await client.get(
        f"https://www.googleapis.com/drive/v3/files/{sid}/export",
        headers=headers,
        params={"mimeType": mime},
    )
    r.raise_for_status()
    payload = base64.b64encode(r.content).decode("ascii")
    return NodeResult(
        success=True,
        output_data={
            "format": fmt,
            "mime_type": mime,
            "size_bytes": len(r.content),
            "content_b64": payload,
        },
    )


def _parse_range_for_grid(range_str: str) -> dict[str, Any] | None:
    """Best-effort A1 → grid-range parsing. Supports `Sheet1!A1:D10` and
    `Sheet1!A:D` (column-only) forms. Returns None when the parse fails
    — the caller surfaces a user-friendly error."""
    import re

    if "!" not in range_str:
        return None
    sheet_name, a1 = range_str.split("!", 1)
    sheet_name = sheet_name.strip().strip("'")
    m = re.match(r"^([A-Z]+)(\d*):([A-Z]+)(\d*)$", a1.replace(" ", ""))
    if not m:
        return None
    start_col_letters, start_row, end_col_letters, end_row = m.groups()

    def letters_to_idx(letters: str) -> int:
        n = 0
        for ch in letters:
            n = n * 26 + (ord(ch) - 64)
        return n - 1

    out: dict[str, Any] = {
        "sheet_name": sheet_name,
        "startColumnIndex": letters_to_idx(start_col_letters),
        "endColumnIndex": letters_to_idx(end_col_letters) + 1,
    }
    if start_row:
        out["startRowIndex"] = int(start_row) - 1
    if end_row:
        out["endRowIndex"] = int(end_row)
    return out


async def _resolve_sheet_id_from_range(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    sid: str,
    sheet_name: str,
) -> int | None:
    meta = await client.get(
        f"{SHEETS_API}/{sid}",
        headers=headers,
        params={"fields": "sheets.properties(sheetId,title)"},
    )
    meta.raise_for_status()
    for sh in meta.json().get("sheets") or []:
        props = (sh or {}).get("properties") or {}
        if str(props.get("title") or "") == sheet_name:
            return int(props.get("sheetId"))
    return None


async def _sort_range(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    parsed = _parse_range_for_grid(rng)
    if parsed is None:
        return NodeResult(success=False, error=f"Could not parse range: {rng!r}.")
    sheet_id_num = await _resolve_sheet_id_from_range(client, headers, sid, parsed["sheet_name"])
    if sheet_id_num is None:
        return NodeResult(success=False, error=f"Sheet {parsed['sheet_name']!r} not found.")
    grid_range: dict[str, Any] = {
        "sheetId": sheet_id_num,
        "startColumnIndex": parsed["startColumnIndex"],
        "endColumnIndex": parsed["endColumnIndex"],
    }
    if "startRowIndex" in parsed:
        grid_range["startRowIndex"] = parsed["startRowIndex"]
    if "endRowIndex" in parsed:
        grid_range["endRowIndex"] = parsed["endRowIndex"]
    result = await _batch_update_request(
        client,
        headers,
        sid,
        [
            {
                "sortRange": {
                    "range": grid_range,
                    "sortSpecs": [
                        {
                            "dimensionIndex": (
                                parsed["startColumnIndex"]
                                + max(0, int(node.props.sort_column_index or 0))
                            ),
                            "sortOrder": node.props.sort_order or "ASCENDING",
                        }
                    ],
                }
            }
        ],
    )
    return NodeResult(success=True, output_data=result)


def _hex_to_rgb01(hex_str: str) -> dict[str, float] | None:
    """`#rrggbb` → Sheets RGB struct (0..1 floats). Returns None on parse
    failure so the caller can decide whether to drop or error."""
    h = (hex_str or "").strip().lstrip("#")
    if len(h) != 6:
        return None
    try:
        r, g, b = int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16)
    except ValueError:
        return None
    return {"red": r / 255, "green": g / 255, "blue": b / 255}


async def _format_range(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    rng = _require_range(node)
    if isinstance(rng, NodeResult):
        return rng
    parsed = _parse_range_for_grid(rng)
    if parsed is None:
        return NodeResult(success=False, error=f"Could not parse range: {rng!r}.")
    sheet_id_num = await _resolve_sheet_id_from_range(client, headers, sid, parsed["sheet_name"])
    if sheet_id_num is None:
        return NodeResult(success=False, error=f"Sheet {parsed['sheet_name']!r} not found.")

    fmt_cell: dict[str, Any] = {}
    text_fmt: dict[str, Any] = {}
    fields_parts: list[str] = []

    if node.props.format_bold:
        text_fmt["bold"] = True
        fields_parts.append("userEnteredFormat.textFormat.bold")
    if node.props.format_italic:
        text_fmt["italic"] = True
        fields_parts.append("userEnteredFormat.textFormat.italic")
    if node.props.format_text_color:
        rgb = _hex_to_rgb01(node.props.format_text_color)
        if rgb is None:
            return NodeResult(success=False, error="`format_text_color` must be a `#rrggbb` hex.")
        text_fmt["foregroundColor"] = rgb
        fields_parts.append("userEnteredFormat.textFormat.foregroundColor")
    if text_fmt:
        fmt_cell["textFormat"] = text_fmt
    if node.props.format_background_color:
        rgb = _hex_to_rgb01(node.props.format_background_color)
        if rgb is None:
            return NodeResult(
                success=False, error="`format_background_color` must be a `#rrggbb` hex."
            )
        fmt_cell["backgroundColor"] = rgb
        fields_parts.append("userEnteredFormat.backgroundColor")
    if node.props.format_number_format:
        fmt_cell["numberFormat"] = {
            "type": "NUMBER",
            "pattern": node.props.format_number_format,
        }
        fields_parts.append("userEnteredFormat.numberFormat")

    if not fields_parts:
        return NodeResult(success=False, error="Pick at least one formatting knob.")

    grid_range: dict[str, Any] = {
        "sheetId": sheet_id_num,
        "startColumnIndex": parsed["startColumnIndex"],
        "endColumnIndex": parsed["endColumnIndex"],
    }
    if "startRowIndex" in parsed:
        grid_range["startRowIndex"] = parsed["startRowIndex"]
    if "endRowIndex" in parsed:
        grid_range["endRowIndex"] = parsed["endRowIndex"]
    result = await _batch_update_request(
        client,
        headers,
        sid,
        [
            {
                "repeatCell": {
                    "range": grid_range,
                    "cell": {"userEnteredFormat": fmt_cell},
                    "fields": ",".join(fields_parts),
                }
            }
        ],
    )
    return NodeResult(success=True, output_data=result)


async def _auto_resize_columns(
    node: GoogleSheetsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    sid = _require_spreadsheet_id(node)
    if isinstance(sid, NodeResult):
        return sid
    sheet_name = _require_sheet_name(node)
    if isinstance(sheet_name, NodeResult):
        return sheet_name
    sheet_id_num = await _resolve_sheet_id_from_range(client, headers, sid, sheet_name)
    if sheet_id_num is None:
        return NodeResult(success=False, error=f"Sheet {sheet_name!r} not found.")
    # Optional range_name narrows to specific columns; absent → resize all.
    dim_range: dict[str, Any] = {"sheetId": sheet_id_num, "dimension": "COLUMNS"}
    if node.props.range_name:
        parsed = _parse_range_for_grid(node.props.range_name)
        if parsed is not None:
            dim_range["startIndex"] = parsed["startColumnIndex"]
            dim_range["endIndex"] = parsed["endColumnIndex"]
    result = await _batch_update_request(
        client,
        headers,
        sid,
        [{"autoResizeDimensions": {"dimensions": dim_range}}],
    )
    return NodeResult(success=True, output_data=result)


_HANDLERS: dict[str, Any] = {
    "get_spreadsheet": _get_spreadsheet,
    "get_values": _get_values,
    "update_values": _update_values,
    "append_values": _append_values,
    "clear_values": _clear_values,
    "create_spreadsheet": _create_spreadsheet,
    "create_sheet": _create_sheet,
    "duplicate_sheet": _duplicate_sheet,
    "delete_sheet": _delete_sheet,
    "find_replace": _find_replace,
    "batch_update": _batch_update,
    "lookup_row": _lookup_row,
    "add_row": _add_row,
    "update_row": _update_row,
    "delete_row": _delete_row,
    "rename_sheet": _rename_sheet,
    "share": _share,
    "export": _export,
    "sort_range": _sort_range,
    "format_range": _format_range,
    "auto_resize_columns": _auto_resize_columns,
}
