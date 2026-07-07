"""Fathom (fathom.video) webhook trigger — manifest form.

Fathom ships the shared webhook secret directly in the
`x-webhook-secret` header — no HMAC. We compare the bare header
value against the configured secret under `hmac.compare_digest` via
the shared `gitlab_token` scheme.

Setup
  1. Fathom Settings → Integrations → Webhooks → Add Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/fathom/${workflow_id}/${node_id}`.
  3. Copy the generated *webhook secret* into the trigger's Secret field.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    meeting = body.get("meeting") or body
    return {
        "event": event_type or body.get("event") or "",
        "delivery": delivery_id or meeting.get("id") or "",
        "meeting_id": meeting.get("id"),
        "meeting_url": meeting.get("url"),
        "title": meeting.get("title"),
        "recording_url": meeting.get("recording_url"),
        "transcript_url": meeting.get("transcript_url"),
        "summary": meeting.get("summary") or body.get("summary"),
        "action_items": meeting.get("action_items") or body.get("action_items"),
        "attendees": meeting.get("attendees") or body.get("attendees"),
        "started_at": meeting.get("started_at"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.fathom_webhook",
    name="Fathom",
    description=(
        "Fires when Fathom posts a meeting event (summary ready, action "
        "items generated). Verified via bare-secret compare against "
        "`x-webhook-secret`."
    ),
    icon_slug="fathom",
    color="#1c1c1c",
    provider="fathom",
    signature=SignatureSpec(
        scheme="gitlab_token",
        header_name="x-webhook-secret",
        secret_field="secret",
        prefix="",
    ),
    event_header="x-fathom-event",
    events=[
        WebhookEvent(value="meeting.ended", label="Meeting ended"),
        WebhookEvent(value="meeting.summary_ready", label="Summary ready"),
        WebhookEvent(value="meeting.action_items_ready", label="Action items ready"),
        WebhookEvent(value="meeting.transcript_ready", label="Transcript ready"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "meeting_id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "recording_url", "type": "string"},
        {"label": "transcript_url", "type": "string"},
        {"label": "summary", "type": "string"},
        {"label": "action_items", "type": "array"},
        {"label": "body", "type": "object"},
    ],
)
