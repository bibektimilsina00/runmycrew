"""Consolidated Instagram action node.

Replaces `ig_send_dm`, `ig_reply_comment`, `ig_publish_post`, and
`ig_publish_story` with one `action.meta.instagram` node carrying an
`operation` dropdown + condition-driven field visibility.
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
    IG_CREDENTIAL_TYPES,
    find_credential,
    ig_send_context,
    resolve_media_field,
)

IG_ACTION_OPS: tuple[str, ...] = (
    "send_dm",
    "reply_comment",
    "publish_post",
    "publish_story",
)

_PUBLISH_KINDS = {"IMAGE", "VIDEO", "REELS"}


class InstagramActionProperties(BaseModel):
    credential: str | None = None
    ig_account_id: str = ""
    operation: str = "send_dm"

    # send_dm
    recipient_id: str = ""
    message: str = ""

    # reply_comment
    comment_id: str = ""
    reply_text: str = ""

    # publish_post / publish_story — shared media_url. Accepts either a
    # plain URL string or a discriminated `{type: "url" | "asset", ...}`
    # dict from the MediaRenderer; `resolve_media_field` normalizes both.
    media_url: Any = ""
    kind: str = "IMAGE"
    caption: str | None = None


class InstagramActionNode(BaseNode[InstagramActionProperties]):
    SUPPORTED_CREDENTIAL_TYPES = IG_CREDENTIAL_TYPES

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        cond_send_dm = {"field": "operation", "value": "send_dm"}
        cond_reply_comment = {"field": "operation", "value": "reply_comment"}
        cond_publish_post = {"field": "operation", "value": "publish_post"}
        cond_publish_any = {"field": "operation", "value": ["publish_post", "publish_story"]}

        return NodeMetadata(
            type="action.meta.instagram",
            name="Instagram",
            category="action",
            description=(
                "Send DMs, reply to comments, and publish posts or stories from "
                "the connected Instagram Business account. Pick the operation below."
            ),
            icon="Instagram",
            color="#E1306C",
            properties=[
                {
                    "name": "credential",
                    "label": "Meta or Instagram Account",
                    "type": "credential",
                    "credentialType": list(IG_CREDENTIAL_TYPES),
                    "required": True,
                },
                {
                    "name": "ig_account_id",
                    "label": "Instagram Account",
                    "type": "meta-resource",
                    "resourceKind": "ig_account",
                    "dependsOn": ["credential"],
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "send_dm",
                    "options": [
                        {"label": "Send DM", "value": "send_dm"},
                        {"label": "Reply to Comment", "value": "reply_comment"},
                        {"label": "Publish Post", "value": "publish_post"},
                        {"label": "Publish Story", "value": "publish_story"},
                    ],
                },
                # ── send_dm ──────────────────────────────────────────
                {
                    "name": "recipient_id",
                    "label": "Recipient IGSID",
                    "type": "string",
                    "required": True,
                    "placeholder": "=$step.from_id",
                    "description": (
                        "Instagram scoped user id. From a comment / DM trigger, "
                        "use the upstream `from_id` output."
                    ),
                    "condition": cond_send_dm,
                },
                {
                    "name": "message",
                    "label": "Message",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                    "placeholder": "Thanks! Here's the link: ...",
                    "condition": cond_send_dm,
                },
                # ── reply_comment ────────────────────────────────────
                {
                    "name": "comment_id",
                    "label": "Comment ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "=$step.comment_id",
                    "condition": cond_reply_comment,
                },
                {
                    "name": "reply_text",
                    "label": "Reply",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                    "condition": cond_reply_comment,
                },
                # ── publish_post + publish_story ─────────────────────
                {
                    "name": "media_url",
                    "label": "Media",
                    "type": "media",
                    "required": True,
                    "placeholder": "https://...",
                    "description": (
                        "Paste a public URL, upload a file, or pick one from "
                        "your Library. Uploads + library picks are served "
                        "through a short-lived signed URL so Meta can fetch "
                        "them without auth."
                    ),
                    "typeOptions": {
                        "accept": "image/*,video/*",
                        "mediaKindField": "kind",
                    },
                    "condition": cond_publish_any,
                },
                {
                    "name": "kind",
                    "label": "Media Type",
                    "type": "options",
                    "default": "IMAGE",
                    "options": [
                        {"label": "Image", "value": "IMAGE"},
                        {"label": "Video", "value": "VIDEO"},
                        {"label": "Reel", "value": "REELS"},
                    ],
                    "condition": cond_publish_post,
                },
                {
                    "name": "caption",
                    "label": "Caption (optional)",
                    "type": "string",
                    "multiline": True,
                    "condition": cond_publish_post,
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
    def get_properties_model(cls) -> type[InstagramActionProperties]:
        return InstagramActionProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")

        op = (self.props.operation or "").strip()
        if op not in IG_ACTION_OPS:
            return NodeResult(
                success=False,
                error=f"Unsupported operation '{op}' (expected one of {list(IG_ACTION_OPS)})",
            )

        ig_account_id = (self.props.ig_account_id or "").strip()
        if not ig_account_id:
            return NodeResult(success=False, error="ig_account_id is required")

        credential = find_credential(
            context.credentials, self.props.credential, IG_CREDENTIAL_TYPES
        )
        if credential is None:
            return NodeResult(success=False, error="No Meta or Instagram credential available")

        ctx = ig_send_context(credential, ig_account_id)
        if ctx is None:
            return NodeResult(
                success=False,
                error=(
                    "No access token found for this Instagram account. "
                    "Reconnect the credential to refresh tokens."
                ),
            )
        access_token, graph_base, resolved_ig_id = ctx
        service = MetaService(context.db)

        try:
            if op == "send_dm":
                return await self._send_dm(service, access_token, graph_base, resolved_ig_id)
            if op == "reply_comment":
                return await self._reply_comment(service, access_token, graph_base)
            if op == "publish_post":
                return await self._publish_post(service, access_token, graph_base, resolved_ig_id)
            # publish_story
            return await self._publish_story(service, access_token, graph_base, resolved_ig_id)
        except Exception as exc:  # noqa: BLE001 — surface Graph error verbatim
            return NodeResult(success=False, error=str(exc))

    # ── per-operation handlers ────────────────────────────────────────

    async def _send_dm(
        self,
        service: MetaService,
        access_token: str,
        graph_base: str,
        ig_user_id: str,
    ) -> NodeResult:
        recipient_id = (self.props.recipient_id or "").strip()
        message = self.props.message or ""
        if not recipient_id:
            return NodeResult(success=False, error="recipient_id is required")
        if not message.strip():
            return NodeResult(success=False, error="message is required")

        response = await service.ig_send_dm(
            page_access_token=access_token,
            ig_user_id=ig_user_id,
            recipient_id=recipient_id,
            text=message,
            graph_base=graph_base,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "send_dm",
                "id": str(response.get("message_id") or ""),
                "recipient_id": recipient_id,
                "response": response,
            },
        )

    async def _reply_comment(
        self,
        service: MetaService,
        access_token: str,
        graph_base: str,
    ) -> NodeResult:
        comment_id = (self.props.comment_id or "").strip()
        reply_text = self.props.reply_text or ""
        if not comment_id:
            return NodeResult(success=False, error="comment_id is required")
        if not reply_text.strip():
            return NodeResult(success=False, error="reply_text is required")

        response = await service.ig_reply_comment(
            access_token,
            comment_id,
            reply_text,
            graph_base=graph_base,
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
        access_token: str,
        graph_base: str,
        ig_user_id: str,
    ) -> NodeResult:
        media_url = resolve_media_field(self.props.media_url)
        if not media_url:
            return NodeResult(success=False, error="media_url is required")
        kind_upper = (self.props.kind or "IMAGE").upper()
        if kind_upper not in _PUBLISH_KINDS:
            return NodeResult(
                success=False,
                error=f"Invalid kind '{self.props.kind}' (expected {sorted(_PUBLISH_KINDS)})",
            )

        response = await service.ig_publish_media(
            page_access_token=access_token,
            ig_user_id=ig_user_id,
            media_url=media_url,
            kind=kind_upper,
            caption=self.props.caption,
            graph_base=graph_base,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "publish_post",
                "id": str(response.get("id") or ""),
                "response": response,
            },
        )

    async def _publish_story(
        self,
        service: MetaService,
        access_token: str,
        graph_base: str,
        ig_user_id: str,
    ) -> NodeResult:
        media_url = resolve_media_field(self.props.media_url)
        if not media_url:
            return NodeResult(success=False, error="media_url is required")

        response = await service.ig_publish_media(
            page_access_token=access_token,
            ig_user_id=ig_user_id,
            media_url=media_url,
            kind="STORIES",
            graph_base=graph_base,
        )
        return NodeResult(
            success=True,
            output_data={
                "operation": "publish_story",
                "id": str(response.get("id") or ""),
                "response": response,
            },
        )
