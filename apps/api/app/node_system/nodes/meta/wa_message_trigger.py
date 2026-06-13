from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class WAMessageTriggerProperties(BaseModel):
    # Selected via `meta-resource` (kind=waba). Same as Meta's `entry.id`
    # for `object: whatsapp_business_account` deliveries — what
    # MetaService routing filters on via `waba_id` in _target_filters.
    waba_id: str = ""
    # Optional per-number filter so one workflow can listen on one phone
    # even when the WABA owns several.
    phone_number_id: str | None = Field(
        default=None,
        description="Optional — only fire for this WhatsApp phone number id.",
    )
    keyword: str | None = Field(
        default=None,
        description="Optional case-insensitive substring filter on text body.",
    )


class WAMessageTriggerNode(BaseNode[WAMessageTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.wa_message",
            name="WhatsApp Message",
            category="trigger",
            description=(
                "Fires when a user sends a WhatsApp message to one of the "
                "phone numbers under the connected WhatsApp Business "
                "Account. Powers customer-support flows."
            ),
            icon="MessageCircle",
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
                    "description": "Only fire for this specific WhatsApp number.",
                },
                {
                    "name": "keyword",
                    "label": "Keyword filter (optional)",
                    "type": "string",
                    "placeholder": "STOP",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "message_id", "type": "string"},
                {"label": "from", "type": "string"},
                {"label": "phone_number_id", "type": "string"},
                {"label": "display_phone_number", "type": "string"},
                {"label": "type", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "timestamp", "type": "string"},
                {"label": "contact_name", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[WAMessageTriggerProperties]:
        return WAMessageTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # MetaService._flatten_entry forks one trigger event per inbound
        # message, embedding the original message under `_event` so the
        # surrounding metadata (display_phone_number, contacts) stays
        # adjacent. See service.py for the envelope shape.
        value = input_data.get("value") or {}
        msg = value.get("_event") or {}
        metadata = value.get("metadata") or {}
        contacts = value.get("contacts") or []

        phone_id_actual = str(metadata.get("phone_number_id") or "")
        phone_id_filter = (self.props.phone_number_id or "").strip()
        if phone_id_filter and phone_id_actual != phone_id_filter:
            return NodeResult(success=True, output_data={"skipped": "phone_number_id mismatch"})

        msg_type = str(msg.get("type") or "")
        text = ""
        if msg_type == "text":
            text = str((msg.get("text") or {}).get("body") or "")
        elif msg_type == "button":
            text = str((msg.get("button") or {}).get("text") or "")
        elif msg_type == "interactive":
            inter = msg.get("interactive") or {}
            text = str(
                (inter.get("button_reply") or {}).get("title")
                or (inter.get("list_reply") or {}).get("title")
                or ""
            )

        keyword = (self.props.keyword or "").strip()
        if keyword and keyword.lower() not in text.lower():
            return NodeResult(success=True, output_data={"skipped": "keyword mismatch"})

        first_contact = contacts[0] if isinstance(contacts, list) and contacts else {}
        profile = (first_contact or {}).get("profile") or {}

        return NodeResult(
            success=True,
            output_data={
                "message_id": str(msg.get("id") or ""),
                "from": str(msg.get("from") or ""),
                "phone_number_id": phone_id_actual,
                "display_phone_number": str(metadata.get("display_phone_number") or ""),
                "type": msg_type,
                "text": text,
                "timestamp": str(msg.get("timestamp") or ""),
                "contact_name": str(profile.get("name") or ""),
                "payload": msg,
            },
        )
