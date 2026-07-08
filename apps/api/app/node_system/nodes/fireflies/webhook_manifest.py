"""Fireflies.ai webhook trigger — manifest form.

Fireflies signs webhook deliveries with HMAC-SHA1 hex under the
`x-hub-signature` header (same convention as legacy GitHub v1
webhooks). Prefix: `sha1=`.

Setup
  1. Fireflies Dashboard → Integrations → Webhooks.
  2. URL: `${BASE_URL}/api/v1/webhooks/fireflies/${workflow_id}/${node_id}`.
  3. Copy the *webhook secret* into this trigger's Secret field.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.nodes.fireflies import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    meeting = body.get("meetingData") or body.get("meeting") or {}
    return {
        "event": event_type or body.get("event") or body.get("eventType") or "",
        "delivery": delivery_id or body.get("meetingId") or meeting.get("id") or "",
        "meeting_id": body.get("meetingId") or meeting.get("id"),
        "title": meeting.get("title") or body.get("title"),
        "date": meeting.get("date") or body.get("date"),
        "duration": meeting.get("duration"),
        "transcript_url": meeting.get("transcript_url") or body.get("transcript_url"),
        "audio_url": meeting.get("audio_url") or body.get("audio_url"),
        "video_url": meeting.get("video_url") or body.get("video_url"),
        "summary": meeting.get("summary") or body.get("summary"),
        "attendees": meeting.get("attendees") or body.get("attendees"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.fireflies_webhook",
    name=NAME,
    description=(
        "Fires when Fireflies posts a meeting event (transcript ready, "
        "summary complete). Verified via HMAC-SHA1 in `x-hub-signature`."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    provider="fireflies",
    signature=SignatureSpec(
        scheme="hmac_sha1",
        header_name="x-hub-signature",
        secret_field="secret",
        prefix="sha1=",
    ),
    event_header="x-fireflies-event",
    events=[
        WebhookEvent(value="Transcription completed", label="Transcription completed"),
        WebhookEvent(value="Summary completed", label="Summary completed"),
        WebhookEvent(value="Meeting created", label="Meeting created"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "meeting_id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "date", "type": "string"},
        {"label": "transcript_url", "type": "string"},
        {"label": "audio_url", "type": "string"},
        {"label": "summary", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
