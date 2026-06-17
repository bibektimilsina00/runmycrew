"""Google Slides action node — one node, 24 operations.

Presentation CRUD
  - `create` / `get` / `get_text`
  - `rename` / `copy` / `delete` / `share`
  - `export` (PDF / PPTX / SVG / TXT / ODP / PNG-per-slide)
  - `get_thumbnail`

Slide ops
  - `add_slide` (with layout enum)
  - `duplicate_slide`
  - `delete_slide`
  - `reorder_slide`
  - `set_speaker_notes`
  - `set_slide_background` (colour or image)

Text ops
  - `replace_all_text` (deck-wide find/replace)
  - `format_text` (range: bold / italic / underline / font / size /
                   colour / bg colour)
  - `set_paragraph_style` (alignment / indent / spacing)

Insert ops
  - `insert_text_box` (x/y/width/height + initial text)
  - `insert_image` (media field — URL/Upload/Library)
  - `insert_table` (rows × cols + position)
  - `insert_shape` (RECTANGLE / ELLIPSE / TRIANGLE / ARROW / STAR + position)
  - `replace_image` (swap an image element's content)
  - `delete_element` (any page-element object id)

OAuth scope: `presentations` + `drive.file` (in GoogleOAuthProvider).
Mime: `application/vnd.google-apps.presentation`.

`presentation_id` is wired through the generic `google-file` picker —
the same renderer Docs / Sheets / Forms use, with the Slides mime
configured.
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
from apps.api.app.node_system.nodes.google_sheets.google_sheets import _hex_to_rgb01

logger = get_logger(__name__)

SLIDES_API = "https://slides.googleapis.com/v1/presentations"
DRIVE_API = "https://www.googleapis.com/drive/v3"
SLIDES_MIME = "application/vnd.google-apps.presentation"


# Drive exports Slides into the widely-used document formats below.
# PNG / SVG / JPEG export render only the first slide; for
# per-slide PNG users go through `get_thumbnail`.
_EXPORT_MIME: dict[str, str] = {
    "pdf": "application/pdf",
    "pptx": ("application/vnd.openxmlformats-officedocument.presentationml.presentation"),
    "txt": "text/plain",
    "odp": "application/vnd.oasis.opendocument.presentation",
    "svg": "image/svg+xml",
    "png": "image/png",
    "jpeg": "image/jpeg",
}


# Predefined slide layouts the Slides API exposes. Keep the dropdown
# focused on the canonical set instead of every internal variant.
_LAYOUT_OPTIONS: list[dict[str, str]] = [
    {"label": "Blank", "value": "BLANK"},
    {"label": "Title", "value": "TITLE"},
    {"label": "Title & body", "value": "TITLE_AND_BODY"},
    {"label": "Section header", "value": "SECTION_HEADER"},
    {"label": "Title, two columns", "value": "TITLE_AND_TWO_COLUMNS"},
    {"label": "Title only", "value": "TITLE_ONLY"},
    {"label": "Big number", "value": "BIG_NUMBER"},
    {"label": "Caption only", "value": "CAPTION_ONLY"},
]


# Shapes the `insert_shape` op surfaces. The Slides API supports far
# more (≈40); these are the everyday ones.
_SHAPE_OPTIONS: list[dict[str, str]] = [
    {"label": "Rectangle", "value": "RECTANGLE"},
    {"label": "Rounded rectangle", "value": "ROUND_RECTANGLE"},
    {"label": "Ellipse", "value": "ELLIPSE"},
    {"label": "Triangle", "value": "TRIANGLE"},
    {"label": "Right triangle", "value": "RIGHT_TRIANGLE"},
    {"label": "Diamond", "value": "DIAMOND"},
    {"label": "Pentagon", "value": "PENTAGON"},
    {"label": "Hexagon", "value": "HEXAGON"},
    {"label": "Arrow right", "value": "RIGHT_ARROW"},
    {"label": "Star (5-point)", "value": "STAR_5"},
    {"label": "Cloud", "value": "CLOUD"},
]


_ALIGNMENT_OPTIONS: list[dict[str, str]] = [
    {"label": "Left / Start", "value": "START"},
    {"label": "Center", "value": "CENTER"},
    {"label": "Right / End", "value": "END"},
    {"label": "Justify", "value": "JUSTIFIED"},
]


_INSERT_POSITION_OPTIONS: list[dict[str, str]] = [
    {"label": "Append at end", "value": "end"},
    {"label": "Insert at index (specify below)", "value": "index"},
]


class GoogleSlidesProperties(BaseModel):
    credential: str | None = None
    operation: str = "get"

    presentation_id: str | None = None

    # create / rename
    title: str | None = None
    initial_content: str | None = None  # add a title-slide text on create
    new_title: str | None = None

    # slide identity
    slide_id: str | None = None  # objectId
    element_id: str | None = None  # any pageElement

    # add_slide / duplicate_slide / reorder_slide
    layout: str = "BLANK"
    insert_position: str = "end"  # "end" or "index"
    slide_index: int | None = None  # zero-based when insert_position == "index"

    # set_speaker_notes
    speaker_notes: Any = None

    # set_slide_background — choose colour OR image URL
    background_color: str | None = None  # #rrggbb
    background_image_url: str | None = None

    # replace_all_text
    find_text: str | None = None
    replace_text: str | None = None
    match_case: bool = False

    # format_text / set_paragraph_style — range is text under an
    # element. We accept whole-element by default; advanced users can
    # pass `start_index` + `end_index` to scope.
    start_index: int | None = None
    end_index: int | None = None

    format_bold: bool = False
    format_italic: bool = False
    format_underline: bool = False
    format_strikethrough: bool = False
    format_font_family: str | None = None
    format_font_size_pt: float | None = None
    format_text_color: str | None = None
    format_background_color: str | None = None

    paragraph_alignment: str | None = None
    paragraph_indent_start_pt: float | None = None
    paragraph_line_spacing_percent: float | None = None  # 100 = single

    # insert_text_box / insert_image / insert_table / insert_shape /
    # insert_video — placement (in EMU / PT — we use PT for the user
    # interface and convert).
    position_x_pt: float = 50
    position_y_pt: float = 50
    width_pt: float = 400
    height_pt: float = 200

    text_content: Any = None  # initial text inside a text box

    # insert_image / replace_image
    media: Any = None

    # insert_table
    table_rows: int = 2
    table_cols: int = 2

    # insert_shape
    shape_type: str = "RECTANGLE"

    # share
    share_email: str | None = None
    share_role: str = "reader"
    share_send_notification: bool = False

    # export
    export_format: str = "pdf"

    # get_thumbnail
    thumbnail_size: str = "MEDIUM"  # SMALL / MEDIUM / LARGE

    @field_validator(
        "presentation_id",
        "slide_id",
        "element_id",
        mode="before",
    )
    @classmethod
    def _coerce_resource_id(cls, value: Any) -> str | None:
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


_PRES_OPS = (
    "get",
    "get_text",
    "rename",
    "copy",
    "delete",
    "share",
    "export",
    "get_thumbnail",
    "add_slide",
    "duplicate_slide",
    "delete_slide",
    "reorder_slide",
    "set_speaker_notes",
    "set_slide_background",
    "replace_all_text",
    "format_text",
    "set_paragraph_style",
    "insert_text_box",
    "insert_image",
    "insert_table",
    "insert_shape",
    "replace_image",
    "delete_element",
)
_NEEDS_SLIDE_ID = (
    "duplicate_slide",
    "delete_slide",
    "reorder_slide",
    "set_speaker_notes",
    "set_slide_background",
    "insert_text_box",
    "insert_image",
    "insert_table",
    "insert_shape",
    "get_thumbnail",
)
_NEEDS_ELEMENT_ID = (
    "format_text",
    "set_paragraph_style",
    "replace_image",
    "delete_element",
)
_HAS_POSITION = ("insert_text_box", "insert_image", "insert_table", "insert_shape")


class GoogleSlidesNode(BaseNode[GoogleSlidesProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleSlidesProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gslides",
            name="Google Slides",
            category="integration",
            description=(
                "Create, edit, and export Google Slides — slide layouts, "
                "text edits, find/replace, images, tables, shapes, speaker "
                "notes, backgrounds, sharing, and exports."
            ),
            icon="si:SiGoogleslides",
            color="#f4b400",
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
                    "default": "get",
                    "options": [
                        {"label": "Get Presentation", "value": "get"},
                        {"label": "Get All Text", "value": "get_text"},
                        {"label": "Create Presentation", "value": "create"},
                        {"label": "Rename Presentation", "value": "rename"},
                        {"label": "Copy Presentation", "value": "copy"},
                        {"label": "Delete Presentation", "value": "delete"},
                        {"label": "Share Presentation", "value": "share"},
                        {"label": "Export Presentation", "value": "export"},
                        {"label": "Get Slide Thumbnail", "value": "get_thumbnail"},
                        {"label": "Add Slide", "value": "add_slide"},
                        {"label": "Duplicate Slide", "value": "duplicate_slide"},
                        {"label": "Delete Slide", "value": "delete_slide"},
                        {"label": "Reorder Slide", "value": "reorder_slide"},
                        {"label": "Set Speaker Notes", "value": "set_speaker_notes"},
                        {"label": "Set Slide Background", "value": "set_slide_background"},
                        {"label": "Find & Replace (deck-wide)", "value": "replace_all_text"},
                        {"label": "Format Text", "value": "format_text"},
                        {"label": "Set Paragraph Style", "value": "set_paragraph_style"},
                        {"label": "Insert Text Box", "value": "insert_text_box"},
                        {"label": "Insert Image", "value": "insert_image"},
                        {"label": "Insert Table", "value": "insert_table"},
                        {"label": "Insert Shape", "value": "insert_shape"},
                        {"label": "Replace Image", "value": "replace_image"},
                        {"label": "Delete Element", "value": "delete_element"},
                    ],
                },
                # presentation_id — needed for everything except `create`
                {
                    "name": "presentation_id",
                    "label": "Presentation",
                    "type": "google-file",
                    "required": True,
                    "typeOptions": {
                        "mimeType": SLIDES_MIME,
                        "placeholder": "Pick a slide deck…",
                        "searchPlaceholder": "Search your decks…",
                        "createPlaceholder": "Create new deck…",
                    },
                    "condition": _cond_any(*_PRES_OPS),
                },
                # create
                {
                    "name": "title",
                    "label": "Presentation title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Q1 launch deck",
                    "condition": _cond("create"),
                },
                {
                    "name": "initial_content",
                    "label": "Title-slide subtitle",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 2},
                    "placeholder": "Optional — text inserted into the title slide's subtitle.",
                    "condition": _cond("create"),
                    "mode": "advanced",
                },
                # rename / copy
                {
                    "name": "new_title",
                    "label": "New title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Renamed deck",
                    "condition": _cond("rename"),
                },
                {
                    "name": "new_title",
                    "label": "New title",
                    "type": "string",
                    "placeholder": 'Leave blank to keep Google\'s default "Copy of …".',
                    "condition": _cond("copy"),
                },
                # slide_id picker (free-text — slide IDs come from triggers
                # or get_text output)
                {
                    "name": "slide_id",
                    "label": "Slide ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $node.get_text.slides[0].slide_id }}",
                    "description": "Object ID of the slide. Run `Get All Text` first to discover IDs.",
                    "condition": _cond_any(*_NEEDS_SLIDE_ID),
                },
                # element_id (also free-text)
                {
                    "name": "element_id",
                    "label": "Element ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $node.get_text.slides[0].elements[0].id }}",
                    "description": "Object ID of the page element (text box, image, shape).",
                    "condition": _cond_any(*_NEEDS_ELEMENT_ID),
                },
                # add_slide
                {
                    "name": "layout",
                    "label": "Layout",
                    "type": "options",
                    "default": "BLANK",
                    "options": _LAYOUT_OPTIONS,
                    "condition": _cond("add_slide"),
                },
                {
                    "name": "insert_position",
                    "label": "Insert at",
                    "type": "options",
                    "default": "end",
                    "options": _INSERT_POSITION_OPTIONS,
                    "condition": _cond_any("add_slide", "duplicate_slide", "reorder_slide"),
                },
                {
                    "name": "slide_index",
                    "label": "Index (0-based)",
                    "type": "number",
                    "placeholder": "2",
                    "description": "Position in the slide list.",
                    "condition": {
                        "all": [
                            {
                                "field": "operation",
                                "value": ["add_slide", "duplicate_slide", "reorder_slide"],
                            },
                            {"field": "insert_position", "value": "index"},
                        ]
                    },
                },
                # set_speaker_notes
                {
                    "name": "speaker_notes",
                    "label": "Speaker notes",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 4},
                    "required": True,
                    "condition": _cond("set_speaker_notes"),
                },
                # set_slide_background — colour or image
                {
                    "name": "background_color",
                    "label": "Background colour",
                    "type": "string",
                    "placeholder": "#1a73e8",
                    "description": "Hex `#rrggbb`. Leave blank to use the image instead.",
                    "condition": _cond("set_slide_background"),
                },
                {
                    "name": "background_image_url",
                    "label": "Background image URL",
                    "type": "string",
                    "placeholder": "https://… (jpg/png/gif under 25MB)",
                    "condition": _cond("set_slide_background"),
                    "mode": "advanced",
                },
                # replace_all_text
                {
                    "name": "find_text",
                    "label": "Find",
                    "type": "string",
                    "required": True,
                    "condition": _cond("replace_all_text"),
                },
                {
                    "name": "replace_text",
                    "label": "Replace with",
                    "type": "string",
                    "condition": _cond("replace_all_text"),
                },
                {
                    "name": "match_case",
                    "label": "Match case",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("replace_all_text"),
                    "mode": "advanced",
                },
                # format_text — range (optional; whole-element by default)
                {
                    "name": "start_index",
                    "label": "Range start (chars)",
                    "type": "number",
                    "description": "Optional. Leave blank to format every run on the element.",
                    "condition": _cond_any("format_text", "set_paragraph_style"),
                    "mode": "advanced",
                },
                {
                    "name": "end_index",
                    "label": "Range end (chars)",
                    "type": "number",
                    "description": "Optional. Required if you set a start.",
                    "condition": _cond_any("format_text", "set_paragraph_style"),
                    "mode": "advanced",
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
                    "placeholder": "Roboto",
                    "condition": _cond("format_text"),
                    "mode": "advanced",
                },
                {
                    "name": "format_font_size_pt",
                    "label": "Font size (pt)",
                    "type": "number",
                    "placeholder": "18",
                    "condition": _cond("format_text"),
                    "mode": "advanced",
                },
                {
                    "name": "format_text_color",
                    "label": "Text colour",
                    "type": "string",
                    "placeholder": "#111111",
                    "condition": _cond("format_text"),
                },
                {
                    "name": "format_background_color",
                    "label": "Background colour",
                    "type": "string",
                    "placeholder": "#fff3a3",
                    "condition": _cond("format_text"),
                    "mode": "advanced",
                },
                # set_paragraph_style
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
                {
                    "name": "paragraph_line_spacing_percent",
                    "label": "Line spacing %",
                    "type": "number",
                    "placeholder": "100",
                    "description": "100 = single, 150 = 1.5×.",
                    "condition": _cond("set_paragraph_style"),
                    "mode": "advanced",
                },
                # insert_text_box — initial text
                {
                    "name": "text_content",
                    "label": "Text",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 2},
                    "placeholder": "Initial text inside the box (optional)",
                    "condition": _cond("insert_text_box"),
                },
                # insert_image / replace_image — media field
                {
                    "name": "media",
                    "label": "Image",
                    "type": "media",
                    "required": True,
                    "typeOptions": {"accept": "image/*"},
                    "description": "URL, upload, or pick from Library.",
                    "condition": _cond_any("insert_image", "replace_image", "set_slide_background"),
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
                # insert_shape
                {
                    "name": "shape_type",
                    "label": "Shape",
                    "type": "options",
                    "default": "RECTANGLE",
                    "options": _SHAPE_OPTIONS,
                    "condition": _cond("insert_shape"),
                },
                # position + size for placed elements
                {
                    "name": "position_x_pt",
                    "label": "X (pt)",
                    "type": "number",
                    "default": 50,
                    "condition": _cond_any(*_HAS_POSITION),
                    "mode": "advanced",
                },
                {
                    "name": "position_y_pt",
                    "label": "Y (pt)",
                    "type": "number",
                    "default": 50,
                    "condition": _cond_any(*_HAS_POSITION),
                    "mode": "advanced",
                },
                {
                    "name": "width_pt",
                    "label": "Width (pt)",
                    "type": "number",
                    "default": 400,
                    "condition": _cond_any(*_HAS_POSITION),
                    "mode": "advanced",
                },
                {
                    "name": "height_pt",
                    "label": "Height (pt)",
                    "type": "number",
                    "default": 200,
                    "condition": _cond_any(*_HAS_POSITION),
                    "mode": "advanced",
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
                        {"label": "PowerPoint (.pptx)", "value": "pptx"},
                        {"label": "Plain text (.txt)", "value": "txt"},
                        {"label": "OpenDocument (.odp)", "value": "odp"},
                        {"label": "SVG (first slide)", "value": "svg"},
                        {"label": "PNG (first slide)", "value": "png"},
                        {"label": "JPEG (first slide)", "value": "jpeg"},
                    ],
                    "condition": _cond("export"),
                },
                # get_thumbnail
                {
                    "name": "thumbnail_size",
                    "label": "Thumbnail size",
                    "type": "options",
                    "default": "MEDIUM",
                    "options": [
                        {"label": "Small (200px)", "value": "SMALL"},
                        {"label": "Medium (800px)", "value": "MEDIUM"},
                        {"label": "Large (1600px)", "value": "LARGE"},
                    ],
                    "condition": _cond("get_thumbnail"),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "presentation_id", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "slide_id", "type": "string"},
                {"label": "element_id", "type": "string"},
                {"label": "url", "type": "string"},
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
            async with httpx.AsyncClient(timeout=60) as client:
                return await handler(self, client, headers)
        except httpx.HTTPStatusError as exc:
            return NodeResult(
                success=False,
                error=f"Google Slides API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleSlidesNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── shared helpers ──────────────────────────────────────────────────────


def _require_presentation(node: GoogleSlidesNode) -> str | NodeResult:
    pid = (node.props.presentation_id or "").strip()
    if not pid:
        return NodeResult(success=False, error="Presentation is required.")
    return pid


def _require_slide(node: GoogleSlidesNode) -> str | NodeResult:
    sid = (node.props.slide_id or "").strip()
    if not sid:
        return NodeResult(success=False, error="Slide ID is required.")
    return sid


def _require_element(node: GoogleSlidesNode) -> str | NodeResult:
    eid = (node.props.element_id or "").strip()
    if not eid:
        return NodeResult(success=False, error="Element ID is required.")
    return eid


async def _slides_batch_update(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    presentation_id: str,
    requests: list[dict[str, Any]],
) -> dict[str, Any]:
    r = await client.post(
        f"{SLIDES_API}/{presentation_id}:batchUpdate",
        headers=headers,
        json={"requests": requests},
    )
    r.raise_for_status()
    return r.json()


def _color_field(hex_str: str) -> dict[str, Any] | None:
    """Hex → Slides OpaqueColor shape, or None if invalid."""
    rgb = _hex_to_rgb01(hex_str)
    if rgb is None:
        return None
    return {"opaqueColor": {"rgbColor": rgb}}


def _placement(node: GoogleSlidesNode, slide_id: str) -> dict[str, Any]:
    """Build the `elementProperties` (size + transform) block all
    create_* requests share."""
    # Slides API takes EMU for transforms; we expose PT in the UI.
    # 1 PT == 12,700 EMU.
    return {
        "pageObjectId": slide_id,
        "size": {
            "width": {"magnitude": float(node.props.width_pt), "unit": "PT"},
            "height": {"magnitude": float(node.props.height_pt), "unit": "PT"},
        },
        "transform": {
            "scaleX": 1,
            "scaleY": 1,
            "translateX": float(node.props.position_x_pt),
            "translateY": float(node.props.position_y_pt),
            "unit": "PT",
        },
    }


def _find_text_placeholder(slide: dict[str, Any], *, preferred: tuple[str, ...]) -> str | None:
    """Walk a slide's pageElements → first placeholder shape whose
    `placeholder.type` matches one of the preferred kinds. Used after
    `create` to seed text into the title-slide subtitle without
    knowing the layout-generated object id ahead of time.

    Returns None when the slide has no placeholders (e.g. BLANK layout)
    so the caller can skip the seed step silently."""
    preferred_set = {p.upper() for p in preferred}
    matched: dict[str, str] = {}
    for element in slide.get("pageElements") or []:
        eid = element.get("objectId")
        if not isinstance(eid, str):
            continue
        ptype = ((element.get("shape") or {}).get("placeholder") or {}).get("type") or ""
        if not ptype:
            continue
        ptype_upper = ptype.upper()
        if ptype_upper in preferred_set and ptype_upper not in matched:
            matched[ptype_upper] = eid
    for kind in preferred:
        if kind.upper() in matched:
            return matched[kind.upper()]
    return None


def _extract_slide_text(presentation: dict[str, Any]) -> list[dict[str, Any]]:
    """Walk slides → per-slide flattened text + element list. Used by
    `get_text` (returns the structure downstream nodes need to drive
    text edits)."""
    out: list[dict[str, Any]] = []
    for slide in (presentation or {}).get("slides") or []:
        slide_id = slide.get("objectId") or ""
        elements: list[dict[str, Any]] = []
        text_chunks: list[str] = []
        for element in slide.get("pageElements") or []:
            eid = element.get("objectId") or ""
            element_text = _extract_element_text(element)
            elements.append(
                {
                    "id": eid,
                    "kind": _element_kind(element),
                    "text": element_text,
                }
            )
            if element_text:
                text_chunks.append(element_text)
        out.append(
            {
                "slide_id": slide_id,
                "text": "\n".join(text_chunks),
                "elements": elements,
            }
        )
    return out


def _element_kind(element: dict[str, Any]) -> str:
    for kind in ("shape", "image", "video", "line", "table", "wordArt"):
        if kind in element:
            return kind
    return "unknown"


def _extract_element_text(element: dict[str, Any]) -> str:
    text = (element.get("shape") or {}).get("text") or {}
    if not text:
        return ""
    parts: list[str] = []
    for tx in text.get("textElements") or []:
        run = tx.get("textRun") or {}
        if isinstance(run.get("content"), str):
            parts.append(run["content"])
    return "".join(parts)


# ── handlers — presentation CRUD ────────────────────────────────────────


async def _create(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    title = (node.props.title or "").strip()
    if not title:
        return NodeResult(success=False, error="Title is required.")
    r = await client.post(SLIDES_API, headers=headers, json={"title": title})
    r.raise_for_status()
    data = r.json()
    pres_id = data.get("presentationId")
    # If the user wanted a subtitle seeded on the title slide, drop the
    # text into the first slide's subtitle placeholder via a follow-up
    # batchUpdate. The slide page itself (objectId "p") does NOT accept
    # text — we have to target a placeholder shape inside it.
    if node.props.initial_content and pres_id:
        slides = data.get("slides") or []
        if slides:
            placeholder_id = _find_text_placeholder(
                slides[0],
                preferred=("SUBTITLE", "BODY", "CENTERED_TITLE", "TITLE"),
            )
            if placeholder_id:
                await _slides_batch_update(
                    client,
                    headers,
                    pres_id,
                    [
                        {
                            "insertText": {
                                "objectId": placeholder_id,
                                "text": node.props.initial_content,
                            }
                        }
                    ],
                )
    return NodeResult(
        success=True,
        output_data={
            "presentation_id": pres_id,
            "title": title,
            "url": (f"https://docs.google.com/presentation/d/{pres_id}/edit" if pres_id else None),
        },
    )


async def _get(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    r = await client.get(f"{SLIDES_API}/{pid}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _get_text(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    r = await client.get(f"{SLIDES_API}/{pid}", headers=headers)
    r.raise_for_status()
    data = r.json()
    slides = _extract_slide_text(data)
    return NodeResult(
        success=True,
        output_data={
            "presentation_id": pid,
            "title": data.get("title") or "",
            "slide_count": len(slides),
            "slides": slides,
        },
    )


async def _rename(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    new_title = (node.props.new_title or "").strip()
    if not new_title:
        return NodeResult(success=False, error="`new_title` is required.")
    r = await client.patch(
        f"{DRIVE_API}/files/{pid}",
        headers=headers,
        json={"name": new_title},
        params={"supportsAllDrives": "true"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _copy(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    body: dict[str, Any] = {}
    if node.props.new_title:
        body["name"] = node.props.new_title
    r = await client.post(
        f"{DRIVE_API}/files/{pid}/copy",
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
            "presentation_id": new_id,
            "title": data.get("name"),
            "url": (f"https://docs.google.com/presentation/d/{new_id}/edit" if new_id else None),
        },
    )


async def _delete(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    r = await client.patch(
        f"{DRIVE_API}/files/{pid}",
        headers=headers,
        json={"trashed": True},
        params={"supportsAllDrives": "true"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data={"presentation_id": pid, "trashed": True})


async def _share(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    email = (node.props.share_email or "").strip()
    if not email:
        return NodeResult(success=False, error="`share_email` is required.")
    r = await client.post(
        f"{DRIVE_API}/files/{pid}/permissions",
        headers=headers,
        json={
            "type": "user",
            "role": node.props.share_role or "reader",
            "emailAddress": email,
        },
        params={
            "sendNotificationEmail": ("true" if node.props.share_send_notification else "false"),
            "supportsAllDrives": "true",
        },
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _export(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    import base64

    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    fmt = (node.props.export_format or "pdf").lower()
    mime = _EXPORT_MIME.get(fmt)
    if not mime:
        return NodeResult(success=False, error=f"Unsupported export format: {fmt}")
    r = await client.get(
        f"{DRIVE_API}/files/{pid}/export",
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


async def _get_thumbnail(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid
    r = await client.get(
        f"{SLIDES_API}/{pid}/pages/{sid}/thumbnail",
        headers=headers,
        params={
            "thumbnailProperties.mimeType": "PNG",
            "thumbnailProperties.thumbnailSize": node.props.thumbnail_size or "MEDIUM",
        },
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


# ── handlers — slide ops ────────────────────────────────────────────────


def _slide_insertion_index(node: GoogleSlidesNode) -> int | None:
    if (node.props.insert_position or "end") == "end":
        return None
    return int(node.props.slide_index or 0)


async def _add_slide(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    request: dict[str, Any] = {
        "createSlide": {"slideLayoutReference": {"predefinedLayout": node.props.layout or "BLANK"}}
    }
    insert_at = _slide_insertion_index(node)
    if insert_at is not None:
        request["createSlide"]["insertionIndex"] = insert_at
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(success=True, output_data=result)


async def _duplicate_slide(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid
    request: dict[str, Any] = {"duplicateObject": {"objectId": sid}}
    result = await _slides_batch_update(client, headers, pid, [request])
    # The duplicate lands right after the source by default; an explicit
    # index requires a follow-up updateSlidesPosition.
    new_id: str | None = None
    for reply in result.get("replies") or []:
        dup = reply.get("duplicateObject") or {}
        if dup.get("objectId"):
            new_id = dup["objectId"]
            break
    insert_at = _slide_insertion_index(node)
    if new_id and insert_at is not None:
        await _slides_batch_update(
            client,
            headers,
            pid,
            [
                {
                    "updateSlidesPosition": {
                        "slideObjectIds": [new_id],
                        "insertionIndex": insert_at,
                    }
                }
            ],
        )
    return NodeResult(success=True, output_data={**result, "new_slide_id": new_id})


async def _delete_slide(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid
    result = await _slides_batch_update(client, headers, pid, [{"deleteObject": {"objectId": sid}}])
    return NodeResult(success=True, output_data=result)


async def _reorder_slide(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid
    insert_at = _slide_insertion_index(node)
    if insert_at is None:
        return NodeResult(
            success=False,
            error='Set `Insert at` to "Insert at index" and provide an index.',
        )
    result = await _slides_batch_update(
        client,
        headers,
        pid,
        [
            {
                "updateSlidesPosition": {
                    "slideObjectIds": [sid],
                    "insertionIndex": int(insert_at),
                }
            }
        ],
    )
    return NodeResult(success=True, output_data=result)


async def _set_speaker_notes(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid
    notes = "" if node.props.speaker_notes is None else str(node.props.speaker_notes)
    # First fetch the slide so we can grab the notes page's speaker
    # notes objectId — the Slides API requires inserting text into
    # that specific shape, not the slide itself.
    pres = await client.get(f"{SLIDES_API}/{pid}", headers=headers)
    pres.raise_for_status()
    notes_object_id: str | None = None
    for slide in pres.json().get("slides") or []:
        if slide.get("objectId") != sid:
            continue
        notes_object_id = (
            ((slide.get("slideProperties") or {}).get("notesPage") or {})
            .get("notesProperties", {})
            .get("speakerNotesObjectId")
        )
        if not notes_object_id:
            # The speaker notes shape lives under the notes page elements.
            notes_page = (slide.get("slideProperties") or {}).get("notesPage") or {}
            for element in notes_page.get("pageElements") or []:
                shape = element.get("shape") or {}
                if shape.get("placeholder", {}).get("type") == "BODY":
                    notes_object_id = element.get("objectId")
                    break
        break
    if not notes_object_id:
        return NodeResult(
            success=False, error=f"Could not locate the speaker notes shape on slide {sid}."
        )
    requests: list[dict[str, Any]] = [
        {
            "deleteText": {
                "objectId": notes_object_id,
                "textRange": {"type": "ALL"},
            }
        },
        {
            "insertText": {
                "objectId": notes_object_id,
                "text": notes,
            }
        },
    ]
    result = await _slides_batch_update(client, headers, pid, requests)
    return NodeResult(success=True, output_data=result)


async def _set_slide_background(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid

    from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

    bg: dict[str, Any] = {}
    if node.props.background_color:
        cf = _color_field(node.props.background_color)
        if cf is None:
            return NodeResult(success=False, error="`background_color` must be `#rrggbb`.")
        bg["solidFill"] = {"color": cf}
    media_url = (
        resolve_media_field(node.props.media) or (node.props.background_image_url or "").strip()
    )
    if media_url:
        bg["stretchedPictureFill"] = {"contentUrl": media_url}

    if not bg:
        return NodeResult(
            success=False,
            error="Provide either `background_color` or `background_image_url` / `media`.",
        )

    request = {
        "updatePageProperties": {
            "objectId": sid,
            "pageProperties": {"pageBackgroundFill": bg},
            "fields": "pageBackgroundFill",
        }
    }
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(success=True, output_data=result)


# ── handlers — text ops ────────────────────────────────────────────────


async def _replace_all_text(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    find = node.props.find_text or ""
    if not find:
        return NodeResult(success=False, error="`find_text` is required.")
    request = {
        "replaceAllText": {
            "containsText": {"text": find, "matchCase": bool(node.props.match_case)},
            "replaceText": node.props.replace_text or "",
        }
    }
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(success=True, output_data=result)


def _text_range(node: GoogleSlidesNode) -> dict[str, Any]:
    """Pick the textRange that update*TextStyle requests expect."""
    if node.props.start_index is not None and node.props.end_index is not None:
        return {
            "type": "FIXED_RANGE",
            "startIndex": int(node.props.start_index),
            "endIndex": int(node.props.end_index),
        }
    return {"type": "ALL"}


async def _format_text(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    eid = _require_element(node)
    if isinstance(eid, NodeResult):
        return eid

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

    request = {
        "updateTextStyle": {
            "objectId": eid,
            "textRange": _text_range(node),
            "style": text_style,
            "fields": ",".join(fields),
        }
    }
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(success=True, output_data=result)


async def _set_paragraph_style(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    eid = _require_element(node)
    if isinstance(eid, NodeResult):
        return eid

    paragraph_style: dict[str, Any] = {}
    fields: list[str] = []

    if node.props.paragraph_alignment:
        paragraph_style["alignment"] = node.props.paragraph_alignment
        fields.append("alignment")
    if node.props.paragraph_indent_start_pt is not None:
        paragraph_style["indentStart"] = {
            "magnitude": float(node.props.paragraph_indent_start_pt),
            "unit": "PT",
        }
        fields.append("indentStart")
    if node.props.paragraph_line_spacing_percent is not None:
        paragraph_style["lineSpacing"] = float(node.props.paragraph_line_spacing_percent)
        fields.append("lineSpacing")

    if not fields:
        return NodeResult(success=False, error="Pick at least one knob.")

    request = {
        "updateParagraphStyle": {
            "objectId": eid,
            "textRange": _text_range(node),
            "style": paragraph_style,
            "fields": ",".join(fields),
        }
    }
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(success=True, output_data=result)


# ── handlers — insert / replace / delete ────────────────────────────────


async def _insert_text_box(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid

    object_id = _gen_object_id("tb")
    requests: list[dict[str, Any]] = [
        {
            "createShape": {
                "objectId": object_id,
                "shapeType": "TEXT_BOX",
                "elementProperties": _placement(node, sid),
            }
        }
    ]
    initial = "" if node.props.text_content is None else str(node.props.text_content)
    if initial:
        requests.append({"insertText": {"objectId": object_id, "text": initial}})
    result = await _slides_batch_update(client, headers, pid, requests)
    return NodeResult(
        success=True,
        output_data={"presentation_id": pid, "element_id": object_id, "result": result},
    )


async def _insert_image(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid
    media_url = resolve_media_field(node.props.media)
    if not media_url:
        return NodeResult(success=False, error="`media` could not be resolved to a fetchable URL.")
    object_id = _gen_object_id("img")
    request = {
        "createImage": {
            "objectId": object_id,
            "url": media_url,
            "elementProperties": _placement(node, sid),
        }
    }
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(
        success=True,
        output_data={"presentation_id": pid, "element_id": object_id, "result": result},
    )


async def _insert_table(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid
    rows = max(1, int(node.props.table_rows or 2))
    cols = max(1, int(node.props.table_cols or 2))
    object_id = _gen_object_id("tbl")
    request = {
        "createTable": {
            "objectId": object_id,
            "elementProperties": _placement(node, sid),
            "rows": rows,
            "columns": cols,
        }
    }
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(
        success=True,
        output_data={"presentation_id": pid, "element_id": object_id, "result": result},
    )


async def _insert_shape(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    sid = _require_slide(node)
    if isinstance(sid, NodeResult):
        return sid
    object_id = _gen_object_id("sh")
    request = {
        "createShape": {
            "objectId": object_id,
            "shapeType": node.props.shape_type or "RECTANGLE",
            "elementProperties": _placement(node, sid),
        }
    }
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(
        success=True,
        output_data={"presentation_id": pid, "element_id": object_id, "result": result},
    )


async def _replace_image(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    from apps.api.app.node_system.nodes.meta._helpers import resolve_media_field

    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    eid = _require_element(node)
    if isinstance(eid, NodeResult):
        return eid
    media_url = resolve_media_field(node.props.media)
    if not media_url:
        return NodeResult(success=False, error="`media` could not be resolved to a fetchable URL.")
    request = {
        "replaceImage": {
            "imageObjectId": eid,
            "url": media_url,
            "imageReplaceMethod": "CENTER_INSIDE",
        }
    }
    result = await _slides_batch_update(client, headers, pid, [request])
    return NodeResult(success=True, output_data=result)


async def _delete_element(
    node: GoogleSlidesNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    pid = _require_presentation(node)
    if isinstance(pid, NodeResult):
        return pid
    eid = _require_element(node)
    if isinstance(eid, NodeResult):
        return eid
    result = await _slides_batch_update(client, headers, pid, [{"deleteObject": {"objectId": eid}}])
    return NodeResult(success=True, output_data=result)


def _gen_object_id(prefix: str) -> str:
    """Generate a Slides-API-safe object id. Slides requires the id to
    be 5–50 chars, start with a letter, and contain only letters,
    digits, dashes, and underscores."""
    import secrets

    return f"{prefix}_{secrets.token_hex(10)}"


_HANDLERS: dict[str, Any] = {
    "create": _create,
    "get": _get,
    "get_text": _get_text,
    "rename": _rename,
    "copy": _copy,
    "delete": _delete,
    "share": _share,
    "export": _export,
    "get_thumbnail": _get_thumbnail,
    "add_slide": _add_slide,
    "duplicate_slide": _duplicate_slide,
    "delete_slide": _delete_slide,
    "reorder_slide": _reorder_slide,
    "set_speaker_notes": _set_speaker_notes,
    "set_slide_background": _set_slide_background,
    "replace_all_text": _replace_all_text,
    "format_text": _format_text,
    "set_paragraph_style": _set_paragraph_style,
    "insert_text_box": _insert_text_box,
    "insert_image": _insert_image,
    "insert_table": _insert_table,
    "insert_shape": _insert_shape,
    "replace_image": _replace_image,
    "delete_element": _delete_element,
}
