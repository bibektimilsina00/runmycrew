from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class IGMentionTriggerProperties(BaseModel):
    ig_account_id: str = ""


class IGMentionTriggerNode(BaseNode[IGMentionTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.ig_mention",
            name="Instagram Mention",
            category="trigger",
            description=(
                "Fires when another user @mentions you in a public Instagram "
                "post or comment. Use to drive engagement / acknowledgement flows."
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
                {"label": "media_id", "type": "string"},
                {"label": "comment_id", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[IGMentionTriggerProperties]:
        return IGMentionTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        return NodeResult(
            success=True,
            output_data={
                "media_id": str(value.get("media_id") or ""),
                "comment_id": str(value.get("comment_id") or ""),
                "received_at": str(input_data.get("received_at") or ""),
                "payload": value,
            },
        )
