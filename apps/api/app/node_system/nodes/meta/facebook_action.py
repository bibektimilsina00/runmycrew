"""Consolidated Facebook (Page / Messenger) action node.

Replaces `fb_send_message`, `fb_reply_comment`, `fb_publish_post` with
`action.meta.facebook` carrying an `operation` dropdown.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import (
    find_credential,
    page_token_by_page_id,
    resolve_media_field,
)

FB_ACTION_OPS: tuple[str, ...] = ("send_message", "reply_comment", "publish_post")

_VALID_MESSAGING_TYPES = {"RESPONSE", "UPDATE", "MESSAGE_TAG"}
_VALID_MESSAGE_TAGS = {
    "HUMAN_AGENT",
    "CONFIRMED_EVENT_UPDATE",
    "POST_PURCHASE_UPDATE",
    "ACCOUNT_UPDATE",
}


class FacebookActionProperties(BaseModel):
    credential: str | None = None
    page_id: str = ""
    operation: str = "send_message"

    # send_message
    recipient_id: str = ""
    message: str = ""
    messaging_type: str = "RESPONSE"
    message_tag: str | None = None

    # reply_comment
    comment_id: str = ""
    reply_text: str = ""

    # publish_post — text-only, photo, or video. media_url accepts both
    # the legacy plain-URL string and the MediaRenderer's discriminated
    # dict; `resolve_media_field` normalizes it at execute time.
    post_message: str = ""
    link: str | None = None
    media_url: Any = ""
    media_kind: str = "IMAGE"


class FacebookActionNode(BaseNode[FacebookActionProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        cond_send = {"field": "operation", "value": "send_message"}
        cond_reply = {"field": "operation", "value": "reply_comment"}
        cond_publish = {"field": "operation", "value": "publish_post"}

        return NodeMetadata(
            type="action.meta.facebook",
            name="Facebook",
            category="action",
            description=(
                "Send Messenger DMs, reply to Page comments, or publish posts on a Facebook Page."
            ),
            icon="facebook",
            color="#1c1c1c",
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
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "send_message",
                    "options": [
                        {"label": "Send Messenger DM", "value": "send_message"},
                        {"label": "Reply to Comment", "value": "reply_comment"},
                        {"label": "Publish Page Post", "value": "publish_post"},
                    ],
                },
                # ── send_message ─────────────────────────────────────
                {
                    "name": "recipient_id",
                    "label": "Recipient PSID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $step.from_id }}",
                    "condition": cond_send,
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                    "condition": cond_send,
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
                    "condition": cond_send,
                },
                {
                    "name": "message_tag",
                    "label": "Message Tag",
                    "type": "options",
                    "default": "HUMAN_AGENT",
                    "options": [
                        {"label": "Human Agent", "value": "HUMAN_AGENT"},
                        {"label": "Confirmed Event Update", "value": "CONFIRMED_EVENT_UPDATE"},
                        {"label": "Post Purchase Update", "value": "POST_PURCHASE_UPDATE"},
                        {"label": "Account Update", "value": "ACCOUNT_UPDATE"},
                    ],
                    "condition": {
                        "all": [
                            cond_send,
                            {"field": "messaging_type", "value": "MESSAGE_TAG"},
                        ]
                    },
                },
                # ── reply_comment ────────────────────────────────────
                {
                    "name": "comment_id",
                    "label": "Comment ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $step.comment_id }}",
                    "condition": cond_reply,
                },
                {
                    "name": "reply_text",
                    "label": "Reply",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                    "condition": cond_reply,
                },
                # ── publish_post ─────────────────────────────────────
                {
                    "name": "post_message",
                    "label": "Post Body",
                    "type": "string",
                    "required": False,
                    "multiline": True,
                    "description": (
                        "Optional when a media attachment is provided — the "
                        "Page UI requires either text or media (or both)."
                    ),
                    "condition": cond_publish,
                },
                {
                    "name": "media_url",
                    "label": "Media (optional)",
                    "type": "media",
                    "description": (
                        "Attach an image or video. URL, upload, or library — "
                        "same picker as the Instagram action."
                    ),
                    "typeOptions": {
                        "accept": "image/*,video/*",
                        "mediaKindField": "media_kind",
                    },
                    "condition": cond_publish,
                },
                {
                    "name": "media_kind",
                    "label": "Media Type",
                    "type": "options",
                    "default": "IMAGE",
                    "options": [
                        {"label": "Image", "value": "IMAGE"},
                        {"label": "Video", "value": "VIDEO"},
                    ],
                    "condition": cond_publish,
                },
                {
                    "name": "link",
                    "label": "Link (optional)",
                    "type": "string",
                    "placeholder": "https://...",
                    "description": (
                        "Only used for text-only posts. Ignored when a media "
                        "attachment is provided — the media becomes the post."
                    ),
                    "condition": cond_publish,
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
    def get_properties_model(cls) -> type[FacebookActionProperties]:
        return FacebookActionProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")

        op = (self.props.operation or "").strip()
        if op not in FB_ACTION_OPS:
            return NodeResult(
                success=False,
                error=f"Unsupported operation '{op}' (expected one of {list(FB_ACTION_OPS)})",
            )

        page_id = (self.props.page_id or "").strip()
        if not page_id:
            return NodeResult(success=False, error="page_id is required")

        credential = find_credential(context.credentials, self.props.credential)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")
        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")

        token = page_token_by_page_id(data, page_id)
        if not token:
            return NodeResult(success=False, error="No page access token for this Page.")

        service = MetaService(context.db)
        try:
            if op == "send_message":
                return await self._send_message(service, token, page_id)
            if op == "reply_comment":
                return await self._reply_comment(service, token)
            # publish_post
            return await self._publish_post(service, token, page_id)
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))

    async def _send_message(
        self,
        service: MetaService,
        page_access_token: str,
        page_id: str,
    ) -> NodeResult:
        recipient_id = (self.props.recipient_id or "").strip()
        message = self.props.message or ""
        messaging_type = self.props.messaging_type or "RESPONSE"

        if not recipient_id:
            return NodeResult(success=False, error="recipient_id is required")
        if not message.strip():
            return NodeResult(success=False, error="message is required")
        if messaging_type not in _VALID_MESSAGING_TYPES:
            return NodeResult(
                success=False,
                error=f"Invalid messaging_type '{messaging_type}'",
            )

        tag = (self.props.message_tag or "").strip() or None
        if messaging_type == "MESSAGE_TAG" and (not tag or tag not in _VALID_MESSAGE_TAGS):
            return NodeResult(
                success=False,
                error=(
                    "messaging_type=MESSAGE_TAG requires a valid message_tag "
                    f"({sorted(_VALID_MESSAGE_TAGS)})"
                ),
            )

        response = await service.fb_send_message(
            page_access_token=page_access_token,
            page_id=page_id,
            recipient_id=recipient_id,
            text=message,
            messaging_type=messaging_type,
            message_tag=tag,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "send_message",
                "id": str(response.get("message_id") or ""),
                "recipient_id": recipient_id,
                "response": response,
            },
        )

    async def _reply_comment(
        self,
        service: MetaService,
        page_access_token: str,
    ) -> NodeResult:
        comment_id = (self.props.comment_id or "").strip()
        reply_text = self.props.reply_text or ""
        if not comment_id:
            return NodeResult(success=False, error="comment_id is required")
        if not reply_text.strip():
            return NodeResult(success=False, error="reply_text is required")

        response = await service.fb_reply_comment(
            page_access_token,
            comment_id,
            reply_text,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "reply_comment",
                "id": str(response.get("id") or ""),
                "response": response,
            },
        )

    async def _publish_post(
        self,
        service: MetaService,
        page_access_token: str,
        page_id: str,
    ) -> NodeResult:
        post_message = (self.props.post_message or "").strip()
        media_url = resolve_media_field(self.props.media_url)
        if not post_message and not media_url:
            return NodeResult(
                success=False,
                error="Either post_message or media_url is required",
            )

        response = await service.fb_publish_post(
            page_access_token=page_access_token,
            page_id=page_id,
            message=post_message,
            link=self.props.link,
            media_url=media_url,
            media_kind=self.props.media_kind,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "publish_post",
                "id": str(response.get("id") or ""),
                "response": response,
            },
        )
