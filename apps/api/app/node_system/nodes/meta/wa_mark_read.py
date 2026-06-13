from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import find_credential


class WAMarkReadProperties(BaseModel):
    credential: str | None = None
    phone_number_id: str = ""
    message_id: str = ""  # wamid... — surfaced by the WA message trigger


class WAMarkReadNode(BaseNode[WAMarkReadProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.wa_mark_read",
            name="Mark WhatsApp Message Read",
            category="action",
            description=(
                "Mark an inbound WhatsApp message as read (surfaces the blue "
                "double check in the recipient's app). Useful as the first "
                "node in an automated reply flow."
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
                    "name": "phone_number_id",
                    "label": "Sender Phone Number",
                    "type": "meta-resource",
                    "resourceKind": "waba_phone",
                    "dependsOn": "credential",
                    "required": True,
                },
                {
                    "name": "message_id",
                    "label": "Inbound Message ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $node('WhatsApp Message').message_id }}",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "success", "type": "boolean"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[WAMarkReadProperties]:
        return WAMarkReadProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")
        if not self.props.phone_number_id:
            return NodeResult(success=False, error="phone_number_id is required")
        if not self.props.message_id:
            return NodeResult(success=False, error="message_id is required")

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
            resp = await service.wa_mark_read(
                access_token=access_token,
                phone_number_id=self.props.phone_number_id,
                message_id=self.props.message_id,
            )
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))
        return NodeResult(
            success=True,
            output_data={"success": bool(resp.get("success", True)), "response": resp},
        )
