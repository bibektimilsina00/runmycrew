"""Google Forms action node — one node, 14 operations.

Form-level
  - `create`              / `get_form`
  - `update_form_info`    / `update_settings`
  - `delete`              / `share`

Items / questions
  - `add_text_question`        (short or paragraph)
  - `add_choice_question`      (RADIO / CHECKBOX / DROP_DOWN)
  - `add_date_question`        (optional time + year)
  - `add_scale_question`       (low / high + labels)
  - `add_file_upload_question` (max files + size + accepted types)
  - `add_section_break`
  - `delete_item`              / `move_item`

Responses
  - `list_responses`           (with `submitted_after` filter)
  - `get_response`

OAuth scopes: `forms.body` + `forms.responses.readonly` + `drive.file`
(all in `GoogleOAuthProvider`).
Mime: `application/vnd.google-apps.form`.
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

logger = get_logger(__name__)

FORMS_API = "https://forms.googleapis.com/v1/forms"
DRIVE_API = "https://www.googleapis.com/drive/v3"
FORM_MIME = "application/vnd.google-apps.form"


# Choice-question kinds the API accepts. Quiz-style picks live on the
# same enum, but we surface the three common shapes by default — power
# users can still drive the rest via `add_choice_question` if needed.
_CHOICE_TYPE_OPTIONS: list[dict[str, str]] = [
    {"label": "Radio (single answer)", "value": "RADIO"},
    {"label": "Checkbox (multi answer)", "value": "CHECKBOX"},
    {"label": "Dropdown", "value": "DROP_DOWN"},
]


_EMAIL_COLLECTION_OPTIONS: list[dict[str, str]] = [
    {"label": "Don't collect emails", "value": "DO_NOT_COLLECT"},
    {"label": "Verified email (Google account required)", "value": "VERIFIED"},
    {"label": "Responder-entered email", "value": "RESPONDER_INPUT"},
]


class GoogleFormsProperties(BaseModel):
    credential: str | None = None
    operation: str = "get_form"

    form_id: str | None = None

    # create / update_form_info / share
    title: str | None = None
    description: str | None = None
    document_title: str | None = None

    # update_settings
    is_quiz: bool = False
    email_collection_type: str = "DO_NOT_COLLECT"

    # add_* common
    question_title: Any = None
    required: bool = False
    item_index: int | None = None  # zero-based; None → append

    # add_text_question
    paragraph: bool = False

    # add_choice_question
    choice_type: str = "RADIO"
    choices: Any = None  # list[str]
    shuffle: bool = False

    # add_date_question
    include_time: bool = False
    include_year: bool = True

    # add_scale_question
    scale_low: int = 1
    scale_high: int = 5
    low_label: str | None = None
    high_label: str | None = None

    # add_file_upload_question
    max_files: int = 1
    max_file_size_mb: int = 10
    allowed_types: Any = None  # list[str] e.g. ["IMAGE", "PDF", "DOCUMENT"]

    # delete_item / move_item
    original_index: int | None = None
    new_index: int | None = None

    # share
    share_email: str | None = None
    share_role: str = "reader"
    share_send_notification: bool = False

    # list_responses
    submitted_after: str | None = None  # RFC3339
    page_size: int = 100
    page_token: str | None = None

    # get_response
    response_id: str | None = None

    @field_validator("form_id", mode="before")
    @classmethod
    def _coerce_form_id(cls, value: Any) -> str | None:
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


# Ops grouped so the conditional-visibility list at the top stays
# readable. Anything that's form-scoped needs `form_id`.
_FORM_SCOPED_OPS = (
    "get_form",
    "update_form_info",
    "update_settings",
    "delete",
    "share",
    "add_text_question",
    "add_choice_question",
    "add_date_question",
    "add_scale_question",
    "add_file_upload_question",
    "add_section_break",
    "delete_item",
    "move_item",
    "list_responses",
    "get_response",
)
_ADD_QUESTION_OPS = (
    "add_text_question",
    "add_choice_question",
    "add_date_question",
    "add_scale_question",
    "add_file_upload_question",
    "add_section_break",
)


class GoogleFormsNode(BaseNode[GoogleFormsProperties]):
    @classmethod
    def get_properties_model(cls):
        return GoogleFormsProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.gforms",
            name="Google Forms",
            category="integration",
            description=(
                "Create, edit, and read Google Forms — manage questions and "
                "settings, share via Drive, and pull responses."
            ),
            icon="google-forms",
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
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "get_form",
                    "options": [
                        {"label": "Read Form Structure", "value": "get_form"},
                        {"label": "Create Form", "value": "create"},
                        {"label": "Update Title / Description", "value": "update_form_info"},
                        {"label": "Update Settings", "value": "update_settings"},
                        {"label": "Add Text Question", "value": "add_text_question"},
                        {"label": "Add Choice Question", "value": "add_choice_question"},
                        {"label": "Add Date Question", "value": "add_date_question"},
                        {"label": "Add Linear Scale", "value": "add_scale_question"},
                        {"label": "Add File Upload", "value": "add_file_upload_question"},
                        {"label": "Add Section Break", "value": "add_section_break"},
                        {"label": "Delete Item", "value": "delete_item"},
                        {"label": "Move Item", "value": "move_item"},
                        {"label": "List Responses", "value": "list_responses"},
                        {"label": "Get Response", "value": "get_response"},
                        {"label": "Share Form", "value": "share"},
                        {"label": "Delete Form", "value": "delete"},
                    ],
                },
                # form_id — everything except `create` needs it
                {
                    "name": "form_id",
                    "label": "Form",
                    "type": "google-file",
                    "required": True,
                    "typeOptions": {
                        "mimeType": FORM_MIME,
                        "placeholder": "Pick a form…",
                        "searchPlaceholder": "Search your forms…",
                        "createPlaceholder": "Create new form…",
                    },
                    "condition": _cond_any(*_FORM_SCOPED_OPS),
                },
                # ── create / update_form_info ──────────────────────────
                {
                    "name": "title",
                    "label": "Title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Customer feedback",
                    "condition": _cond_any("create", "update_form_info"),
                },
                {
                    "name": "description",
                    "label": "Description",
                    "type": "string",
                    "typeOptions": {"multiline": True, "rows": 3},
                    "placeholder": "Shown under the form title",
                    "condition": _cond_any("create", "update_form_info"),
                    "mode": "advanced",
                },
                {
                    "name": "document_title",
                    "label": "Document title (Drive name)",
                    "type": "string",
                    "description": "Optional override for the file name in Drive.",
                    "condition": _cond_any("create", "update_form_info"),
                    "mode": "advanced",
                },
                # ── update_settings ────────────────────────────────────
                {
                    "name": "is_quiz",
                    "label": "Quiz mode",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("update_settings"),
                },
                {
                    "name": "email_collection_type",
                    "label": "Email collection",
                    "type": "options",
                    "default": "DO_NOT_COLLECT",
                    "options": _EMAIL_COLLECTION_OPTIONS,
                    "condition": _cond("update_settings"),
                },
                # ── add_* shared ───────────────────────────────────────
                {
                    "name": "question_title",
                    "label": "Question title",
                    "type": "string",
                    "required": True,
                    "placeholder": "What's your favourite colour?",
                    "condition": _cond_any(*_ADD_QUESTION_OPS),
                },
                {
                    "name": "required",
                    "label": "Required answer",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond_any(
                        "add_text_question",
                        "add_choice_question",
                        "add_date_question",
                        "add_scale_question",
                        "add_file_upload_question",
                    ),
                },
                {
                    "name": "item_index",
                    "label": "Insert at index",
                    "type": "number",
                    "description": "Zero-based position. Leave blank to append.",
                    "condition": _cond_any(*_ADD_QUESTION_OPS),
                    "mode": "advanced",
                },
                # ── add_text_question ──────────────────────────────────
                {
                    "name": "paragraph",
                    "label": "Paragraph (long answer)",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("add_text_question"),
                },
                # ── add_choice_question ────────────────────────────────
                {
                    "name": "choice_type",
                    "label": "Choice kind",
                    "type": "options",
                    "default": "RADIO",
                    "options": _CHOICE_TYPE_OPTIONS,
                    "condition": _cond("add_choice_question"),
                },
                {
                    "name": "choices",
                    "label": "Choices",
                    "type": "json",
                    "required": True,
                    "placeholder": '["Red", "Green", "Blue"]',
                    "description": "Array of option strings.",
                    "condition": _cond("add_choice_question"),
                },
                {
                    "name": "shuffle",
                    "label": "Shuffle option order",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("add_choice_question"),
                    "mode": "advanced",
                },
                # ── add_date_question ──────────────────────────────────
                {
                    "name": "include_time",
                    "label": "Include time",
                    "type": "boolean",
                    "default": False,
                    "condition": _cond("add_date_question"),
                },
                {
                    "name": "include_year",
                    "label": "Include year",
                    "type": "boolean",
                    "default": True,
                    "condition": _cond("add_date_question"),
                    "mode": "advanced",
                },
                # ── add_scale_question ─────────────────────────────────
                {
                    "name": "scale_low",
                    "label": "Low value",
                    "type": "number",
                    "default": 1,
                    "condition": _cond("add_scale_question"),
                },
                {
                    "name": "scale_high",
                    "label": "High value",
                    "type": "number",
                    "default": 5,
                    "condition": _cond("add_scale_question"),
                },
                {
                    "name": "low_label",
                    "label": "Low label",
                    "type": "string",
                    "placeholder": "Strongly disagree",
                    "condition": _cond("add_scale_question"),
                    "mode": "advanced",
                },
                {
                    "name": "high_label",
                    "label": "High label",
                    "type": "string",
                    "placeholder": "Strongly agree",
                    "condition": _cond("add_scale_question"),
                    "mode": "advanced",
                },
                # ── add_file_upload_question ───────────────────────────
                {
                    "name": "max_files",
                    "label": "Max files",
                    "type": "number",
                    "default": 1,
                    "condition": _cond("add_file_upload_question"),
                },
                {
                    "name": "max_file_size_mb",
                    "label": "Max file size (MB)",
                    "type": "number",
                    "default": 10,
                    "condition": _cond("add_file_upload_question"),
                },
                {
                    "name": "allowed_types",
                    "label": "Allowed types",
                    "type": "json",
                    "placeholder": '["IMAGE", "DOCUMENT", "PDF"]',
                    "description": (
                        "Array of Google Forms type tags: ANY, DOCUMENT, "
                        "PRESENTATION, SPREADSHEET, DRAWING, PDF, IMAGE, "
                        "VIDEO, AUDIO."
                    ),
                    "condition": _cond("add_file_upload_question"),
                    "mode": "advanced",
                },
                # ── delete_item / move_item ────────────────────────────
                {
                    "name": "original_index",
                    "label": "Original index",
                    "type": "number",
                    "required": True,
                    "condition": _cond_any("delete_item", "move_item"),
                },
                {
                    "name": "new_index",
                    "label": "New index",
                    "type": "number",
                    "required": True,
                    "condition": _cond("move_item"),
                },
                # ── list_responses ─────────────────────────────────────
                {
                    "name": "submitted_after",
                    "label": "Submitted after",
                    "type": "datetime",
                    "typeOptions": {"granularity": "datetime"},
                    "description": "Optional — filter to responses submitted after this point.",
                    "condition": _cond("list_responses"),
                },
                {
                    "name": "page_size",
                    "label": "Page size",
                    "type": "number",
                    "default": 100,
                    "condition": _cond("list_responses"),
                    "mode": "advanced",
                },
                {
                    "name": "page_token",
                    "label": "Page token",
                    "type": "string",
                    "placeholder": "Continuation token from prior call",
                    "condition": _cond("list_responses"),
                    "mode": "advanced",
                },
                # ── get_response ───────────────────────────────────────
                {
                    "name": "response_id",
                    "label": "Response ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $trigger.response_id }}",
                    "condition": _cond("get_response"),
                },
                # ── share ──────────────────────────────────────────────
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
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "form_id", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "responder_uri", "type": "string"},
                {"label": "answers", "type": "object"},
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
                error=f"Google Forms API error {exc.response.status_code}: {exc.response.text[:300]}",
            )
        except Exception as exc:  # noqa: BLE001
            logger.error(f"GoogleFormsNode {op} failed: {exc}", exc_info=True)
            return NodeResult(success=False, error=str(exc))


# ── shared helpers ──────────────────────────────────────────────────────


def _require_form(node: GoogleFormsNode) -> str | NodeResult:
    fid = (node.props.form_id or "").strip()
    if not fid:
        return NodeResult(success=False, error="Form is required.")
    return fid


async def _form_batch_update(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    form_id: str,
    requests: list[dict[str, Any]],
) -> dict[str, Any]:
    r = await client.post(
        f"{FORMS_API}/{form_id}:batchUpdate",
        headers=headers,
        json={"requests": requests},
    )
    r.raise_for_status()
    return r.json()


def _question_item_payload(question: dict[str, Any], *, required: bool) -> dict[str, Any]:
    return {
        "questionItem": {
            "question": {"required": bool(required), **question},
        },
    }


def _build_create_item_request(
    title: str,
    item_inner: dict[str, Any],
    *,
    description: str | None = None,
    location_index: int | None = None,
) -> dict[str, Any]:
    item: dict[str, Any] = {"title": title}
    if description:
        item["description"] = description
    item.update(item_inner)
    location = {"index": int(location_index) if location_index is not None else 0}
    return {
        "createItem": {
            "item": item,
            "location": location,
        }
    }


# ── form-level handlers ─────────────────────────────────────────────────


async def _create(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    title = (node.props.title or "").strip()
    if not title:
        return NodeResult(success=False, error="Title is required.")
    body: dict[str, Any] = {"info": {"title": title}}
    if node.props.document_title:
        body["info"]["documentTitle"] = node.props.document_title
    # The create endpoint accepts only `info`; description has to follow
    # via a batchUpdate. We do that in one go for the user.
    r = await client.post(FORMS_API, headers=headers, json=body)
    r.raise_for_status()
    data = r.json()
    form_id = data.get("formId")
    if node.props.description and form_id:
        await _form_batch_update(
            client,
            headers,
            form_id,
            [
                {
                    "updateFormInfo": {
                        "info": {"description": node.props.description},
                        "updateMask": "description",
                    }
                }
            ],
        )
    return NodeResult(
        success=True,
        output_data={
            "form_id": form_id,
            "title": title,
            "responder_uri": data.get("responderUri"),
            "edit_uri": (f"https://docs.google.com/forms/d/{form_id}/edit" if form_id else None),
        },
    )


async def _get_form(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    r = await client.get(f"{FORMS_API}/{fid}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=r.json())


async def _update_form_info(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    info: dict[str, Any] = {}
    mask: list[str] = []
    if node.props.title:
        info["title"] = node.props.title
        mask.append("title")
    if node.props.description is not None:
        info["description"] = node.props.description
        mask.append("description")
    if node.props.document_title:
        info["documentTitle"] = node.props.document_title
        mask.append("documentTitle")
    if not mask:
        return NodeResult(success=False, error="Pick at least one field to update.")
    result = await _form_batch_update(
        client,
        headers,
        fid,
        [{"updateFormInfo": {"info": info, "updateMask": ",".join(mask)}}],
    )
    return NodeResult(success=True, output_data=result)


async def _update_settings(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    settings: dict[str, Any] = {
        "quizSettings": {"isQuiz": bool(node.props.is_quiz)},
        "emailCollectionType": node.props.email_collection_type or "DO_NOT_COLLECT",
    }
    result = await _form_batch_update(
        client,
        headers,
        fid,
        [
            {
                "updateSettings": {
                    "settings": settings,
                    "updateMask": "quizSettings,emailCollectionType",
                }
            }
        ],
    )
    return NodeResult(success=True, output_data=result)


async def _delete(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    r = await client.patch(
        f"{DRIVE_API}/files/{fid}",
        headers=headers,
        json={"trashed": True},
        params={"supportsAllDrives": "true"},
    )
    r.raise_for_status()
    return NodeResult(success=True, output_data={"form_id": fid, "trashed": True})


async def _share(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    email = (node.props.share_email or "").strip()
    if not email:
        return NodeResult(success=False, error="`share_email` is required.")
    r = await client.post(
        f"{DRIVE_API}/files/{fid}/permissions",
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


# ── item handlers ───────────────────────────────────────────────────────


def _require_title(node: GoogleFormsNode) -> str | NodeResult:
    title = "" if node.props.question_title is None else str(node.props.question_title)
    if not title.strip():
        return NodeResult(success=False, error="Question title is required.")
    return title


async def _add_text_question(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    title = _require_title(node)
    if isinstance(title, NodeResult):
        return title
    item_inner = _question_item_payload(
        {"textQuestion": {"paragraph": bool(node.props.paragraph)}},
        required=node.props.required,
    )
    req = _build_create_item_request(title, item_inner, location_index=node.props.item_index)
    result = await _form_batch_update(client, headers, fid, [req])
    return NodeResult(success=True, output_data=result)


async def _add_choice_question(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    title = _require_title(node)
    if isinstance(title, NodeResult):
        return title
    raw_choices = node.props.choices
    if not isinstance(raw_choices, list) or not raw_choices:
        return NodeResult(success=False, error="`choices` must be a non-empty array.")
    choices = [{"value": str(c)} for c in raw_choices if str(c).strip()]
    if not choices:
        return NodeResult(success=False, error="`choices` had no non-blank entries.")
    item_inner = _question_item_payload(
        {
            "choiceQuestion": {
                "type": node.props.choice_type or "RADIO",
                "options": choices,
                "shuffle": bool(node.props.shuffle),
            }
        },
        required=node.props.required,
    )
    req = _build_create_item_request(title, item_inner, location_index=node.props.item_index)
    result = await _form_batch_update(client, headers, fid, [req])
    return NodeResult(success=True, output_data=result)


async def _add_date_question(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    title = _require_title(node)
    if isinstance(title, NodeResult):
        return title
    item_inner = _question_item_payload(
        {
            "dateQuestion": {
                "includeTime": bool(node.props.include_time),
                "includeYear": bool(node.props.include_year),
            }
        },
        required=node.props.required,
    )
    req = _build_create_item_request(title, item_inner, location_index=node.props.item_index)
    result = await _form_batch_update(client, headers, fid, [req])
    return NodeResult(success=True, output_data=result)


async def _add_scale_question(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    title = _require_title(node)
    if isinstance(title, NodeResult):
        return title
    low = int(node.props.scale_low or 1)
    high = int(node.props.scale_high or 5)
    if high <= low:
        return NodeResult(success=False, error="`scale_high` must be greater than `scale_low`.")
    scale: dict[str, Any] = {"low": low, "high": high}
    if node.props.low_label:
        scale["lowLabel"] = node.props.low_label
    if node.props.high_label:
        scale["highLabel"] = node.props.high_label
    item_inner = _question_item_payload(
        {"scaleQuestion": scale},
        required=node.props.required,
    )
    req = _build_create_item_request(title, item_inner, location_index=node.props.item_index)
    result = await _form_batch_update(client, headers, fid, [req])
    return NodeResult(success=True, output_data=result)


async def _add_file_upload_question(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    title = _require_title(node)
    if isinstance(title, NodeResult):
        return title
    file_q: dict[str, Any] = {
        "maxFiles": max(1, int(node.props.max_files or 1)),
        "maxFileSize": str(int(node.props.max_file_size_mb or 10) * 1024 * 1024),
    }
    if isinstance(node.props.allowed_types, list) and node.props.allowed_types:
        file_q["types"] = [str(t).upper() for t in node.props.allowed_types]
    item_inner = _question_item_payload(
        {"fileUploadQuestion": file_q},
        required=node.props.required,
    )
    req = _build_create_item_request(title, item_inner, location_index=node.props.item_index)
    result = await _form_batch_update(client, headers, fid, [req])
    return NodeResult(success=True, output_data=result)


async def _add_section_break(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    title = _require_title(node)
    if isinstance(title, NodeResult):
        return title
    item_inner = {"pageBreakItem": {}}
    req = _build_create_item_request(title, item_inner, location_index=node.props.item_index)
    result = await _form_batch_update(client, headers, fid, [req])
    return NodeResult(success=True, output_data=result)


async def _delete_item(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    if node.props.original_index is None:
        return NodeResult(success=False, error="`original_index` is required.")
    req = {"deleteItem": {"location": {"index": int(node.props.original_index)}}}
    result = await _form_batch_update(client, headers, fid, [req])
    return NodeResult(success=True, output_data=result)


async def _move_item(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    if node.props.original_index is None or node.props.new_index is None:
        return NodeResult(
            success=False,
            error="`original_index` and `new_index` are both required.",
        )
    req = {
        "moveItem": {
            "originalLocation": {"index": int(node.props.original_index)},
            "newLocation": {"index": int(node.props.new_index)},
        }
    }
    result = await _form_batch_update(client, headers, fid, [req])
    return NodeResult(success=True, output_data=result)


# ── response handlers ──────────────────────────────────────────────────


def _extract_answer_value(answer: dict[str, Any]) -> Any:
    """Pull the human-readable value out of a Forms answer payload.

    Forms wraps the actual response inside a typed sub-object — text,
    file uploads, and a few enum-typed inputs. We collapse to a single
    Python value so downstream nodes can read `answers[title]` without
    knowing the wire shape."""
    text = (answer.get("textAnswers") or {}).get("answers") or []
    if text:
        # Multiple values come back when the question is a checkbox
        # (one entry per checked option) — return list; otherwise scalar.
        values = [a.get("value") for a in text if a.get("value") is not None]
        return values if len(values) > 1 else (values[0] if values else None)
    files = (answer.get("fileUploadAnswers") or {}).get("answers") or []
    if files:
        return [
            {
                "id": f.get("fileId"),
                "name": f.get("fileName"),
                "mime_type": f.get("mimeType"),
            }
            for f in files
        ]
    grade = answer.get("grade")
    if grade is not None:
        return grade
    return None


def _build_question_id_to_title(form: dict[str, Any]) -> dict[str, str]:
    """Walk the form's item tree → `{question_id: question_title}` map.
    Responses arrive keyed by `questionId`, but users want to read
    answers by their question text."""
    mapping: dict[str, str] = {}
    for item in form.get("items") or []:
        title = item.get("title") or ""
        q = (item.get("questionItem") or {}).get("question") or {}
        qid = q.get("questionId")
        if qid:
            mapping[str(qid)] = title
        # questionGroupItem (grid) — one questionId per row
        for row in (item.get("questionGroupItem") or {}).get("questions") or []:
            qid = (row.get("rowQuestion") or {}).get("title") and row.get("questionId")
            if row.get("questionId"):
                mapping[str(row["questionId"])] = (row.get("rowQuestion") or {}).get(
                    "title"
                ) or title
    return mapping


def _normalise_response(response: dict[str, Any], titles: dict[str, str]) -> dict[str, Any]:
    """Flatten a response into a friendlier shape: `{question_title:
    value}`. Also surfaces the raw payload for power users."""
    answers_in = response.get("answers") or {}
    answers_out: dict[str, Any] = {}
    for qid, a in answers_in.items():
        title = titles.get(str(qid), str(qid))
        answers_out[title] = _extract_answer_value(a)
    return {
        "response_id": response.get("responseId"),
        "form_id": response.get("formId"),
        "submitted_at": response.get("lastSubmittedTime") or response.get("createTime"),
        "respondent_email": response.get("respondentEmail") or "",
        "answers": answers_out,
        "payload": response,
    }


async def _fetch_titles(
    client: httpx.AsyncClient, headers: dict[str, str], form_id: str
) -> dict[str, str]:
    r = await client.get(f"{FORMS_API}/{form_id}", headers=headers)
    r.raise_for_status()
    return _build_question_id_to_title(r.json())


async def _list_responses(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    titles = await _fetch_titles(client, headers, fid)
    params: dict[str, str] = {
        "pageSize": str(max(1, min(int(node.props.page_size or 100), 5000))),
    }
    if node.props.page_token:
        params["pageToken"] = node.props.page_token
    if node.props.submitted_after:
        # Forms expects the filter string `timestamp > 2024-01-01T00:00:00Z`.
        params["filter"] = f"timestamp > {node.props.submitted_after}"
    r = await client.get(f"{FORMS_API}/{fid}/responses", headers=headers, params=params)
    r.raise_for_status()
    data = r.json()
    responses = [_normalise_response(resp, titles) for resp in (data.get("responses") or [])]
    return NodeResult(
        success=True,
        output_data={
            "responses": responses,
            "next_page_token": data.get("nextPageToken"),
            "matched": len(responses),
        },
    )


async def _get_response(
    node: GoogleFormsNode, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    fid = _require_form(node)
    if isinstance(fid, NodeResult):
        return fid
    rid = (node.props.response_id or "").strip()
    if not rid:
        return NodeResult(success=False, error="`response_id` is required.")
    titles = await _fetch_titles(client, headers, fid)
    r = await client.get(f"{FORMS_API}/{fid}/responses/{rid}", headers=headers)
    r.raise_for_status()
    return NodeResult(success=True, output_data=_normalise_response(r.json(), titles))


_HANDLERS: dict[str, Any] = {
    "create": _create,
    "get_form": _get_form,
    "update_form_info": _update_form_info,
    "update_settings": _update_settings,
    "delete": _delete,
    "share": _share,
    "add_text_question": _add_text_question,
    "add_choice_question": _add_choice_question,
    "add_date_question": _add_date_question,
    "add_scale_question": _add_scale_question,
    "add_file_upload_question": _add_file_upload_question,
    "add_section_break": _add_section_break,
    "delete_item": _delete_item,
    "move_item": _move_item,
    "list_responses": _list_responses,
    "get_response": _get_response,
}
