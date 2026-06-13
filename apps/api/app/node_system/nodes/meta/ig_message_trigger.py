from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class IGMessageTriggerProperties(BaseModel):
    # Selected via the `meta-resource` field type (kind=ig_account). Matches
    # the Instagram business account id Meta sends as `entry.id` for
    # `object: instagram` messaging deliveries — see MetaService routing
    # via `_target_filters` keyed on `ig_account_id`.
    ig_account_id: str = ""
    keyword: str | None = Field(
        default=None,
        description="Optional case-insensitive substring filter on message text.",
    )


class IGMessageTriggerNode(BaseNode[IGMessageTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.ig_message",
            name="Instagram DM",
            category="trigger",
            description=(
                "Fires when a user sends a DM to the connected Instagram "
                "Business account. Powers inbox automation flows."
            ),
            icon="MessageCircle",
            color="#E1306C",
            properties=[
                {
                    "name": "credential",
                    "label": "Meta Account",
                    "type": "credential",
                    "credentialType": "meta_oauth",
                    "required": True,
                },
                {
                    "name": "ig_account_id",
                    "label": "Instagram Account",
                    "type": "meta-resource",
                    "resourceKind": "ig_account",
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
    def get_properties_model(cls) -> type[IGMessageTriggerProperties]:
        return IGMessageTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
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
