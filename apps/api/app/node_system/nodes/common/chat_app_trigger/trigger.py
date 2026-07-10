"""``trigger.chat_app`` — hosted chat / form product driven directly by the
workflow.

The trigger IS the app's config. Activating the workflow makes the URL
``/apps/{workspace_slug}/{app_slug}`` live; deactivating takes it offline.
Every save to the graph is immediately reflected on the public URL — same
model as ``trigger.webhook`` or ``trigger.cron``.

Password + API key hashes live on the ``Workflow`` row (not in graph JSON)
so they don't leak via workflow export.

At runtime this trigger forwards the per-turn payload — {message, session_id,
user_id, files, form_data, history} — as its output so downstream nodes
consume it exactly like any other trigger.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

_MODE_OPTIONS = [
    {"label": "Chat — multi-turn conversation", "value": "chat"},
    {"label": "Form — one-shot input → result page", "value": "form"},
    {"label": "Agent — chat with baked-in persona + tools", "value": "agent"},
]

_AUTH_OPTIONS = [
    {"label": "Public — anyone with the link", "value": "public"},
    {"label": "Password — one shared password", "value": "password"},
    {"label": "Login — Fuse account required", "value": "login"},
    {"label": "API key — X-App-Key header", "value": "api_key"},
]

_INPUT_FIELD_TYPE_OPTIONS = [
    {"label": "Text", "value": "text"},
    {"label": "Long text", "value": "textarea"},
    {"label": "Number", "value": "number"},
    {"label": "Yes / No", "value": "boolean"},
    {"label": "Select one", "value": "select"},
    {"label": "Select many", "value": "multiselect"},
    {"label": "Date", "value": "date"},
    {"label": "Email", "value": "email"},
    {"label": "URL", "value": "url"},
    {"label": "File upload", "value": "file"},
]


class ChatAppTriggerProperties(BaseModel):
    # Identity
    app_slug: str = ""
    title: str = "My Chat App"
    description: str = ""
    mode: str = "chat"  # chat | form | agent

    # Welcome experience
    welcome_headline: str = ""
    welcome_sub: str = ""
    welcome_message: str = ""
    suggested_prompts: list[dict[str, Any]] = Field(default_factory=list)

    # Runtime wiring
    system_persona_id: str | None = None
    allow_history: bool = True
    output_target: str = "both"  # chat | canvas | both

    # Form / attachments
    input_fields: list[dict[str, Any]] = Field(default_factory=list)
    allow_file_upload: bool = False
    allowed_file_types: list[str] = Field(default_factory=list)
    max_file_size_mb: int = 10

    # Auth
    auth_mode: str = "public"

    # Rate limits + cost caps
    rate_limit_per_min: int = 20
    session_cost_cap_usd: float = 5.0
    daily_cost_cap_usd: float = 50.0

    # Theme
    primary_color: str = "#8b5cf6"
    logo_url: str = ""
    dark_mode: str = "auto"  # light | dark | auto
    show_powered_by: bool = True

    # SEO
    og_image_url: str = ""


class ChatAppTriggerNode(BaseNode[ChatAppTriggerProperties]):
    @classmethod
    def get_properties_model(cls) -> type[ChatAppTriggerProperties]:
        return ChatAppTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.chat_app",
            name="Chat App",
            category="trigger",
            description=(
                "Turn this workflow into a hosted chat / form product. Activate the "
                "workflow → URL goes live at /apps/{workspace}/{slug}. Each visitor "
                "message runs the graph."
            ),
            icon="MessagesSquare",
            color="#8b5cf6",
            properties=[
                # ── Identity ──────────────────────────────────────
                {
                    "name": "title",
                    "label": "App title",
                    "type": "string",
                    "required": True,
                    "placeholder": "Support Bot",
                    "description": "Shown as the page title and header.",
                },
                {
                    "name": "app_slug",
                    "label": "URL slug",
                    "type": "string",
                    "placeholder": "support-bot",
                    "description": (
                        "URL-safe identifier. Full URL: /apps/{workspace}/{slug}. "
                        "Leave empty to auto-generate from the title."
                    ),
                },
                {
                    "name": "description",
                    "label": "Description",
                    "type": "string",
                    "placeholder": "Ask us anything about our product.",
                    "description": "Subtitle + social share meta description.",
                },
                {
                    "name": "mode",
                    "label": "Mode",
                    "type": "options",
                    "default": "chat",
                    "required": True,
                    "options": _MODE_OPTIONS,
                },
                # ── Welcome ───────────────────────────────────────
                {
                    "name": "welcome_headline",
                    "label": "Welcome headline",
                    "type": "string",
                    "placeholder": "How can I help you today?",
                },
                {
                    "name": "welcome_sub",
                    "label": "Welcome subtitle",
                    "type": "string",
                    "placeholder": "Ask me anything.",
                },
                {
                    "name": "welcome_message",
                    "label": "First assistant message",
                    "type": "string",
                    "typeOptions": {"multiline": True},
                    "placeholder": "Hi! I'm here to answer questions about…",
                    "description": "Markdown supported.",
                },
                {
                    "name": "suggested_prompts",
                    "label": "Suggested prompts",
                    "type": "collection",
                    "default": [],
                    "typeOptions": {
                        "multipleValues": True,
                        "addButtonText": "Add suggestion",
                    },
                    "properties": [
                        {"name": "label", "label": "Chip label", "type": "string"},
                        {"name": "prompt", "label": "Prompt sent", "type": "string"},
                    ],
                },
                # ── Runtime wiring ────────────────────────────────
                {
                    "name": "system_persona_id",
                    "label": "System persona",
                    "type": "persona-picker",
                    "required": False,
                    "description": "Overlay this persona onto the first agent node.",
                },
                {
                    "name": "allow_history",
                    "label": "Remember conversation history",
                    "type": "boolean",
                    "default": True,
                    "mode": "advanced",
                },
                {
                    "name": "output_target",
                    "label": "Where do artifacts render?",
                    "type": "options",
                    "default": "both",
                    "mode": "advanced",
                    "options": [
                        {"label": "Chat inline only", "value": "chat"},
                        {"label": "Canvas panel only", "value": "canvas"},
                        {"label": "Both — inline reference + canvas", "value": "both"},
                    ],
                },
                # ── Form fields ────────────────────────────────────
                {
                    "name": "input_fields",
                    "label": "Input fields",
                    "type": "collection",
                    "default": [],
                    "mode": "advanced",
                    "typeOptions": {
                        "multipleValues": True,
                        "addButtonText": "Add field",
                        "autoIncrementField": "name",
                        "autoIncrementPrefix": "field",
                    },
                    "properties": [
                        {"name": "name", "label": "Name", "type": "string", "required": True},
                        {"name": "label", "label": "Label", "type": "string"},
                        {
                            "name": "type",
                            "label": "Type",
                            "type": "options",
                            "default": "text",
                            "options": _INPUT_FIELD_TYPE_OPTIONS,
                        },
                        {
                            "name": "required",
                            "label": "Required",
                            "type": "boolean",
                            "default": False,
                        },
                        {"name": "placeholder", "label": "Placeholder", "type": "string"},
                        {"name": "help_text", "label": "Help text", "type": "string"},
                    ],
                    "description": "Form fields (form mode). Also usable as chat attachments.",
                },
                {
                    "name": "allow_file_upload",
                    "label": "Allow file upload",
                    "type": "boolean",
                    "default": False,
                    "mode": "advanced",
                },
                {
                    "name": "allowed_file_types",
                    "label": "Allowed mime types (blank = any)",
                    "type": "list",
                    "default": [],
                    "mode": "advanced",
                    "condition": {"field": "allow_file_upload", "value": True},
                },
                {
                    "name": "max_file_size_mb",
                    "label": "Max file size (MB)",
                    "type": "number",
                    "default": 10,
                    "mode": "advanced",
                    "condition": {"field": "allow_file_upload", "value": True},
                },
                # ── Auth ──────────────────────────────────────────
                {
                    "name": "auth_mode",
                    "label": "Access",
                    "type": "options",
                    "default": "public",
                    "options": _AUTH_OPTIONS,
                    "description": (
                        "Password + API key values are set via the Share dialog — "
                        "never stored in the graph."
                    ),
                },
                # ── Rate limits + cost caps ──────────────────────
                {
                    "name": "rate_limit_per_min",
                    "label": "Rate limit (msgs/min per visitor)",
                    "type": "number",
                    "default": 20,
                    "mode": "advanced",
                },
                {
                    "name": "session_cost_cap_usd",
                    "label": "Session cost cap ($)",
                    "type": "number",
                    "default": 5.0,
                    "mode": "advanced",
                },
                {
                    "name": "daily_cost_cap_usd",
                    "label": "Daily cost cap ($)",
                    "type": "number",
                    "default": 50.0,
                    "mode": "advanced",
                },
                # ── Theme ─────────────────────────────────────────
                {
                    "name": "primary_color",
                    "label": "Primary color",
                    "type": "string",
                    "default": "#8b5cf6",
                    "mode": "advanced",
                },
                {
                    "name": "logo_url",
                    "label": "Logo URL",
                    "type": "string",
                    "mode": "advanced",
                },
                {
                    "name": "dark_mode",
                    "label": "Dark mode",
                    "type": "options",
                    "default": "auto",
                    "mode": "advanced",
                    "options": [
                        {"label": "Auto (follow visitor)", "value": "auto"},
                        {"label": "Light", "value": "light"},
                        {"label": "Dark", "value": "dark"},
                    ],
                },
                {
                    "name": "show_powered_by",
                    "label": "Show 'Powered by Fuse'",
                    "type": "boolean",
                    "default": True,
                    "mode": "advanced",
                },
                # ── SEO ───────────────────────────────────────────
                {
                    "name": "og_image_url",
                    "label": "Social share image",
                    "type": "string",
                    "mode": "advanced",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "message", "type": "string"},
                {"label": "session_id", "type": "string"},
                {"label": "user_id", "type": "string"},
                {"label": "files", "type": "array"},
                {"label": "form_data", "type": "object"},
                {"label": "history", "type": "array"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        payload = input_data if isinstance(input_data, dict) else {}
        return NodeResult(
            success=True,
            output_data={
                "message": payload.get("message") or "",
                "session_id": payload.get("session_id") or "",
                "user_id": payload.get("user_id"),
                "files": payload.get("files") or [],
                "form_data": payload.get("form_data") or {},
                "history": payload.get("history") or [],
            },
        )
