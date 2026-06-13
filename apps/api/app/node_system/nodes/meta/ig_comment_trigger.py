from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class IGCommentTriggerProperties(BaseModel):
    # Selected via the `meta-resource` field type (kind=ig_account). The id
    # here is the Instagram *business* account id — also the `entry.id` Meta
    # uses on the incoming webhook envelope, which is what
    # MetaService.receive_webhook filters on.
    ig_account_id: str = ""
    media_id: str | None = Field(
        default=None,
        description="Optional — only fire on comments under this specific post.",
    )
    keyword: str | None = Field(
        default=None,
        description="Optional case-insensitive substring filter on comment text.",
    )
    regex_pattern: str | None = Field(
        default=None,
        description="Optional regex filter (overrides keyword when set).",
    )


class IGCommentTriggerNode(BaseNode[IGCommentTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.ig_comment",
            name="Instagram Comment",
            category="trigger",
            description=(
                "Fires when a user comments on a post by the connected "
                "Instagram Business account. Powers the comment-to-DM trend."
            ),
            icon="MessageSquare",
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
                    "name": "media_id",
                    "label": "Post ID (optional)",
                    "type": "string",
                    "placeholder": "17841405822304914",
                    "description": "Only fire on comments under this specific post.",
                },
                {
                    "name": "keyword",
                    "label": "Keyword filter (optional)",
                    "type": "string",
                    "placeholder": "GUIDE",
                    "description": "Case-insensitive substring match on comment text.",
                },
                {
                    "name": "regex_pattern",
                    "label": "Regex filter (optional)",
                    "type": "string",
                    "placeholder": r"^\\s*(GUIDE|LINK)\\b",
                    "description": "Overrides the keyword filter when set.",
                    "advanced": True,
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "comment_id", "type": "string"},
                {"label": "comment_text", "type": "string"},
                {"label": "from_id", "type": "string"},
                {"label": "from_username", "type": "string"},
                {"label": "media_id", "type": "string"},
                {"label": "parent_id", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[IGCommentTriggerProperties]:
        return IGCommentTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # `input_data` is the trigger payload assembled by MetaService.
        # Shape: { object, field, target_id, value, received_at }
        value = input_data.get("value") or {}
        comment_text = str(value.get("text") or "")
        media = value.get("media") or {}
        from_field = value.get("from") or {}

        # Server-side filters — keep them here (in addition to the webhook
        # router's property_filters) because property_filters only narrows by
        # ig_account_id, not by post/keyword/regex.
        media_id_filter = (self.props.media_id or "").strip()
        if media_id_filter and str(media.get("id") or "") != media_id_filter:
            return NodeResult(success=True, output_data={"skipped": "media_id mismatch"})

        regex = (self.props.regex_pattern or "").strip()
        keyword = (self.props.keyword or "").strip()
        if regex:
            try:
                if not re.search(regex, comment_text):
                    return NodeResult(success=True, output_data={"skipped": "regex mismatch"})
            except re.error as exc:
                return NodeResult(success=False, error=f"Invalid regex_pattern: {exc}")
        elif keyword and keyword.lower() not in comment_text.lower():
            return NodeResult(success=True, output_data={"skipped": "keyword mismatch"})

        output = {
            "comment_id": str(value.get("id") or ""),
            "comment_text": comment_text,
            "from_id": str(from_field.get("id") or ""),
            "from_username": str(from_field.get("username") or ""),
            "media_id": str(media.get("id") or ""),
            "parent_id": str(value.get("parent_id") or ""),
            "received_at": str(input_data.get("received_at") or ""),
            "payload": value,
        }
        return NodeResult(success=True, output_data=output)
