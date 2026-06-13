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
    page_token_by_ig_account_id,
)


class IGReplyCommentProperties(BaseModel):
    credential: str | None = None
    ig_account_id: str = ""
    comment_id: str = ""
    message: str = ""


class IGReplyCommentNode(BaseNode[IGReplyCommentProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.ig_reply_comment",
            name="Reply to Instagram Comment",
            category="action",
            description="Post a public reply under an Instagram comment.",
            icon="MessageSquareReply",
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
                    "dependsOn": ["credential"],
                    "required": True,
                },
                {
                    "name": "comment_id",
                    "label": "Comment ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $node('IG Comment').comment_id }}",
                },
                {
                    "name": "message",
                    "label": "Reply",
                    "type": "string",
                    "required": True,
                    "multiline": True,
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "reply_id", "type": "string"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[IGReplyCommentProperties]:
        return IGReplyCommentProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")
        if not self.props.comment_id:
            return NodeResult(success=False, error="comment_id is required")
        if not self.props.message.strip():
            return NodeResult(success=False, error="message is required")

        credential = find_credential(context.credentials, self.props.credential)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")
        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")

        token = page_token_by_ig_account_id(data, self.props.ig_account_id)
        if not token:
            return NodeResult(
                success=False,
                error="No page access token for this Instagram account.",
            )

        service = MetaService(context.db)
        try:
            resp = await service.ig_reply_comment(token, self.props.comment_id, self.props.message)
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))
        return NodeResult(
            success=True,
            output_data={"reply_id": str(resp.get("id") or ""), "response": resp},
        )
