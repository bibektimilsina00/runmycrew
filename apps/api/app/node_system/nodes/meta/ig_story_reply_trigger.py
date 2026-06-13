from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class IGStoryReplyTriggerProperties(BaseModel):
    ig_account_id: str = ""


class IGStoryReplyTriggerNode(BaseNode[IGStoryReplyTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.ig_story_reply",
            name="Instagram Story Reply",
            category="trigger",
            description=(
                "Fires when a user replies to one of your Instagram stories. "
                "Reply text + the original story id are surfaced for downstream nodes."
            ),
            icon="MessageSquare",
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
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "message_id", "type": "string"},
                {"label": "sender_id", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "story_id", "type": "string"},
                {"label": "timestamp", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[IGStoryReplyTriggerProperties]:
        return IGStoryReplyTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        message = value.get("message") or {}
        reply_to = message.get("reply_to") or {}
        story = reply_to.get("story") or {}
        sender = value.get("sender") or {}

        return NodeResult(
            success=True,
            output_data={
                "message_id": str(message.get("mid") or ""),
                "sender_id": str(sender.get("id") or ""),
                "text": str(message.get("text") or ""),
                "story_id": str(story.get("id") or ""),
                "timestamp": str(value.get("timestamp") or ""),
                "payload": value,
            },
        )
