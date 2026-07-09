"""Google Docs action node — one node, 18 operations.

Document CRUD
  - `create`           / `get_text`     / `get_with_structure`
  - `rename`           / `copy`         / `delete`
  - `share`            / `export`

Text editing
  - `append_text`      / `insert_text`
  - `find_replace`     / `delete_range`
  - `format_text`      / `set_paragraph_style`

Insert structure
  - `insert_image`     / `insert_table`
  - `insert_page_break`

Header / footer
  - `set_header`       / `set_footer`

OAuth scope: `documents` + `drive.file` (already in GoogleOAuthProvider).
Mime: `application/vnd.google-apps.document`.

`document_id` is wired through the generic `google-file` picker — same
renderer Sheets uses, with the Docs mime configured.
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
from apps.api.app.node_system.nodes.google.google_sheets.google_sheets import _hex_to_rgb01

logger = get_logger(__name__)

DOCS_API = "https://docs.googleapis.com/v1/documents"
DRIVE_API = "https://www.googleapis.com/drive/v3"
DOC_MIME = "application/vnd.google-apps.document"


# Export targets — Docs is widely interoperable, so we surface the full
# set Drive supports for Google Docs.
_EXPORT_MIME: dict[str, str] = {
    "pdf": "application/pdf",
    "docx": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    "html": "application/zip",  # Drive ships HTML as a zip of HTML + assets
    "txt": "text/plain",
    "epub": "application/epub+zip",
    "odt": "application/vnd.oasis.opendocument.text",
    "rtf": "application/rtf",
}


# Heading levels we surface in `set_paragraph_style`. The Docs API name
# is `namedStyleType`. Keep the dropdown small + meaningful instead of
# exposing every internal style.
_NAMED_STYLE_OPTIONS: list[dict[str, str]] = [
    {"label": "Normal text", "value": "NORMAL_TEXT"},
    {"label": "Title", "value": "TITLE"},
    {"label": "Subtitle", "value": "SUBTITLE"},
    {"label": "Heading 1", "value": "HEADING_1"},
    {"label": "Heading 2", "value": "HEADING_2"},
    {"label": "Heading 3", "value": "HEADING_3"},
    {"label": "Heading 4", "value": "HEADING_4"},
    {"label": "Heading 5", "value": "HEADING_5"},
    {"label": "Heading 6", "value": "HEADING_6"},
]


_ALIGNMENT_OPTIONS: list[dict[str, str]] = [
    {"label": "Left", "value": "START"},
    {"label": "Center", "value": "CENTER"},
    {"label": "Right", "value": "END"},
    {"label": "Justify", "value": "JUSTIFIED"},
]


class GoogleDocsProperties(BaseModel):
    credential: str | None = None
    operation: str = "get_text"

    document_id: str | None = None

    # create / copy / rename
    title: str | None = None
    initial_content: str | None = None  # plain text — gets inserted at index 1 on create
    new_title: str | None = None

    # text editing
    text: Any = None  # accept Any so expressions render through unchanged
    index: int | None = None
    start_index: int | None = None
    end_index: int | None = None

    # find_replace
    find_text: str | None = None
    replace_text: str | None = None
    match_case: bool = False

    # insert_image
    image_content: Any = None  # `media` field — emits {type, value} discriminated union
    image_width_pt: float | None = None
    image_height_pt: float | None = None

    # insert_table
    table_rows: int = 2
    table_cols: int = 2

    # format_text
    format_bold: bool = False
    format_italic: bool = False
    format_underline: bool = False
    format_strikethrough: bool = False
    format_font_family: str | None = None
    format_font_size_pt: float | None = None
    format_text_color: str | None = None  # #rrggbb
    format_background_color: str | None = None

    # set_paragraph_style
    paragraph_named_style: str | None = None  # NORMAL_TEXT / HEADING_1 / TITLE / …
    paragraph_alignment: str | None = None  # START / CENTER / END / JUSTIFIED
    paragraph_indent_start_pt: float | None = None

    # share
    share_email: str | None = None
    share_role: str = "reader"  # reader / commenter / writer
    share_send_notification: bool = False

    # export
    export_format: str = "pdf"

    # set_header / set_footer
    header_text: str | None = None
    footer_text: str | None = None

    @field_validator("document_id", mode="before")
    @classmethod
    def _coerce_document_id(cls, value: Any) -> str | None:
        # Picker emits `{id, name}` so the editor can show the picked
        # title back — runtime only needs the id.
        if isinstance(value, dict):
            v = value.get("id")
            return str(v) if isinstance(v, str) and v else None
        if value in (None, ""):
            return None
        return str(value)


def _cond(op: str) -> dict[str, Any]:
    return {"field": "operation", "value": op}


def _cond_any(*ops: str) -> dict[str, Any]:
    return {"field": "operation", "value": list(ops)}


class GoogleDocsNode(BaseNode[GoogleDocsProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleDocsProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gdocs",
            name="Google Docs",
            category="integration",
            description=(
                "Create, read, edit, format, and export Google Docs via OAuth — "
                "text edits, structural inserts (images, tables, breaks), "
                "find/replace, headers/footers, sharing, and exports."
            ),
            icon="google-docs",
            color="#ffffff",
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
                    "default": "get_text",
                    "options": [
                        {"label": "Read Text", "value": "get_text"},
                        {"label": "Read with Structure", "value": "get_with_structure"},
                        {"label": "Append Text", "value": "append_text"},
                        {"label": "Insert Text", "value": "insert_text"},
                        {"label": "Find & Replace", "value": "find_replace"},
                        {"label": "Delete Range", "value": "delete_range"},
                        {"label": "Format Text", "value": "format_text"},
                        {"label": "Set Paragraph Style", "value": "set_paragraph_style"},
                        {"label": "Insert Image", "value": "insert_image"},
                        {"label": "Insert Table", "value": "insert_table"},
                        {"label": "Insert Page Break", "value": "insert_page_break"},
                        {"label": "Set Header", "value": "set_header"},
                        {"label": "Set Footer", "value": "set_footer"},
                        {"label": "Create Document", "value": "create"},
                        {"label": "Copy Document", "value": "copy"},
                        {"label": "Rename Document", "value": "rename"},
                        {"label": "Delete Document", "value": "delete"},
                        {"label": "Share Document", "value": "share"},
                        {"label": "Export Document", "value": "export"},
                    ],
                },
                # document_id — needed for everything except `create`
                {
                    "name": "document_id",
                    "label": "Document",
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
                        "mimeType": DOC_MIME,
                        "placeholder": "Pick a Google Doc…",
                        "searchPlaceholder": "Search your Docs…",
                        "createPlaceholder": "Create new Doc…",
                    },
                    "condition": _cond_any(
                        "get_text",
                        "get_with_structure",
                        "append_text",
                        "insert_text",
                        "find_replace",
                        "delete_range",
                        "format_text",
                        "set_paragraph_style",
                        "insert_image",
                        "insert_table",
                        "insert_page_break",
                        "set_header",
                        "set_footer",
                        "copy",
                        "rename",
                        "delete",
                        "share",
                        "export",
                    ),
                },
                # create
                {
                    "name": "title",
                    "label": "Document title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Quarterly review",
                    "condition": _cond("create"),
                },
                {
                    "name": "initial_content",
                    "label": "Initial content",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 4},
                    "placeholder": "Optional — inserted at the top of the new doc.",
                    "condition": _cond("create"),
                    "mode": "advanced",
                },
                # copy — new title
                {
                    "name": "new_title",
                    "label": "New title",
                    "type": "string",
                    "placeholder": "Copy of …",
                    "description": 'Leave blank to keep Google\'s default "Copy of …".',
                    "condition": _cond_any("copy", "rename"),
                },
                # text-content ops — append / insert / header / footer share `text`
                {
                    "name": "text",
                    "label": "Text",
                    "type": "string",
                    "required": True,
                    "typeOptions": {"multiline": True, "rows": 4},
                    "placeholder": "The text to insert.",
                    "condition": _cond_any("append_text", "insert_text"),
                },
                {
                    "name": "header_text",
                    "label": "Header text",
                    "type": "string",
                    "required": True,
                    "typeOptions": {"multiline": True, "rows": 2},
                    "condition": _cond("set_header"),
                },
                {
                    "name": "footer_text",
                    "label": "Footer text",
                    "type": "string",
                    "required": True,
                    "typeOptions": {"multiline": True, "rows": 2},
                    "condition": _cond("set_footer"),
                },
                # insert_text uses index
                {
                    "name": "index",
                    "label": "Insert at index",
                    "type": "number",
                    "default": 1,
                    "description": "1-based position in the document body.",
                    "condition": _cond_any(
                        "insert_text", "insert_image", "insert_table", "insert_page_break"
                    ),
                },
                # find_replace
                {
                    "name": "find_text",
                    "label": "Find",
                    "type": "string",
                    "required": True,
                    "condition": _cond("find_replace"),
                },
                {
                    "name": "replace_text",
                    "label": "Replace with",
                    "type": "string",
                    "condition": _cond("find_replace"),
                },
                {
                    "name": "match_case",
                    "label": "Match case",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("find_replace"),
                    "mode": "advanced",
                },
                # delete_range / format_text / set_paragraph_style — share start/end
                {
                    "name": "start_index",
                    "label": "Start index",
                    "type": "number",
                    "required": True,
                    "condition": _cond_any("delete_range", "format_text", "set_paragraph_style"),
                },
                {
                    "name": "end_index",
                    "label": "End index",
                    "type": "number",
                    "required": True,
                    "condition": _cond_any("delete_range", "format_text", "set_paragraph_style"),
                },
                # format_text knobs
                {
                    "name": "format_bold",
                    "label": "Bold",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("format_text"),
                },
                {
                    "name": "format_italic",
                    "label": "Italic",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("format_text"),
                },
                {
                    "name": "format_underline",
                    "label": "Underline",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("format_text"),
                },
                {
                    "name": "format_strikethrough",
                    "label": "Strikethrough",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("format_text"),
                    "mode": "advanced",
                },
                {
                    "name": "format_font_family",
                    "label": "Font family",
                    "type": "string",
                    "placeholder": "Arial",
                    "condition": _cond("format_text"),
                    "mode": "advanced",
                },
                {
                    "name": "format_font_size_pt",
                    "label": "Font size (pt)",
                    "type": "number",
                    "placeholder": "11",
                    "condition": _cond("format_text"),
                    "mode": "advanced",
                },
                {
                    "name": "format_text_color",
                    "label": "Text colour",
                    "type": "string",
                    "placeholder": "#111111",
                    "description": "Hex like `#rrggbb`.",
                    "condition": _cond("format_text"),
                },
                {
                    "name": "format_background_color",
                    "label": "Background colour",
                    "type": "string",
                    "placeholder": "#fff3a3",
                    "description": "Hex like `#rrggbb`.",
                    "condition": _cond("format_text"),
                    "mode": "advanced",
                },
                # set_paragraph_style
                {
                    "name": "paragraph_named_style",
                    "label": "Named style",
                    "type": "options",
                    "default": "NORMAL_TEXT",
                    "options": _NAMED_STYLE_OPTIONS,
                    "condition": _cond("set_paragraph_style"),
                },
                {
                    "name": "paragraph_alignment",
                    "label": "Alignment",
                    "type": "options",
                    "default": "START",
                    "options": _ALIGNMENT_OPTIONS,
                    "condition": _cond("set_paragraph_style"),
                },
                {
                    "name": "paragraph_indent_start_pt",
                    "label": "Left indent (pt)",
                    "type": "number",
                    "placeholder": "18",
                    "condition": _cond("set_paragraph_style"),
                    "mode": "advanced",
                },
                # insert_image — media field, optional size
                {
                    "name": "image_content",
                    "label": "Image",
                    "type": "media",
                    "required": True,
                    "typeOptions": {"accept": "image/*"},
                    "description": "URL, upload, or pick from your Library.",
                    "condition": _cond("insert_image"),
                },
                {
                    "name": "image_width_pt",
                    "label": "Width (pt)",
                    "type": "number",
                    "placeholder": "300",
                    "description": "Optional — leave blank to use the image's natural width.",
                    "condition": _cond("insert_image"),
                    "mode": "advanced",
                },
                {
                    "name": "image_height_pt",
                    "label": "Height (pt)",
                    "type": "number",
                    "placeholder": "200",
                    "condition": _cond("insert_image"),
                    "mode": "advanced",
                },
                # insert_table
                {
                    "name": "table_rows",
                    "label": "Rows",
                    "type": "number",
                    "default": 2,
                    "condition": _cond("insert_table"),
                },
                {
                    "name": "table_cols",
                    "label": "Columns",
                    "type": "number",
                    "default": 2,
                    "condition": _cond("insert_table"),
                },
                # share
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
                # export
                {
                    "name": "export_format",
                    "label": "Format",
                    "type": "options",
                    "default": "pdf",
                    "options": [
                        {"label": "PDF", "value": "pdf"},
                        {"label": "Word (.docx)", "value": "docx"},
                        {"label": "Plain text (.txt)", "value": "txt"},
                        {"label": "HTML (zip)", "value": "html"},
                        {"label": "EPUB", "value": "epub"},
                        {"label": "OpenDocument (.odt)", "value": "odt"},
                        {"label": "Rich Text (.rtf)", "value": "rtf"},
                    ],
                    "condition": _cond("export"),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "document_id", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "web_view_link", "type": "string"},
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
                error=f"Google Docs API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleDocsNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── shared helpers ──────────────────────────────────────────────────────


def _require_document_id(node: GoogleDocsNode) -> str | NodeResult:
    doc_id = (node.props.document_id or "").strip()
    if not doc_id:
        return NodeResult(success=False, error="Document is required.")
    return doc_id


async def _doc_batch_update(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    doc_id: str,
    requests: list[dict[str, Any]],
) -> dict[str, Any]:
    """One-shot `batchUpdate` against the Docs API."""
    r = await client.post(
        f"{DOCS_API}/{doc_id}:batchUpdate",
        headers=headers,
        json={"requests": requests},
    )
    r.raise_for_status()
    return r.json()


def _extract_doc_text(document: dict[str, Any]) -> str:
    """Walk `document.body.content` → join every `textRun.content` into a
    flat string. Drops formatting; useful for downstream LLMs / search.
    """
    body = (document or {}).get("body") or {}
    parts: list[str] = []
    for entry in body.get("content") or []:
        para = entry.get("paragraph")
        if not para:
            continue
        for elem in para.get("elements") or []:
            run = elem.get("textRun")
            if run and isinstance(run.get("content"), str):
                parts.append(run["content"])
    return "".join(parts)


async def _fetch_doc_end_index(
    client: httpx.AsyncClient, headers: dict[str, str], doc_id: str
) -> int:
    """End-of-body index for `append_text`. Docs always ends with a
    section break — its `endIndex` is one past the last paragraph; we
    insert one slot earlier so the new text lands inside the body."""
    r = await client.get(f"{DOCS_API}/{doc_id}", headers=headers)
    r.raise_for_status()
    body = (r.json().get("body") or {}).get("content") or []
    if not body:
        return 1
    last = body[-1]
    return int(last.get("endIndex") or 1) - 1


def _color_field(hex_str: str) -> dict[str, Any] | None:
    """Hex → Docs OptionalColor shape, or None if the hex is invalid."""
    rgb = _hex_to_rgb01(hex_str)
    if rgb is None:
        return None
    return {"color": {"rgbColor": rgb}}


def _drive_share_body(node: GoogleDocsNode) -> dict[str, Any]:
    return {
        "type": "user",
        "role": node.props.share_role or "reader",
        "emailAddress": (node.props.share_email or "").strip(),
    }


# ── operation handlers ──────────────────────────────────────────────────


async def _create(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    title = (node.props.title or "").strip()
    if not title:
        return NodeResult(success=False, error="Title is required.")
    r = await client.post(DOCS_API, headers=headers, json={"title": title})
    r.raise_for_status()
    data = r.json()
    doc_id = data.get("documentId")
    # Optionally seed initial content right after create.
    initial = (node.props.initial_content or "").strip()
    if initial and doc_id:
        await _doc_batch_update(
            client,
            headers,
            doc_id,
            [{"insertText": {"location": {"index": 1}, "text": initial}}],
        )
    return NodeResult(
        success=True,
        output_data={
            "document_id": doc_id,
            "title": title,
            "web_view_link": f"https://docs.google.com/document/d/{doc_id}/edit"
            if doc_id
            else None,
        },
    )


async def _get_text(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    r = await client.get(f"{DOCS_API}/{doc_id}", headers=headers)
    r.raise_for_status()
    data = r.json()
    text = _extract_doc_text(data)
    return NodeResult(
        success=True,
        output_data={
            "document_id": doc_id,
            "title": data.get("title") or "",
            "text": text,
            "revision_id": data.get("revisionId"),
        },
    )


async def _get_with_structure(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    r = await client.get(f"{DOCS_API}/{doc_id}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _append_text(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    text = "" if node.props.text is None else str(node.props.text)
    if not text:
        return NodeResult(success=False, error="`text` is required.")
    end = await _fetch_doc_end_index(client, headers, doc_id)
    result = await _doc_batch_update(
        client,
        headers,
        doc_id,
        [{"insertText": {"location": {"index": end}, "text": text}}],
    )
    return NodeResult(success=True, output_data={"document_id": doc_id, "result": result})


async def _insert_text(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    text = "" if node.props.text is None else str(node.props.text)
    if not text:
        return NodeResult(success=False, error="`text` is required.")
    index = node.props.index if node.props.index is not None else 1
    if index < 1:
        index = 1
    result = await _doc_batch_update(
        client,
        headers,
        doc_id,
        [{"insertText": {"location": {"index": index}, "text": text}}],
    )
    return NodeResult(success=True, output_data={"document_id": doc_id, "result": result})


async def _find_replace(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    find = node.props.find_text or ""
    if not find:
        return NodeResult(success=False, error="`find_text` is required.")
    req = {
        "replaceAllText": {
            "containsText": {"text": find, "matchCase": bool(node.props.match_case)},
            "replaceText": node.props.replace_text or "",
        }
    }
    result = await _doc_batch_update(client, headers, doc_id, [req])
    return NodeResult(success=True, output_data=result)


async def _delete_range(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    start = node.props.start_index
    end = node.props.end_index
    if start is None or end is None or end <= start:
        return NodeResult(
            success=False,
            error="`start_index` and `end_index` are required and end must be > start.",
        )
    req = {"deleteContentRange": {"range": {"startIndex": int(start), "endIndex": int(end)}}}
    result = await _doc_batch_update(client, headers, doc_id, [req])
    return NodeResult(success=True, output_data=result)


async def _format_text(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    start = node.props.start_index
    end = node.props.end_index
    if start is None or end is None or end <= start:
        return NodeResult(
            success=False,
            error="`start_index` and `end_index` are required and end must be > start.",
        )

    text_style: dict[str, Any] = {}
    fields: list[str] = []

    if node.props.format_bold:
        text_style["bold"] = True
        fields.append("bold")
    if node.props.format_italic:
        text_style["italic"] = True
        fields.append("italic")
    if node.props.format_underline:
        text_style["underline"] = True
        fields.append("underline")
    if node.props.format_strikethrough:
        text_style["strikethrough"] = True
        fields.append("strikethrough")
    if node.props.format_font_family:
        text_style["weightedFontFamily"] = {"fontFamily": node.props.format_font_family}
        fields.append("weightedFontFamily")
    if node.props.format_font_size_pt:
        text_style["fontSize"] = {
            "magnitude": float(node.props.format_font_size_pt),
            "unit": "PT",
        }
        fields.append("fontSize")
    if node.props.format_text_color:
        cf = _color_field(node.props.format_text_color)
        if cf is None:
            return NodeResult(success=False, error="`format_text_color` must be a `#rrggbb` hex.")
        text_style["foregroundColor"] = cf
        fields.append("foregroundColor")
    if node.props.format_background_color:
        cf = _color_field(node.props.format_background_color)
        if cf is None:
            return NodeResult(
                success=False, error="`format_background_color` must be a `#rrggbb` hex."
            )
        text_style["backgroundColor"] = cf
        fields.append("backgroundColor")

    if not fields:
        return NodeResult(success=False, error="Pick at least one formatting knob.")

    req = {
        "updateTextStyle": {
            "range": {"startIndex": int(start), "endIndex": int(end)},
            "textStyle": text_style,
            "fields": ",".join(fields),
        }
    }
    result = await _doc_batch_update(client, headers, doc_id, [req])
    return NodeResult(success=True, output_data=result)


async def _set_paragraph_style(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    start = node.props.start_index
    end = node.props.end_index
    if start is None or end is None or end <= start:
        return NodeResult(
            success=False,
            error="`start_index` and `end_index` are required and end must be > start.",
        )

    paragraph_style: dict[str, Any] = {}
    fields: list[str] = []

    if node.props.paragraph_named_style:
        paragraph_style["namedStyleType"] = node.props.paragraph_named_style
        fields.append("namedStyleType")
    if node.props.paragraph_alignment:
        paragraph_style["alignment"] = node.props.paragraph_alignment
        fields.append("alignment")
    if node.props.paragraph_indent_start_pt is not None:
        paragraph_style["indentStart"] = {
            "magnitude": float(node.props.paragraph_indent_start_pt),
            "unit": "PT",
        }
        fields.append("indentStart")

    if not fields:
        return NodeResult(success=False, error="Pick at least one paragraph-style knob.")

    req = {
        "updateParagraphStyle": {
            "range": {"startIndex": int(start), "endIndex": int(end)},
            "paragraphStyle": paragraph_style,
            "fields": ",".join(fields),
        }
    }
    result = await _doc_batch_update(client, headers, doc_id, [req])
    return NodeResult(success=True, output_data=result)


async def _insert_image(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    uri = resolve_media_field(node.props.image_content)
    if not uri:
        return NodeResult(
            success=False, error="`image_content` could not be resolved to a fetchable URL."
        )
    index = node.props.index if node.props.index is not None else 1
    if index < 1:
        index = 1

    insert_req: dict[str, Any] = {"insertInlineImage": {"location": {"index": index}, "uri": uri}}
    if node.props.image_width_pt or node.props.image_height_pt:
        size: dict[str, Any] = {}
        if node.props.image_width_pt:
            size["width"] = {
                "magnitude": float(node.props.image_width_pt),
                "unit": "PT",
            }
        if node.props.image_height_pt:
            size["height"] = {
                "magnitude": float(node.props.image_height_pt),
                "unit": "PT",
            }
        insert_req["insertInlineImage"]["objectSize"] = size

    result = await _doc_batch_update(client, headers, doc_id, [insert_req])
    return NodeResult(success=True, output_data=result)


async def _insert_table(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    rows = max(1, int(node.props.table_rows or 2))
    cols = max(1, int(node.props.table_cols or 2))
    index = node.props.index if node.props.index is not None else 1
    if index < 1:
        index = 1
    req = {
        "insertTable": {
            "location": {"index": index},
            "rows": rows,
            "columns": cols,
        }
    }
    result = await _doc_batch_update(client, headers, doc_id, [req])
    return NodeResult(success=True, output_data=result)


async def _insert_page_break(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    index = node.props.index if node.props.index is not None else 1
    if index < 1:
        index = 1
    req = {"insertPageBreak": {"location": {"index": index}}}
    result = await _doc_batch_update(client, headers, doc_id, [req])
    return NodeResult(success=True, output_data=result)


async def _set_header_or_footer(
    node: GoogleDocsNode,
    client: httpx.AsyncClient,
    headers: dict[str, str],
    kind: str,
) -> NodeResult:
    """Shared implementation — Docs returns the new headerId/footerId in
    the batchUpdate reply, then we insert text into its content via a
    second batchUpdate call."""
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    text = node.props.header_text if kind == "HEADER" else node.props.footer_text
    body_text = "" if text is None else str(text)
    if not body_text:
        return NodeResult(
            success=False,
            error=f"`{'header' if kind == 'HEADER' else 'footer'}_text` is required.",
        )
    create_req = (
        {"createHeader": {"type": "DEFAULT"}}
        if kind == "HEADER"
        else {"createFooter": {"type": "DEFAULT"}}
    )
    first = await _doc_batch_update(client, headers, doc_id, [create_req])
    reply_key = "createHeader" if kind == "HEADER" else "createFooter"
    id_key = "headerId" if kind == "HEADER" else "footerId"
    container_id = None
    for reply in first.get("replies") or []:
        sub = (reply or {}).get(reply_key) or {}
        if sub.get(id_key):
            container_id = sub[id_key]
            break
    if not container_id:
        return NodeResult(
            success=False,
            error=f"Docs did not return a {kind.lower()}Id from createHeader/createFooter.",
        )

    seg_key = "headerId" if kind == "HEADER" else "footerId"
    insert_req = {
        "insertText": {
            "location": {"segmentId": container_id, "index": 0},
            "text": body_text,
        }
    }
    second = await _doc_batch_update(client, headers, doc_id, [insert_req])
    return NodeResult(
        success=True,
        output_data={
            "document_id": doc_id,
            seg_key: container_id,
            "create_result": first,
            "insert_result": second,
        },
    )


async def _set_header(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    return await _set_header_or_footer(node, client, headers, "HEADER")


async def _set_footer(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    return await _set_header_or_footer(node, client, headers, "FOOTER")


# ── Drive-backed ops (share / copy / rename / delete / export) ──────────


async def _copy(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    body: dict[str, Any] = {}
    if node.props.new_title:
        body["name"] = node.props.new_title
    r = await client.post(
        f"{DRIVE_API}/files/{doc_id}/copy",
        headers=headers,
        json=body,
        params={"supportsAllDrives": "true"},
    )
    r.raise_for_status()
    data = r.json()
    new_id = data.get("id")
    return NodeResult(
        success=True,
        output_data={
            "document_id": new_id,
            "title": data.get("name"),
            "web_view_link": f"https://docs.google.com/document/d/{new_id}/edit"
            if new_id
            else None,
        },
    )


async def _rename(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    new_title = (node.props.new_title or "").strip()
    if not new_title:
        return NodeResult(success=False, error="`new_title` is required.")
    r = await client.patch(
        f"{DRIVE_API}/files/{doc_id}",
        headers=headers,
        json={"name": new_title},
        params={"supportsAllDrives": "true"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _delete(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    # Move to trash — keeps the user's "Restore from trash" affordance.
    r = await client.patch(
        f"{DRIVE_API}/files/{doc_id}",
        headers=headers,
        json={"trashed": True},
        params={"supportsAllDrives": "true"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data={"document_id": doc_id, "trashed": True})


async def _share(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    email = (node.props.share_email or "").strip()
    if not email:
        return NodeResult(success=False, error="`share_email` is required.")
    r = await client.post(
        f"{DRIVE_API}/files/{doc_id}/permissions",
        headers=headers,
        json=_drive_share_body(node),
        params={
            "sendNotificationEmail": ("true" if node.props.share_send_notification else "false"),
            "supportsAllDrives": "true",
        },
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _export(
    node: GoogleDocsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    import base64

    doc_id = _require_document_id(node)
    if isinstance(doc_id, NodeResult):
        return doc_id
    fmt = (node.props.export_format or "pdf").lower()
    mime = _EXPORT_MIME.get(fmt)
    if not mime:
        return NodeResult(success=False, error=f"Unsupported export format: {fmt}")
    r = await client.get(
        f"{DRIVE_API}/files/{doc_id}/export",
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


_HANDLERS: dict[str, Any] = {
    "create": _create,
    "get_text": _get_text,
    "get_with_structure": _get_with_structure,
    "append_text": _append_text,
    "insert_text": _insert_text,
    "find_replace": _find_replace,
    "delete_range": _delete_range,
    "format_text": _format_text,
    "set_paragraph_style": _set_paragraph_style,
    "insert_image": _insert_image,
    "insert_table": _insert_table,
    "insert_page_break": _insert_page_break,
    "set_header": _set_header,
    "set_footer": _set_footer,
    "copy": _copy,
    "rename": _rename,
    "delete": _delete,
    "share": _share,
    "export": _export,
}
