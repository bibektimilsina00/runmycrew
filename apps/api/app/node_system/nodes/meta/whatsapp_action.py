"""Consolidated WhatsApp action node.

Replaces `wa_send_message`, `wa_send_template`, and `wa_mark_read` with
`action.meta.whatsapp` carrying an `operation` dropdown.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import find_credential

WA_ACTION_OPS: tuple[str, ...] = ("send_text", "send_template", "mark_read")


class WhatsAppActionProperties(BaseModel):
    credential: str | None = None
    operation: str = "send_text"
    phone_number_id: str = ""

    # send_text
    to: str = ""
    message: str = ""
    preview_url: bool = False
    reply_to_message_id: str | None = None

    # send_template
    waba_id: str = ""
    template_name: str = ""
    language_code: str = "en_US"
    body_variables: list[str] | None = None

    # mark_read
    message_id: str = ""


class WhatsAppActionNode(BaseNode[WhatsAppActionProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        cond_send_text = {"field": "operation", "value": "send_text"}
        cond_send_template = {"field": "operation", "value": "send_template"}
        cond_mark_read = {"field": "operation", "value": "mark_read"}

        return NodeMetadata(
            type="action.meta.whatsapp",
            name="WhatsApp",
            category="action",
            description=(
                "Send free-form text messages, pre-approved templates, or "
                "mark inbound WhatsApp messages as read."
            ),
            icon="MessageSquare",
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
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "send_text",
                    "options": [
                        {"label": "Send Text", "value": "send_text"},
                        {"label": "Send Template", "value": "send_template"},
                        {"label": "Mark as Read", "value": "mark_read"},
                    ],
                },
                # ── shared by send_text + send_template ──────────────
                {
                    "name": "to",
                    "label": "Recipient (E.164, no +)",
                    "type": "string",
                    "required": True,
                    "placeholder": "15551234567",
                    "condition": {
                        "field": "operation",
                        "value": ["send_text", "send_template"],
                    },
                },
                # ── send_text ─────────────────────────────────────────
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                    "condition": cond_send_text,
                },
                {
                    "name": "preview_url",
                    "label": "Preview Links",
                    "type": "boolean",
                    "default": False,
                    "condition": cond_send_text,
                },
                {
                    "name": "reply_to_message_id",
                    "label": "Reply To (wamid, optional)",
                    "type": "string",
                    "condition": cond_send_text,
                },
                # ── send_template ────────────────────────────────────
                {
                    "name": "waba_id",
                    "label": "WhatsApp Business Account",
                    "type": "meta-resource",
                    "resourceKind": "waba",
                    "dependsOn": ["credential"],
                    "required": True,
                    "condition": cond_send_template,
                },
                {
                    "name": "template_name",
                    "label": "Template",
                    "type": "wa-template",
                    "dependsOn": ["credential", "waba_id"],
                    "required": True,
                    "condition": cond_send_template,
                },
                {
                    "name": "language_code",
                    "label": "Language",
                    "type": "string",
                    "default": "en_US",
                    "placeholder": "en_US",
                    "condition": cond_send_template,
                },
                {
                    "name": "body_variables",
                    "label": "Body Variables (positional)",
                    "type": "json",
                    "description": "Array of strings substituted for {{1}}, {{2}}, ...",
                    "condition": cond_send_template,
                },
                # ── mark_read ────────────────────────────────────────
                {
                    "name": "message_id",
                    "label": "Inbound Message ID (wamid)",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $step.message_id }}",
                    "condition": cond_mark_read,
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "operation", "type": "string"},
                {"label": "id", "type": "string"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[WhatsAppActionProperties]:
        return WhatsAppActionProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")

        op = (self.props.operation or "").strip()
        if op not in WA_ACTION_OPS:
            return NodeResult(
                success=False,
                error=f"Unsupported operation '{op}' (expected one of {list(WA_ACTION_OPS)})",
            )

        phone_number_id = (self.props.phone_number_id or "").strip()
        if not phone_number_id:
            return NodeResult(success=False, error="phone_number_id is required")

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
            if op == "send_text":
                return await self._send_text(service, access_token, phone_number_id)
            if op == "send_template":
                return await self._send_template(service, access_token, phone_number_id)
            # mark_read
            return await self._mark_read(service, access_token, phone_number_id)
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))

    async def _send_text(
        self,
        service: MetaService,
        access_token: str,
        phone_number_id: str,
    ) -> NodeResult:
        to = (self.props.to or "").strip().lstrip("+")
        message = self.props.message or ""
        if not to:
            return NodeResult(success=False, error="to is required")
        if not message.strip():
            return NodeResult(success=False, error="message is required")

        resp = await service.wa_send_text(
            access_token=access_token,
            phone_number_id=phone_number_id,
            to=to,
            text=message,
            preview_url=bool(self.props.preview_url),
            reply_to_message_id=self.props.reply_to_message_id or None,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "send_text",
                "id": _wa_message_id(resp),
                "response": resp,
            },
        )

    async def _send_template(
        self,
        service: MetaService,
        access_token: str,
        phone_number_id: str,
    ) -> NodeResult:
        to = (self.props.to or "").strip().lstrip("+")
        template_name = (self.props.template_name or "").strip()
        if not to:
            return NodeResult(success=False, error="to is required")
        if not template_name:
            return NodeResult(success=False, error="template_name is required")

        resp = await service.wa_send_template(
            access_token=access_token,
            phone_number_id=phone_number_id,
            to=to,
            template_name=template_name,
            language_code=self.props.language_code or "en_US",
            body_variables=self.props.body_variables,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "send_template",
                "id": _wa_message_id(resp),
                "response": resp,
            },
        )

    async def _mark_read(
        self,
        service: MetaService,
        access_token: str,
        phone_number_id: str,
    ) -> NodeResult:
        message_id = (self.props.message_id or "").strip()
        if not message_id:
            return NodeResult(success=False, error="message_id is required")

        resp = await service.wa_mark_read(
            access_token=access_token,
            phone_number_id=phone_number_id,
            message_id=message_id,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "mark_read",
                "id": message_id,
                "response": resp,
            },
        )


def _wa_message_id(resp: dict[str, Any]) -> str:
    """WhatsApp returns the new message id under `messages[0].id`."""
    messages = resp.get("messages") or []
    if isinstance(messages, list) and messages and isinstance(messages[0], dict):
        return str(messages[0].get("id") or "")
    return ""
