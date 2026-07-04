"""Loops.so webhook trigger — manifest form.

Loops signs webhook deliveries with HMAC-SHA256 hex in `X-Loops-Signature`
(no prefix). Event kind lives in the body's `event` field.

Setup
  1. Loops Dashboard → Settings → Webhooks → Add Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/loops_webhook/${wf}/${node}`.
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
    return {
        "event": event_type or body.get("event") or "",
        "delivery": delivery_id or body.get("id") or "",
        "email": body.get("email"),
        "contact_id": body.get("contactId") or body.get("id"),
        "first_name": body.get("firstName"),
        "last_name": body.get("lastName"),
        "user_group": body.get("userGroup"),
        "campaign_id": body.get("campaignId"),
        "campaign_name": body.get("campaignName"),
        "email_id": body.get("emailId"),
        "subscribed": body.get("subscribed"),
        "url_clicked": body.get("urlClicked"),
        "sent_at": body.get("sentAt") or body.get("timestamp"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.loops_webhook",
    name="Loops Webhook",
    description=(
        "Fires when Loops posts a delivery / engagement event. Verified "
        "via HMAC-SHA256 in `X-Loops-Signature`."
    ),
    icon_slug="loops",
    color="#1c1c1c",
    provider="loops_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="X-Loops-Signature",
        secret_field="secret",
        prefix="",
    ),
    event_header="X-Loops-Event",
    event_body_path="event",
    events=[
        WebhookEvent(value="email_sent", label="Email Sent"),
        WebhookEvent(value="email_delivered", label="Email Delivered"),
        WebhookEvent(value="email_opened", label="Email Opened"),
        WebhookEvent(value="email_clicked", label="Email Clicked"),
        WebhookEvent(value="email_bounced", label="Email Bounced"),
        WebhookEvent(value="email_complained", label="Spam Complaint"),
        WebhookEvent(value="contact_subscribed", label="Contact Subscribed"),
        WebhookEvent(value="contact_unsubscribed", label="Contact Unsubscribed"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "contact_id", "type": "string"},
        {"label": "campaign_id", "type": "string"},
        {"label": "url_clicked", "type": "string"},
        {"label": "sent_at", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
