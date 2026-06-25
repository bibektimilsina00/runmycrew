"""Consolidated Instagram trigger.

Replaces the five per-event nodes (`ig_comment`, `ig_message`,
`ig_mention`, `ig_story_reply`, `ig_story_mention`) with a single
`trigger.meta.instagram` node carrying an `event_type` dropdown. Field
visibility is driven by `condition` so the inspector only exposes
filters that apply to the chosen event. Matches the pattern used by
`slack_trigger.py`.
"""

from __future__ import annotations

import re
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import (
    IG_CREDENTIAL_TYPES,
    require_webhook_payload,
)

# Authoritative list of supported event types — kept in sync with
# `MetaService._EVENT_TO_FIELD["trigger.meta.instagram"]`.
IG_EVENT_TYPES: tuple[str, ...] = (
    "comment",
    "message",
    "mention",
    "story_reply",
    "story_mention",
)


class InstagramTriggerProperties(BaseModel):
    # Routing
    event_type: str = "comment"
    ig_account_id: str = ""
    credential: str | None = None
    # Filters — each only applies to a subset of events; visibility is
    # surfaced via the `condition` keys in `get_metadata`.
    media_id: str | None = Field(default=None)
    keyword: str | None = Field(default=None)
    regex_pattern: str | None = Field(default=None)


class InstagramTriggerNode(BaseNode[InstagramTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.instagram",
            name="Instagram",
            category="trigger",
            description=(
                "Fires on Instagram comments, DMs, mentions, story replies, "
                "and story mentions. Pick the event type below."
            ),
            icon="instagram",
            color="#1c1c1c",
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
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": "comment",
                    "options": [
                        {"label": "New Comment", "value": "comment"},
                        {"label": "New DM", "value": "message"},
                        {"label": "Mention", "value": "mention"},
                        {"label": "Story Reply", "value": "story_reply"},
                        {"label": "Story Mention", "value": "story_mention"},
                    ],
                },
                # Comment-only filters
                {
                    "name": "media_id",
                    "label": "Post ID (optional)",
                    "type": "string",
                    "placeholder": "17841405822304914",
                    "description": "Only fire on comments under this specific post.",
                    "condition": {"field": "event_type", "value": "comment"},
                },
                # Substring/regex filters apply to comments + DMs (text-bearing events).
                {
                    "name": "keyword",
                    "label": "Keyword filter (optional)",
                    "type": "string",
                    "placeholder": "GUIDE",
                    "description": "Case-insensitive substring match on text.",
                    "condition": {"field": "event_type", "value": ["comment", "message"]},
                },
                {
                    "name": "regex_pattern",
                    "label": "Regex filter (optional)",
                    "type": "string",
                    "placeholder": r"^\\s*(GUIDE|LINK)\\b",
                    "description": "Overrides keyword filter when set.",
                    "condition": {"field": "event_type", "value": ["comment", "message"]},
                    "mode": "advanced",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "event_type", "type": "string"},
                {"label": "from_id", "type": "string"},
                {"label": "text", "type": "string"},
                {"label": "media_id", "type": "string"},
                {"label": "comment_id", "type": "string"},
                {"label": "message_id", "type": "string"},
                {"label": "story_id", "type": "string"},
                {"label": "attachment_url", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[InstagramTriggerProperties]:
        return InstagramTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        guard = require_webhook_payload(input_data, trigger_label="Instagram")
        if guard is not None:
            return guard

        event_type = (self.props.event_type or "").strip()
        if event_type not in IG_EVENT_TYPES:
            return NodeResult(
                success=False,
                error=f"Unsupported event_type '{event_type}' (expected one of {list(IG_EVENT_TYPES)})",
            )

        value = input_data.get("value") or {}
        received_at = str(input_data.get("received_at") or "")

        if event_type == "comment":
            return self._emit_comment(value, received_at)
        if event_type == "message":
            return self._emit_message(value, received_at)
        if event_type == "mention":
            return self._emit_mention(value, received_at)
        if event_type == "story_reply":
            return self._emit_story_reply(value, received_at)
        # story_mention
        return self._emit_story_mention(value, received_at)

    # ------------------------------------------------------------------
    # Per-event emitters — kept as small functions so the dispatch table
    # above reads top-to-bottom and adding an event = add one branch +
    # one emitter.
    # ------------------------------------------------------------------

    def _emit_comment(self, value: dict[str, Any], received_at: str) -> NodeResult:
        comment_text = str(value.get("text") or "")
        media = value.get("media") or {}
        from_field = value.get("from") or {}

        media_id_filter = (self.props.media_id or "").strip()
        if media_id_filter and str(media.get("id") or "") != media_id_filter:
            return NodeResult(success=True, output_data={"skipped": "media_id mismatch"})

        skip = self._apply_text_filters(comment_text)
        if skip is not None:
            return skip

        return NodeResult(
            success=True,
            output_data={
                "event_type": "comment",
                "from_id": str(from_field.get("id") or ""),
                "from_username": str(from_field.get("username") or ""),
                "comment_id": str(value.get("id") or ""),
                "text": comment_text,
                "media_id": str(media.get("id") or ""),
                "parent_id": str(value.get("parent_id") or ""),
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
                "from_id": str(sender.get("id") or ""),
                "message_id": str(message.get("mid") or ""),
                "recipient_id": str(recipient.get("id") or ""),
                "text": text,
                "timestamp": str(value.get("timestamp") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _emit_mention(self, value: dict[str, Any], received_at: str) -> NodeResult:
        return NodeResult(
            success=True,
            output_data={
                "event_type": "mention",
                "media_id": str(value.get("media_id") or ""),
                "comment_id": str(value.get("comment_id") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _emit_story_reply(self, value: dict[str, Any], received_at: str) -> NodeResult:
        message = value.get("message") or {}
        reply_to = message.get("reply_to") or {}
        story = reply_to.get("story") or {}
        sender = value.get("sender") or {}
        return NodeResult(
            success=True,
            output_data={
                "event_type": "story_reply",
                "from_id": str(sender.get("id") or ""),
                "message_id": str(message.get("mid") or ""),
                "text": str(message.get("text") or ""),
                "story_id": str(story.get("id") or ""),
                "timestamp": str(value.get("timestamp") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )

    def _emit_story_mention(self, value: dict[str, Any], received_at: str) -> NodeResult:
        message = value.get("message") or {}
        attachments = message.get("attachments") or []
        sender = value.get("sender") or {}

        attachment_url = ""
        if isinstance(attachments, list):
            for att in attachments:
                if isinstance(att, dict) and str(att.get("type") or "") == "story_mention":
                    payload = att.get("payload") or {}
                    if isinstance(payload, dict):
                        attachment_url = str(payload.get("url") or "")
                        break

        return NodeResult(
            success=True,
            output_data={
                "event_type": "story_mention",
                "from_id": str(sender.get("id") or ""),
                "message_id": str(message.get("mid") or ""),
                "attachment_url": attachment_url,
                "timestamp": str(value.get("timestamp") or ""),
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
