"""Consolidated Facebook (Page / Messenger) trigger.

Replaces `fb_comment`, `fb_message`, `fb_mention`, `fb_postback`,
`fb_reaction` with a single `trigger.meta.facebook` node carrying an
`event_type` dropdown.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import require_webhook_payload

FB_EVENT_TYPES: tuple[str, ...] = (
    "comment",
    "message",
    "mention",
    "postback",
    "reaction",
)


class FacebookTriggerProperties(BaseModel):
    event_type: str = "comment"
    page_id: str = ""
    credential: str | None = None

    post_id: str | None = Field(default=None)
    keyword: str | None = Field(default=None)
    regex_pattern: str | None = Field(default=None)
    payload_filter: str | None = Field(default=None)
    reaction_type: str | None = Field(default=None)


class FacebookTriggerNode(BaseNode[FacebookTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.facebook",
            name="Facebook",
            category="trigger",
            description=(
                "Fires on Facebook Page comments, Messenger DMs, mentions, "
                "Messenger button clicks, and Page reactions."
            ),
            icon="facebook",
            color="#ffffff",
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
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": "comment",
                    "options": [
                        {"label": "New Comment", "value": "comment"},
                        {"label": "New DM (Messenger)", "value": "message"},
                        {"label": "Page Mention", "value": "mention"},
                        {"label": "Button Click (postback)", "value": "postback"},
                        {"label": "Reaction on Post", "value": "reaction"},
                    ],
                },
                {
                    "name": "post_id",
                    "label": "Post ID (optional)",
                    "type": "string",
                    "placeholder": "10162001234567890_98765",
                    "description": "Only fire on comments under this specific post.",
                    "condition": {"field": "event_type", "value": "comment"},
                },
                {
                    "name": "keyword",
                    "label": "Keyword filter (optional)",
                    "type": "string",
                    "placeholder": "support",
                    "description": "Case-insensitive substring match on text.",
                    "condition": {"field": "event_type", "value": ["comment", "message"]},
                },
                {
                    "name": "regex_pattern",
                    "label": "Regex filter (optional)",
                    "type": "string",
                    "placeholder": r"^\\s*(BUY|SHOP)\\b",
                    "description": "Overrides keyword filter when set.",
                    "condition": {"field": "event_type", "value": ["comment", "message"]},
                    "mode": "advanced",
                },
                {
                    "name": "payload_filter",
                    "label": "Postback Payload (exact match)",
                    "type": "string",
                    "placeholder": "MENU_HELP",
                    "condition": {"field": "event_type", "value": "postback"},
                },
                {
                    "name": "reaction_type",
                    "label": "Reaction Type",
                    "type": "options",
                    "default": "",
                    "options": [
                        {"label": "Any", "value": ""},
                        {"label": "Like", "value": "like"},
                        {"label": "Love", "value": "love"},
                        {"label": "Wow", "value": "wow"},
                        {"label": "Haha", "value": "haha"},
                        {"label": "Sad", "value": "sad"},
                        {"label": "Angry", "value": "angry"},
                        {"label": "Care", "value": "care"},
                    ],
                    "condition": {"field": "event_type", "value": "reaction"},
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "event_type", "type": "string"},
                {"label": "from_id", "type": "string"},
                {"label": "from_name", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "post_id", "type": "string"},
                {"label": "comment_id", "type": "string"},
                {"label": "message_id", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[FacebookTriggerProperties]:
        return FacebookTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        guard = require_webhook_payload(input_data, trigger_label="Facebook")
        if guard is not None:
            return guard

        event_type = (self.props.event_type or "").strip()
        if event_type not in FB_EVENT_TYPES:
            return NodeResult(
                success=False,
                error=f"Unsupported event_type '{event_type}' (expected one of {list(FB_EVENT_TYPES)})",
            )

        value = input_data.get("value") or {}
        received_at = str(input_data.get("received_at") or "")

        if event_type == "comment":
            return self._emit_comment(value, received_at)
        if event_type == "message":
            return self._emit_message(value, received_at)
        if event_type == "mention":
            return self._emit_mention(value, received_at)
        if event_type == "postback":
            return self._emit_postback(value, received_at)
        # reaction
        return self._emit_reaction(value, received_at)

    def _emit_comment(self, value: dict[str, Any], received_at: str) -> NodeResult:
        text = str(value.get("message") or "")
        post_id_actual = str(value.get("post_id") or "")
        from_field = value.get("from") or {}

        post_id_filter = (self.props.post_id or "").strip()
        if post_id_filter and post_id_actual != post_id_filter:
            return NodeResult(success=True, output_data={"skipped": "post_id mismatch"})

        skip = self._apply_text_filters(text)
        if skip is not None:
            return skip

        return NodeResult(
            success=True,
            output_data={
                "event_type": "comment",
                "comment_id": str(value.get("comment_id") or ""),
                "text": text,
                "from_id": str(from_field.get("id") or ""),
                "from_name": str(from_field.get("name") or ""),
                "post_id": post_id_actual,
                "parent_id": str(value.get("parent_id") or ""),
                "verb": str(value.get("verb") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _emit_message(self, value: dict[str, Any], received_at: str) -> NodeResult:
        message = value.get("message") or {}
        text = str(message.get("text") or "")
        sender = value.get("sender") or {}
        recipient = value.get("recipient") or {}

        skip = self._apply_text_filters(text)
        if skip is not None:
            return skip

        return NodeResult(
            success=True,
            output_data={
                "event_type": "message",
                "message_id": str(message.get("mid") or ""),
                "from_id": str(sender.get("id") or ""),
                "recipient_id": str(recipient.get("id") or ""),
                "text": text,
                "timestamp": str(value.get("timestamp") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _emit_mention(self, value: dict[str, Any], received_at: str) -> NodeResult:
        sender = value.get("sender") or value.get("from") or {}
        return NodeResult(
            success=True,
            output_data={
                "event_type": "mention",
                "post_id": str(value.get("post_id") or ""),
                "from_id": str(sender.get("id") or ""),
                "from_name": str(sender.get("name") or ""),
                "text": str(value.get("message") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _emit_postback(self, value: dict[str, Any], received_at: str) -> NodeResult:
        postback = value.get("postback") or {}
        sender = value.get("sender") or {}
        payload_str = str(postback.get("payload") or "")

        wanted = (self.props.payload_filter or "").strip()
        if wanted and wanted != payload_str:
            return NodeResult(success=True, output_data={"skipped": "payload mismatch"})

        return NodeResult(
            success=True,
            output_data={
                "event_type": "postback",
                "from_id": str(sender.get("id") or ""),
                "title": str(postback.get("title") or ""),
                "postback_payload": payload_str,
                "referrer": postback.get("referral") or {},
                "timestamp": str(value.get("timestamp") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _emit_reaction(self, value: dict[str, Any], received_at: str) -> NodeResult:
        from_field = value.get("from") or {}
        reaction = str(value.get("reaction_type") or "").lower()

        wanted = (self.props.reaction_type or "").strip().lower()
        if wanted and wanted != reaction:
            return NodeResult(success=True, output_data={"skipped": "reaction mismatch"})

        return NodeResult(
            success=True,
            output_data={
                "event_type": "reaction",
                "post_id": str(value.get("post_id") or ""),
                "from_id": str(from_field.get("id") or ""),
                "reaction_type": reaction,
                "verb": str(value.get("verb") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _apply_text_filters(self, text: str) -> NodeResult | None:
        regex = (self.props.regex_pattern or "").strip()
        if regex:
            try:
                if not re.search(regex, text):
                    return NodeResult(success=True, output_data={"skipped": "regex mismatch"})
            except re.error as exc:
                return NodeResult(success=False, error=f"Invalid regex_pattern: {exc}")
            return None
        keyword = (self.props.keyword or "").strip()
        if keyword and keyword.lower() not in text.lower():
            return NodeResult(success=True, output_data={"skipped": "keyword mismatch"})
        return None
