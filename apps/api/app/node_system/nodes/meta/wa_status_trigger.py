from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class WAStatusTriggerProperties(BaseModel):
    waba_id: str = ""
    phone_number_id: str | None = Field(
        default=None,
        description="Optional — only fire for this WhatsApp phone number id.",
    )
    status: str | None = Field(
        default=None,
        description="Optional filter on status value: sent / delivered / read / failed.",
    )


class WAStatusTriggerNode(BaseNode[WAStatusTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.wa_status",
            name="WhatsApp Message Status",
            category="trigger",
            description=(
                "Fires when Meta delivers a status callback for a WhatsApp "
                "message you sent: sent / delivered / read / failed. Use "
                "to drive deliverability dashboards, retries, or read-receipts."
            ),
            icon="CheckCheck",
            color="#25D366",
            properties=[
                {
                    "name": "credential",
                    "label": "Meta Account",
                    "type": "credential",
                    "credentialType": "meta_oauth",
                    "required": True,
                },
                {
                    "name": "waba_id",
                    "label": "WhatsApp Business Account",
                    "type": "meta-resource",
                    "resourceKind": "waba",
                    "dependsOn": ["credential"],
                    "required": True,
                },
                {
                    "name": "phone_number_id",
                    "label": "Phone number (optional)",
                    "type": "meta-resource",
                    "resourceKind": "waba_phone",
                    "dependsOn": ["credential"],
                },
                {
                    "name": "status",
                    "label": "Status filter (optional)",
                    "type": "options",
                    "default": None,
                    "options": [
                        {"label": "Any", "value": None},
                        {"label": "Sent", "value": "sent"},
                        {"label": "Delivered", "value": "delivered"},
                        {"label": "Read", "value": "read"},
                        {"label": "Failed", "value": "failed"},
                    ],
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "message_id", "type": "string"},
                {"label": "recipient_id", "type": "string"},
                {"label": "status", "type": "string"},
                {"label": "phone_number_id", "type": "string"},
                {"label": "timestamp", "type": "string"},
                {"label": "conversation_id", "type": "string"},
                {"label": "pricing_category", "type": "string"},
                {"label": "errors", "type": "array"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[WAStatusTriggerProperties]:
        return WAStatusTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        status_event = value.get("_event") or {}
        metadata = value.get("metadata") or {}

        phone_id_actual = str(metadata.get("phone_number_id") or "")
        phone_id_filter = (self.props.phone_number_id or "").strip()
        if phone_id_filter and phone_id_actual != phone_id_filter:
            return NodeResult(success=True, output_data={"skipped": "phone_number_id mismatch"})

        status_actual = str(status_event.get("status") or "").lower()
        status_filter = (self.props.status or "").strip().lower()
        if status_filter and status_filter != status_actual:
            return NodeResult(success=True, output_data={"skipped": "status mismatch"})

        conversation = status_event.get("conversation") or {}
        pricing = status_event.get("pricing") or {}

        return NodeResult(
            success=True,
            output_data={
                "message_id": str(status_event.get("id") or ""),
                "recipient_id": str(status_event.get("recipient_id") or ""),
                "status": status_actual,
                "phone_number_id": phone_id_actual,
                "timestamp": str(status_event.get("timestamp") or ""),
                "conversation_id": str(conversation.get("id") or ""),
                "pricing_category": str(pricing.get("category") or ""),
                "errors": status_event.get("errors") or [],
                "payload": status_event,
            },
        )
