from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class IGStoryMentionTriggerProperties(BaseModel):
    ig_account_id: str = ""


class IGStoryMentionTriggerNode(BaseNode[IGStoryMentionTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.ig_story_mention",
            name="Instagram Story Mention",
            category="trigger",
            description=(
                "Fires when another user @mentions you in their Instagram "
                "story. Surfaces the mention's media URL so workflows can "
                "thank, reshare, or DM the mentioner."
            ),
            icon="AtSign",
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
                {"label": "attachment_url", "type": "string"},
                {"label": "timestamp", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[IGStoryMentionTriggerProperties]:
        return IGStoryMentionTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        message = value.get("message") or {}
        attachments = message.get("attachments") or []
        sender = value.get("sender") or {}

        attachment_url = ""
        if isinstance(attachments, list):
            for att in attachments:
                if isinstance(att, dict) and str(att.get("type") or "") == "story_mention":
                    payload = att.get("payload") or {}
                    if isinstance(payload, dict):
                        attachment_url = str(payload.get("url") or "")
                        break

        return NodeResult(
            success=True,
            output_data={
                "message_id": str(message.get("mid") or ""),
                "sender_id": str(sender.get("id") or ""),
                "attachment_url": attachment_url,
                "timestamp": str(value.get("timestamp") or ""),
                "payload": value,
            },
        )
