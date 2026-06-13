from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class FBMessageTriggerProperties(BaseModel):
    # Selected via the `meta-resource` field type (kind=page). The id here
    # is the FB Page id — same value Meta uses as `entry.id` on Messenger
    # webhook deliveries, which is what MetaService.receive_webhook filters
    # on via `page_id` in _target_filters.
    page_id: str = ""
    keyword: str | None = Field(
        default=None,
        description="Optional case-insensitive substring filter on message text.",
    )


class FBMessageTriggerNode(BaseNode[FBMessageTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.fb_message",
            name="Messenger DM",
            category="trigger",
            description=(
                "Fires when a user sends a direct message to the connected "
                "Facebook Page. Use this to drive Messenger bot replies."
            ),
            icon="MessageCircle",
            color="#0084FF",
            properties=[
                {
                    "name": "credential",
                    "label": "Meta Account",
                    "type": "credential",
                    "credentialType": "meta_oauth",
                    "required": True,
                },
                {
                    "name": "page_id",
                    "label": "Facebook Page",
                    "type": "meta-resource",
                    "resourceKind": "page",
                    "dependsOn": ["credential"],
                    "required": True,
                },
                {
                    "name": "keyword",
                    "label": "Keyword filter (optional)",
                    "type": "string",
                    "placeholder": "support",
                    "description": "Case-insensitive substring match on message text.",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "message_id", "type": "string"},
                {"label": "sender_id", "type": "string"},
                {"label": "recipient_id", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "timestamp", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[FBMessageTriggerProperties]:
        return FBMessageTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # `input_data` carries the synthesized trigger payload from
        # MetaService.receive_webhook: { object, field, target_id, value }.
        # `value` for `messaging.text` is the single entry from Meta's
        # `messaging[]` array — sender / recipient / message blocks.
        value = input_data.get("value") or {}
        message = value.get("message") or {}
        text = str(message.get("text") or "")

        keyword = (self.props.keyword or "").strip()
        if keyword and keyword.lower() not in text.lower():
            return NodeResult(success=True, output_data={"skipped": "keyword mismatch"})

        sender = value.get("sender") or {}
        recipient = value.get("recipient") or {}

        return NodeResult(
            success=True,
            output_data={
                "message_id": str(message.get("mid") or ""),
                "sender_id": str(sender.get("id") or ""),
                "recipient_id": str(recipient.get("id") or ""),
                "text": text,
                "timestamp": str(value.get("timestamp") or ""),
                "payload": value,
            },
        )
