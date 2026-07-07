"""Lemlist webhook trigger — manifest form.

Lemlist ships the shared webhook secret directly in the
`x-webhook-token` header — bare-secret compare, no HMAC. We use the
shared `gitlab_token` scheme.

Event kind lives in the body's `type` field.

Setup
  1. Lemlist Settings → Integrations → Webhooks → Add Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/lemlist_webhook/${wf}/${node}`.
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
        "event": event_type or body.get("type") or "",
        "delivery": delivery_id or body.get("_id") or body.get("id") or "",
        "type": body.get("type"),
        "campaign_id": body.get("campaignId"),
        "campaign_name": body.get("campaignName"),
        "lead_email": body.get("leadEmail") or body.get("email"),
        "lead_first_name": body.get("firstName"),
        "lead_last_name": body.get("lastName"),
        "reply_body": body.get("replyBody"),
        "date": body.get("date") or body.get("createdAt"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.lemlist_webhook",
    name="Lemlist",
    description=(
        "Fires when Lemlist posts a per-email event (bounced, clicked, "
        "opened, replied, sent, interested, linkedin_replied, "
        "not_interested). Verified via bare-secret compare against "
        "`x-webhook-token`."
    ),
    icon_slug="lemlist",
    color="#1c1c1c",
    provider="lemlist_webhook",
    signature=SignatureSpec(
        scheme="gitlab_token",
        header_name="x-webhook-token",
        secret_field="secret",
        prefix="",
    ),
    event_header="x-lemlist-event",
    event_body_path="type",
    events=[
        WebhookEvent(value="emailsBounced", label="Email Bounced"),
        WebhookEvent(value="emailsClicked", label="Email Clicked"),
        WebhookEvent(value="emailsOpened", label="Email Opened"),
        WebhookEvent(value="emailsReplied", label="Email Replied"),
        WebhookEvent(value="emailsSent", label="Email Sent"),
        WebhookEvent(value="emailsInterested", label="Lead Interested"),
        WebhookEvent(value="emailsNotInterested", label="Lead Not Interested"),
        WebhookEvent(value="linkedinReplied", label="LinkedIn Replied"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "type", "type": "string"},
        {"label": "campaign_id", "type": "string"},
        {"label": "lead_email", "type": "string"},
        {"label": "reply_body", "type": "string"},
        {"label": "date", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
