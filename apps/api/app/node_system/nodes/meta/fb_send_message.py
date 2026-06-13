from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

# Meta's allowed message tags for Messenger sends outside the 24h window.
# Source: https://developers.facebook.com/docs/messenger-platform/send-messages/message-tags
_ALLOWED_TAGS = {
    "HUMAN_AGENT",
    "CONFIRMED_EVENT_UPDATE",
    "POST_PURCHASE_UPDATE",
    "ACCOUNT_UPDATE",
}


class FBSendMessageProperties(BaseModel):
    credential: str | None = None
    page_id: str = ""
    recipient_id: str = ""  # PSID — usually fed from the upstream trigger's `sender_id`
    message: str = ""
    # 'RESPONSE'   — default; valid only within the 24h window
    # 'UPDATE'     — transactional updates (order status, etc.)
    # 'MESSAGE_TAG'— outside-window send paired with `message_tag`
    messaging_type: str = "RESPONSE"
    message_tag: str | None = None


class FBSendMessageNode(BaseNode[FBSendMessageProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.fb_send_message",
            name="Send Messenger Message",
            category="action",
            description=(
                "Send a Messenger DM from the connected Facebook Page. "
                "Subject to Meta's 24h messaging window unless a valid "
                "message tag is supplied."
            ),
            icon="Send",
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
                    "name": "recipient_id",
                    "label": "Recipient PSID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $node('Messenger DM').sender_id }}",
                    "description": (
                        "Page-scoped user id of the recipient. From a Messenger "
                        "trigger, use the upstream `sender_id` output."
                    ),
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                    "placeholder": "Thanks for reaching out!",
                },
                {
                    "name": "messaging_type",
                    "label": "Messaging Type",
                    "type": "options",
                    "default": "RESPONSE",
                    "options": [
                        {"label": "Response (within 24h)", "value": "RESPONSE"},
                        {"label": "Update (transactional)", "value": "UPDATE"},
                        {"label": "Message Tag (outside 24h)", "value": "MESSAGE_TAG"},
                    ],
                },
                {
                    "name": "message_tag",
                    "label": "Message Tag",
                    "type": "options",
                    "default": None,
                    "options": [
                        {"label": "Human Agent", "value": "HUMAN_AGENT"},
                        {"label": "Confirmed Event Update", "value": "CONFIRMED_EVENT_UPDATE"},
                        {"label": "Post-Purchase Update", "value": "POST_PURCHASE_UPDATE"},
                        {"label": "Account Update", "value": "ACCOUNT_UPDATE"},
                    ],
                    "condition": {"field": "messaging_type", "value": "MESSAGE_TAG"},
                    "description": "Required when sending outside the 24h window.",
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
    def get_properties_model(cls) -> type[FBSendMessageProperties]:
        return FBSendMessageProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")

        cred_id = (self.props.credential or "").strip()
        page_id = (self.props.page_id or "").strip()
        recipient_id = (self.props.recipient_id or "").strip()
        message = self.props.message or ""
        messaging_type = self.props.messaging_type or "RESPONSE"
        tag = self.props.message_tag

        if not page_id:
            return NodeResult(success=False, error="page_id is required")
        if not recipient_id:
            return NodeResult(success=False, error="recipient_id is required")
        if not message.strip():
            return NodeResult(success=False, error="message is required")

        # Local guard: if the user picked MESSAGE_TAG mode, refuse to send
        # without a valid tag. Meta would reject this with a less friendly
        # error 100; this is a faster, more readable failure.
        if messaging_type == "MESSAGE_TAG" and (not tag or tag not in _ALLOWED_TAGS):
            return NodeResult(
                success=False,
                error=(
                    "messaging_type=MESSAGE_TAG requires a valid message_tag "
                    f"({sorted(_ALLOWED_TAGS)})."
                ),
            )

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

        # Find the page-access token by Page id. The OAuth callback stores
        # one entry per Page the user manages; the page token is the
        # non-expiring access_token on that entry.
        pages = data.get("pages")
        page_token: str | None = None
        if isinstance(pages, list):
            for page in pages:
                if not isinstance(page, dict):
                    continue
                if str(page.get("id") or "") == page_id:
                    token = page.get("access_token")
                    if isinstance(token, str) and token:
                        page_token = token
                    break
        if not page_token:
            return NodeResult(
                success=False,
                error=(
                    "No page access token found for this Page. "
                    "Reconnect the Meta credential to refresh page tokens."
                ),
            )

        service = MetaService(context.db)
        try:
            response = await service.fb_send_message(
                page_access_token=page_token,
                page_id=page_id,
                recipient_id=recipient_id,
                text=message,
                messaging_type=messaging_type,
                message_tag=tag,
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
