from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class FBPostbackTriggerProperties(BaseModel):
    page_id: str = ""
    payload_filter: str | None = Field(
        default=None,
        description="Optional exact-match filter on the postback payload string.",
    )


class FBPostbackTriggerNode(BaseNode[FBPostbackTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.fb_postback",
            name="Messenger Button Click",
            category="trigger",
            description=(
                "Fires when a user taps a Messenger button (postback) or "
                "selects a quick-reply on the connected Page."
            ),
            icon="MousePointerClick",
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
                    "name": "payload_filter",
                    "label": "Payload filter (optional)",
                    "type": "string",
                    "placeholder": "MAIN_MENU",
                    "description": "Exact match on the postback's payload string.",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "sender_id", "type": "string"},
                {"label": "title", "type": "string"},
                {"label": "postback_payload", "type": "string"},
                {"label": "referrer", "type": "object"},
                {"label": "timestamp", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[FBPostbackTriggerProperties]:
        return FBPostbackTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        postback = value.get("postback") or {}
        sender = value.get("sender") or {}
        payload_str = str(postback.get("payload") or "")

        wanted = (self.props.payload_filter or "").strip()
        if wanted and wanted != payload_str:
            return NodeResult(success=True, output_data={"skipped": "payload mismatch"})

        return NodeResult(
            success=True,
            output_data={
                "sender_id": str(sender.get("id") or ""),
                "title": str(postback.get("title") or ""),
                "postback_payload": payload_str,
                "referrer": postback.get("referral") or {},
                "timestamp": str(value.get("timestamp") or ""),
                "payload": value,
            },
        )
