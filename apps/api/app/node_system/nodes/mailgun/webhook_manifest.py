"""Mailgun webhook trigger — manifest form.

Mailgun's signature isn't in a header — it's in the JSON body under
`signature: {timestamp, token, signature}`. Signature is
hex(HMAC-SHA256("{timestamp}{token}", api_key)). 5-min anti-replay
tolerance on timestamp. The scaffold's new `mailgun` scheme handles
the body-based verification.

Event kind lives in body's `event-data.event` (e.g. `delivered`,
`opened`, `clicked`, `failed`, `complained`, `unsubscribed`).

Setup
  1. Mailgun Dashboard → Sending → Webhooks → Add Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/mailgun_webhook/${wf}/${node}`.
  3. Copy the *webhook signing key* (Mailgun API key, from settings)
     into this trigger's Secret field.
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
    event_data = body.get("event-data") or {}
    message = event_data.get("message") or {}
    headers = message.get("headers") or {}
    recipient_domain = event_data.get("recipient-domain")
    delivery_status = event_data.get("delivery-status") or {}
    return {
        "event": event_type or event_data.get("event") or "",
        "delivery": delivery_id or event_data.get("id") or "",
        "event_data": event_data,
        "timestamp": event_data.get("timestamp"),
        "recipient": event_data.get("recipient"),
        "recipient_domain": recipient_domain,
        "message_id": headers.get("message-id") or event_data.get("message-id"),
        "subject": headers.get("subject"),
        "from": headers.get("from"),
        "to": headers.get("to"),
        "delivery_code": delivery_status.get("code"),
        "delivery_message": delivery_status.get("message"),
        "reason": event_data.get("reason"),
        "severity": event_data.get("severity"),
        "url": event_data.get("url"),  # for click events
        "user_variables": event_data.get("user-variables"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.mailgun_webhook",
    name="Mailgun Webhook",
    description=(
        "Fires when Mailgun posts a delivery event (delivered, opened, "
        "clicked, failed, complained, unsubscribed). Body-based signature "
        "verified via HMAC-SHA256 of {timestamp}{token} under the API key, "
        "with 5-min anti-replay tolerance."
    ),
    icon_slug="mailgun",
    color="#1c1c1c",
    provider="mailgun_webhook",
    signature=SignatureSpec(
        scheme="mailgun",
        # Empty header_name — signature lives in the body. Service
        # short-circuits the header presence check when header_name is
        # empty and lets the verifier read the body itself.
        header_name="",
        secret_field="secret",
        prefix="",
    ),
    event_header="X-Mailgun-Event",
    event_body_path="event-data.event",
    events=[
        WebhookEvent(value="accepted", label="Accepted"),
        WebhookEvent(value="rejected", label="Rejected"),
        WebhookEvent(value="delivered", label="Delivered"),
        WebhookEvent(value="failed", label="Failed"),
        WebhookEvent(value="opened", label="Opened"),
        WebhookEvent(value="clicked", label="Clicked"),
        WebhookEvent(value="complained", label="Complained"),
        WebhookEvent(value="unsubscribed", label="Unsubscribed"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "recipient", "type": "string"},
        {"label": "message_id", "type": "string"},
        {"label": "subject", "type": "string"},
        {"label": "delivery_code", "type": "number"},
        {"label": "delivery_message", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
