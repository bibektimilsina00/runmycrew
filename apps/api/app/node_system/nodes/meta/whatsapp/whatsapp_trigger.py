"""Consolidated WhatsApp trigger.

Replaces `wa_message` and `wa_status` with a single
`trigger.meta.whatsapp` node carrying an `event_type` dropdown.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import require_webhook_payload

WA_EVENT_TYPES: tuple[str, ...] = ("message", "status")


class WhatsAppTriggerProperties(BaseModel):
    event_type: str = "message"
    waba_id: str = ""
    credential: str | None = None

    phone_number_id: str | None = Field(default=None)
    keyword: str | None = Field(default=None)
    status: str | None = Field(default=None)


class WhatsAppTriggerNode(BaseNode[WhatsAppTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.whatsapp",
            name="WhatsApp",
            category="trigger",
            description=(
                "Fires when WhatsApp delivers an inbound message or a status "
                "callback (sent / delivered / read / failed)."
            ),
            icon="whatsapp",
            color="#ffffff",
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
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": "message",
                    "options": [
                        {"label": "Inbound Message", "value": "message"},
                        {"label": "Message Status", "value": "status"},
                    ],
                },
                {
                    "name": "phone_number_id",
                    "label": "Phone Number (optional)",
                    "type": "meta-resource",
                    "resourceKind": "waba_phone",
                    "dependsOn": ["credential"],
                    "description": "Only fire for this phone number id.",
                },
                {
                    "name": "keyword",
                    "label": "Keyword filter (optional)",
                    "type": "string",
                    "placeholder": "BUY",
                    "description": "Case-insensitive substring match on text.",
                    "condition": {"field": "event_type", "value": "message"},
                },
                {
                    "name": "status",
                    "label": "Status Filter",
                    "type": "options",
                    "default": "",
                    "options": [
                        {"label": "Any", "value": ""},
                        {"label": "Sent", "value": "sent"},
                        {"label": "Delivered", "value": "delivered"},
                        {"label": "Read", "value": "read"},
                        {"label": "Failed", "value": "failed"},
                    ],
                    "condition": {"field": "event_type", "value": "status"},
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "event_type", "type": "string"},
                {"label": "message_id", "type": "string"},
                {"label": "from", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "phone_number_id", "type": "string"},
                {"label": "status", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[WhatsAppTriggerProperties]:
        return WhatsAppTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        guard = require_webhook_payload(input_data, trigger_label="WhatsApp")
        if guard is not None:
            return guard

        event_type = (self.props.event_type or "").strip()
        if event_type not in WA_EVENT_TYPES:
            return NodeResult(
                success=False,
                error=f"Unsupported event_type '{event_type}' (expected one of {list(WA_EVENT_TYPES)})",
            )

        value = input_data.get("value") or {}
        received_at = str(input_data.get("received_at") or "")
        metadata = value.get("metadata") or {}
        phone_id_actual = str(metadata.get("phone_number_id") or "")

        phone_filter = (self.props.phone_number_id or "").strip()
        if phone_filter and phone_filter != phone_id_actual:
            return NodeResult(success=True, output_data={"skipped": "phone_number_id mismatch"})

        if event_type == "message":
            return self._emit_message(value, received_at, phone_id_actual)
        # status
        return self._emit_status(value, received_at, phone_id_actual)

    def _emit_message(
        self, value: dict[str, Any], received_at: str, phone_id_actual: str
    ) -> NodeResult:
        event = value.get("_event") or {}
        text_field = event.get("text") or {}
        text = str(text_field.get("body") or "")

        keyword = (self.props.keyword or "").strip()
        if keyword and keyword.lower() not in text.lower():
            return NodeResult(success=True, output_data={"skipped": "keyword mismatch"})

        return NodeResult(
            success=True,
            output_data={
                "event_type": "message",
                "message_id": str(event.get("id") or ""),
                "from": str(event.get("from") or ""),
                "text": text,
                "phone_number_id": phone_id_actual,
                "timestamp": str(event.get("timestamp") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _emit_status(
        self, value: dict[str, Any], received_at: str, phone_id_actual: str
    ) -> NodeResult:
        event = value.get("_event") or {}
        status_actual = str(event.get("status") or "").lower()

        wanted = (self.props.status or "").strip().lower()
        if wanted and wanted != status_actual:
            return NodeResult(success=True, output_data={"skipped": "status mismatch"})

        return NodeResult(
            success=True,
            output_data={
                "event_type": "status",
                "message_id": str(event.get("id") or ""),
                "status": status_actual,
                "recipient_id": str(event.get("recipient_id") or ""),
                "phone_number_id": phone_id_actual,
                "timestamp": str(event.get("timestamp") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )
