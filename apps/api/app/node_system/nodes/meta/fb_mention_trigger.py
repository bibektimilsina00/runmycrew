from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class FBMentionTriggerProperties(BaseModel):
    page_id: str = ""


class FBMentionTriggerNode(BaseNode[FBMentionTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.fb_mention",
            name="Facebook Page Mention",
            category="trigger",
            description=(
                "Fires when another Page or user mentions the connected "
                "Facebook Page in a public post or comment."
            ),
            icon="AtSign",
            color="#1877F2",
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
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "post_id", "type": "string"},
                {"label": "sender_id", "type": "string"},
                {"label": "sender_name", "type": "string"},
                {"label": "message", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[FBMentionTriggerProperties]:
        return FBMentionTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        sender = value.get("sender") or value.get("from") or {}
        return NodeResult(
            success=True,
            output_data={
                "post_id": str(value.get("post_id") or ""),
                "sender_id": str(sender.get("id") or ""),
                "sender_name": str(sender.get("name") or ""),
                "message": str(value.get("message") or ""),
                "received_at": str(input_data.get("received_at") or ""),
                "payload": value,
            },
        )
