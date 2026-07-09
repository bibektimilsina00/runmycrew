"""``trigger.chat_app`` — publish a workflow as a hosted chat / form product.

The trigger's inspector holds the *default* config for the app. Publishing
(via the ``PublishedApp`` row) snapshots these values along with any theme /
auth / rate-limit knobs set in the Publish modal. Live workflow edits do not
touch the published version until re-publish (version pinning).

At runtime this trigger just forwards the per-turn payload — {message,
session_id, user_id, files, form_data} — as its output so downstream nodes
can consume it exactly like any other trigger.
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
    # Identity — the slug becomes /apps/{workspace_slug}/{app_slug}
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

    # Input schema for form mode (also surfaces as attachments in chat mode)
    input_fields: list[dict[str, Any]] = Field(default_factory=list)


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
                "Publish this workflow as a hosted chat or form app. Anyone with the "
                "link can talk to it — each user turn becomes a workflow run."
            ),
            icon="MessagesSquare",
            color="#8b5cf6",
            properties=[
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
                        "Leave empty to auto-generate from the title on publish."
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
                    "description": "Chat = conversation. Form = one input page + one result page.",
                },
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
                    "description": "Markdown supported. Rendered as the assistant's opening turn.",
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
                        {
                            "name": "label",
                            "label": "Chip label",
                            "type": "string",
                            "placeholder": "Return policy",
                        },
                        {
                            "name": "prompt",
                            "label": "Prompt sent",
                            "type": "string",
                            "placeholder": "What is your return policy?",
                        },
                    ],
                    "description": "Quick-start chips shown before the first message.",
                },
                {
                    "name": "system_persona_id",
                    "label": "System persona",
                    "type": "persona-picker",
                    "required": False,
                    "description": "Overlay this persona onto the first agent node in the graph.",
                },
                {
                    "name": "allow_history",
                    "label": "Remember conversation history",
                    "type": "boolean",
                    "default": True,
                    "description": "Injects prior messages as memory into the first agent node.",
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
                        {
                            "name": "name",
                            "label": "Name",
                            "type": "string",
                            "required": True,
                            "placeholder": "field1",
                        },
                        {
                            "name": "label",
                            "label": "Label",
                            "type": "string",
                            "placeholder": "Company URL",
                        },
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
                        {
                            "name": "placeholder",
                            "label": "Placeholder",
                            "type": "string",
                        },
                        {
                            "name": "help_text",
                            "label": "Help text",
                            "type": "string",
                        },
                    ],
                    "description": "Form fields (form mode) — also surface as chat attachments.",
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
        # At runtime a per-turn payload is injected by the app_message worker
        # task (see apps/worker/app/jobs/tasks.py:execute_app_message). The
        # trigger just forwards it downstream. In an editor "run node" test
        # with no payload, we emit sensible empty defaults so downstream
        # nodes can be exercised in isolation.
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
