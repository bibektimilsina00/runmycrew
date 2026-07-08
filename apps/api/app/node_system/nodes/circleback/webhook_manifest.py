"""Circleback webhook trigger — manifest form.

Circleback signs webhook deliveries with HMAC-SHA256 hex in
`x-circleback-signature` (no prefix). Event kind lives in the body
under `type` (meeting.ended, insights.ready, action_items.ready).

Setup
  1. Circleback → Settings → Integrations → Webhooks → Add.
  2. URL: `${BASE_URL}/api/v1/webhooks/circleback/${wf}/${node}`.
  3. Copy the *signing secret* into this trigger's Secret field.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.nodes.circleback import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    meeting = body.get("meeting") or body.get("data") or {}
    return {
        "event": event_type or body.get("type") or "",
        "delivery": delivery_id or body.get("id") or "",
        "meeting_id": meeting.get("id") or body.get("meeting_id"),
        "meeting_title": meeting.get("title"),
        "meeting_url": meeting.get("url") or meeting.get("recording_url"),
        "started_at": meeting.get("started_at"),
        "ended_at": meeting.get("ended_at"),
        "attendees": meeting.get("attendees") or [],
        "summary": body.get("summary") or meeting.get("summary"),
        "action_items": body.get("action_items") or meeting.get("action_items") or [],
        "transcript_url": meeting.get("transcript_url"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.circleback_webhook",
    name=NAME,
    description=(
        "Fires when Circleback posts a meeting event (meeting.ended, "
        "insights.ready, action_items.ready). Verified via HMAC-SHA256 "
        "in `x-circleback-signature`."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    provider="circleback",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="x-circleback-signature",
        secret_field="secret",
        prefix="",
    ),
    event_header="X-Circleback-Event",
    event_body_path="type",
    events=[
        WebhookEvent(value="meeting.ended", label="Meeting Ended"),
        WebhookEvent(value="insights.ready", label="Insights Ready"),
        WebhookEvent(value="action_items.ready", label="Action Items Ready"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "meeting_id", "type": "string"},
        {"label": "meeting_title", "type": "string"},
        {"label": "summary", "type": "string"},
        {"label": "action_items", "type": "array"},
        {"label": "attendees", "type": "array"},
        {"label": "body", "type": "object"},
    ],
)
