from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import find_credential


class WASendTemplateProperties(BaseModel):
    credential: str | None = None
    waba_id: str = ""  # picks the template list scope
    phone_number_id: str = ""  # sender
    to: str = ""  # recipient — E.164, no leading +
    template_name: str = ""  # from the wa-template field
    language_code: str = "en_US"
    body_variables: list[str] | None = None


class WASendTemplateNode(BaseNode[WASendTemplateProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.wa_send_template",
            name="Send WhatsApp Template",
            category="action",
            description=(
                "Send a pre-approved WhatsApp template message. Templates "
                "are the only way to reach a user OUTSIDE the 24-hour "
                "customer-service window. Each template must be registered "
                "and APPROVED in the WABA dashboard before this node can "
                "use it."
            ),
            icon="FileText",
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
                    "placeholder": "15551234567",
                },
                {
                    "name": "template_name",
                    "label": "Template",
                    "type": "wa-template",
                    "dependsOn": ["credential", "waba_id"],
                    "required": True,
                    "description": (
                        "Only APPROVED templates can be sent. PENDING / "
                        "REJECTED entries show in the picker for visibility "
                        "but won't be accepted by Meta at send time."
                    ),
                },
                {
                    "name": "language_code",
                    "label": "Language",
                    "type": "string",
                    "default": "en_US",
                    "placeholder": "en_US",
                    "description": "Locale code, e.g. en_US, es, pt_BR.",
                },
                {
                    "name": "body_variables",
                    "label": "Body variables",
                    "type": "list",
                    "description": (
                        "Positional values substituted into the template's "
                        "{{1}}, {{2}}, ... body placeholders."
                    ),
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
    def get_properties_model(cls) -> type[WASendTemplateProperties]:
        return WASendTemplateProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")
        if not self.props.phone_number_id:
            return NodeResult(success=False, error="phone_number_id is required")
        if not self.props.template_name:
            return NodeResult(success=False, error="template_name is required")
        if not self.props.to.strip():
            return NodeResult(success=False, error="to is required")

        credential = find_credential(context.credentials, self.props.credential)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")
        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")
        access_token = str(data.get("access_token") or "")
        if not access_token:
            return NodeResult(success=False, error="Meta credential is missing access_token.")

        service = MetaService(context.db)
        try:
            resp = await service.wa_send_template(
                access_token=access_token,
                phone_number_id=self.props.phone_number_id,
                to=self.props.to.strip().lstrip("+"),
                template_name=self.props.template_name,
                language_code=self.props.language_code or "en_US",
                body_variables=self.props.body_variables or [],
            )
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))

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
