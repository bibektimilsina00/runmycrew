from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import find_credential


class WASendMessageProperties(BaseModel):
    credential: str | None = None
    phone_number_id: str = ""  # WA Cloud API phone-number id (the sender)
    to: str = ""  # recipient — E.164 phone number, no leading `+`
    message: str = ""
    preview_url: bool = False
    reply_to_message_id: str | None = None


class WASendMessageNode(BaseNode[WASendMessageProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.wa_send_message",
            name="Send WhatsApp Message",
            category="action",
            description=(
                "Send a free-form WhatsApp text message. Valid only within "
                "the 24-hour customer-service window since the recipient's "
                "last inbound message. For outside-window sends, use a "
                "pre-approved template via `action.meta.wa_send_template`."
            ),
            icon="Send",
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
                    "name": "phone_number_id",
                    "label": "Sender Phone Number",
                    "type": "meta-resource",
                    "resourceKind": "waba_phone",
                    "dependsOn": ["credential"],
                    "required": True,
                },
                {
                    "name": "to",
                    "label": "Recipient Phone (E.164)",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $node('WhatsApp Message').from }}",
                    "description": (
                        "International phone number with country code, no "
                        "leading `+` — e.g. 15551234567. Use the trigger's "
                        "`from` output to reply to the inbound sender."
                    ),
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                },
                {
                    "name": "preview_url",
                    "label": "Show link preview",
                    "type": "boolean",
                    "default": False,
                    "description": "When the message contains a URL, render a preview card.",
                },
                {
                    "name": "reply_to_message_id",
                    "label": "Reply to message ID (optional)",
                    "type": "string",
                    "advanced": True,
                    "placeholder": "wamid.HBgL...",
                    "description": "Thread the response as a reply to a specific inbound message.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "message_id", "type": "string"},
                {"label": "to", "type": "string"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[WASendMessageProperties]:
        return WASendMessageProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")
        if not self.props.phone_number_id:
            return NodeResult(success=False, error="phone_number_id is required")
        if not self.props.to.strip():
            return NodeResult(success=False, error="to is required")
        if not self.props.message.strip():
            return NodeResult(success=False, error="message is required")

        credential = find_credential(context.credentials, self.props.credential)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")
        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")

        access_token = str(data.get("access_token") or "")
        if not access_token:
            return NodeResult(
                success=False,
                error="Meta credential is missing access_token. Reconnect the Meta credential.",
            )

        service = MetaService(context.db)
        try:
            resp = await service.wa_send_text(
                access_token=access_token,
                phone_number_id=self.props.phone_number_id,
                to=self.props.to.strip().lstrip("+"),
                text=self.props.message,
                preview_url=bool(self.props.preview_url),
                reply_to_message_id=self.props.reply_to_message_id or None,
            )
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))

        # WA returns: {"messaging_product":"whatsapp","contacts":[{...}],
        #              "messages":[{"id":"wamid.HB..."}]}
        messages = resp.get("messages") or []
        message_id = ""
        if isinstance(messages, list) and messages and isinstance(messages[0], dict):
            message_id = str(messages[0].get("id") or "")

        return NodeResult(
            success=True,
            output_data={
                "message_id": message_id,
                "to": self.props.to,
                "response": resp,
            },
        )
