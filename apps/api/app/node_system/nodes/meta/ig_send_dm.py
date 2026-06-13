from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class IGSendDMProperties(BaseModel):
    credential: str | None = None
    ig_account_id: str = ""
    recipient_id: str = ""  # IGSID — usually fed from the upstream trigger's `from_id`
    message: str = ""


class IGSendDMNode(BaseNode[IGSendDMProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.ig_send_dm",
            name="Send Instagram DM",
            category="action",
            description=(
                "Send a direct message from an Instagram Business account. "
                "Subject to Meta's 24-hour messaging window — outside that "
                "window the API rejects the send."
            ),
            icon="Send",
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
                    "dependsOn": "credential",
                    "required": True,
                },
                {
                    "name": "recipient_id",
                    "label": "Recipient IGSID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $node('IG Comment').from_id }}",
                    "description": (
                        "Instagram scoped user id of the recipient. From a "
                        "comment trigger, use the upstream `from_id` output."
                    ),
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                    "placeholder": "Thanks for commenting! Here's the link: ...",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "message_id", "type": "string"},
                {"label": "recipient_id", "type": "string"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[IGSendDMProperties]:
        return IGSendDMProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")

        cred_id = (self.props.credential or "").strip()
        ig_account_id = (self.props.ig_account_id or "").strip()
        recipient_id = (self.props.recipient_id or "").strip()
        message = self.props.message or ""

        if not ig_account_id:
            return NodeResult(success=False, error="ig_account_id is required")
        if not recipient_id:
            return NodeResult(success=False, error="recipient_id is required")
        if not message.strip():
            return NodeResult(success=False, error="message is required")

        credentials = context.credentials or []
        credential = None
        if cred_id:
            credential = next((c for c in credentials if str(c.get("id")) == cred_id), None)
        if credential is None:
            credential = next((c for c in credentials if c.get("type") == "meta_oauth"), None)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")

        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")

        # Find the page-access-token by IG business account id. The OAuth
        # callback enriches each page with `instagram_business_account.{id}`
        # so this lookup is in-memory — no extra Graph call.
        pages = data.get("pages")
        page_token: str | None = None
        if isinstance(pages, list):
            for page in pages:
                if not isinstance(page, dict):
                    continue
                ig = page.get("instagram_business_account") or {}
                if str(ig.get("id") or "") == ig_account_id:
                    token = page.get("access_token")
                    if isinstance(token, str) and token:
                        page_token = token
                    break
        if not page_token:
            return NodeResult(
                success=False,
                error=(
                    "No page access token found for this Instagram account. "
                    "Reconnect the Meta credential to refresh page tokens."
                ),
            )

        service = MetaService(context.db)
        try:
            response = await service.ig_send_dm(
                page_access_token=page_token,
                ig_user_id=ig_account_id,
                recipient_id=recipient_id,
                text=message,
            )
        except Exception as exc:  # noqa: BLE001 — surface the Graph error verbatim
            return NodeResult(success=False, error=str(exc))

        return NodeResult(
            success=True,
            output_data={
                "message_id": str(response.get("message_id") or ""),
                "recipient_id": recipient_id,
                "response": response,
            },
        )
