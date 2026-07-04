"""Gong webhook trigger — manifest form.

Gong signs webhook deliveries with HMAC-SHA256 hex of the raw body
under a shared secret. Header: `X-Gong-Signature`, no prefix.

Gong's automation-rules feature routes calls / recordings / stats
into the same endpoint — event kind lives in the body's `eventType`.

Setup
  1. Gong Admin → Integrations → API → Automation Rule → Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/gong/${workflow_id}/${node_id}`.
  3. Copy the *webhook secret* into this trigger's Secret field.
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
    call = body.get("call") or {}
    return {
        "event": event_type or body.get("eventType") or "",
        "delivery": delivery_id or body.get("eventId") or "",
        "call_id": call.get("id") or body.get("callId"),
        "call_url": call.get("url"),
        "title": call.get("title"),
        "started": call.get("started"),
        "duration": call.get("duration"),
        "participants": call.get("participants"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.gong_webhook",
    name="Gong Webhook",
    description=(
        "Fires when a Gong automation rule delivers a call event "
        "(processed / recording ready / stats updated). Verified via "
        "HMAC-SHA256 in `X-Gong-Signature`."
    ),
    icon_slug="gong",
    color="#1c1c1c",
    provider="gong",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="X-Gong-Signature",
        secret_field="secret",
        prefix="",
    ),
    event_header="X-Gong-Event",
    events=[
        WebhookEvent(value="call.ended", label="Call ended"),
        WebhookEvent(value="call.recording_ready", label="Recording ready"),
        WebhookEvent(value="call.transcript_ready", label="Transcript ready"),
        WebhookEvent(value="call.stats_updated", label="Call stats updated"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "call_id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "started", "type": "string"},
        {"label": "duration", "type": "number"},
        {"label": "body", "type": "object"},
    ],
)
