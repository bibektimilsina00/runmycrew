from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class FBCommentTriggerProperties(BaseModel):
    page_id: str = ""
    post_id: str | None = Field(
        default=None,
        description="Optional — only fire on comments under this specific Page post.",
    )
    keyword: str | None = Field(
        default=None,
        description="Optional case-insensitive substring filter on comment text.",
    )
    regex_pattern: str | None = Field(
        default=None,
        description="Optional regex filter (overrides keyword when set).",
    )


class FBCommentTriggerNode(BaseNode[FBCommentTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.fb_comment",
            name="Facebook Comment",
            category="trigger",
            description=(
                "Fires when a user comments on a post by the connected "
                "Facebook Page. Mirrors the IG-comment trigger for FB."
            ),
            icon="MessageSquare",
            color="#1877F2",
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
                    "name": "post_id",
                    "label": "Post ID (optional)",
                    "type": "string",
                    "placeholder": "1234567_8901234",
                    "description": "Only fire on comments under this specific post.",
                },
                {
                    "name": "keyword",
                    "label": "Keyword filter (optional)",
                    "type": "string",
                    "placeholder": "support",
                },
                {
                    "name": "regex_pattern",
                    "label": "Regex filter (optional)",
                    "type": "string",
                    "advanced": True,
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "comment_id", "type": "string"},
                {"label": "comment_text", "type": "string"},
                {"label": "from_id", "type": "string"},
                {"label": "from_name", "type": "string"},
                {"label": "post_id", "type": "string"},
                {"label": "parent_id", "type": "string"},
                {"label": "verb", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[FBCommentTriggerProperties]:
        return FBCommentTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        comment_text = str(value.get("message") or "")
        post_id_actual = str(value.get("post_id") or "")
        from_field = value.get("from") or {}

        post_id_filter = (self.props.post_id or "").strip()
        if post_id_filter and post_id_actual != post_id_filter:
            return NodeResult(success=True, output_data={"skipped": "post_id mismatch"})

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

        return NodeResult(
            success=True,
            output_data={
                "comment_id": str(value.get("comment_id") or ""),
                "comment_text": comment_text,
                "from_id": str(from_field.get("id") or ""),
                "from_name": str(from_field.get("name") or ""),
                "post_id": post_id_actual,
                "parent_id": str(value.get("parent_id") or ""),
                "verb": str(value.get("verb") or ""),
                "received_at": str(input_data.get("received_at") or ""),
                "payload": value,
            },
        )
