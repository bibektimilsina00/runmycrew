"""Emailbison webhook trigger — manifest form.

Emailbison signs webhook deliveries with HMAC-SHA256 hex under a
shared secret. Header: `x-emailbison-signature`, no prefix.

Event kind lives in the body's `event` field.

Setup
  1. Emailbison Workspace → Settings → Webhooks → Add Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/emailbison_webhook/${wf}/${node}`.
  3. Copy the *webhook secret* into this trigger's Secret field.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.nodes.emailbison import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    data = body.get("data") or body
    return {
        "event": event_type or body.get("event") or "",
        "delivery": delivery_id or body.get("id") or "",
        "workspace_id": body.get("workspace_id"),
        "campaign_id": data.get("campaign_id"),
        "lead_id": data.get("lead_id"),
        "lead_email": data.get("email") or data.get("lead_email"),
        "first_name": data.get("first_name"),
        "last_name": data.get("last_name"),
        "message_id": data.get("message_id"),
        "reply_body": data.get("reply_body"),
        "timestamp": body.get("timestamp"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.emailbison_webhook",
    name=NAME,
    description=(
        "Fires when Emailbison posts a per-email event (sent, opened, "
        "clicked, bounced, reply, lead status). Verified via HMAC-SHA256 "
        "in `x-emailbison-signature`."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    provider="emailbison_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="x-emailbison-signature",
        secret_field="secret",
        prefix="",
    ),
    event_header="x-emailbison-event",
    event_body_path="event",
    events=[
        WebhookEvent(value="email_sent", label="Email Sent"),
        WebhookEvent(value="email_opened", label="Email Opened"),
        WebhookEvent(value="email_clicked", label="Link Clicked"),
        WebhookEvent(value="email_bounced", label="Email Bounced"),
        WebhookEvent(value="email_replied", label="Reply Received"),
        WebhookEvent(value="lead_interested", label="Lead Interested"),
        WebhookEvent(value="lead_not_interested", label="Lead Not Interested"),
        WebhookEvent(value="lead_unsubscribed", label="Lead Unsubscribed"),
        WebhookEvent(value="lead_meeting_booked", label="Meeting Booked"),
        WebhookEvent(value="campaign_completed", label="Campaign Completed"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "campaign_id", "type": "string"},
        {"label": "lead_id", "type": "string"},
        {"label": "lead_email", "type": "string"},
        {"label": "message_id", "type": "string"},
        {"label": "reply_body", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
