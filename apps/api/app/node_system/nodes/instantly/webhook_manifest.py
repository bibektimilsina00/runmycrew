"""Instantly webhook trigger — manifest form.

Instantly.ai delivers per-email events (opens, clicks, replies,
bounces, lead-status changes) via webhook. Signed with HMAC-SHA256
over the raw body under a user-configured secret. Event kind lives
in the body's `event_type` field — the scaffold routes to it via
`event_body_path`.

Setup
  1. Add this trigger to your workflow.
  2. Instantly Console → Integrations → Webhooks → Add Webhook.
  3. URL: `${BASE_URL}/api/v1/webhooks/instantly/${wf}/${node}`.
  4. Copy the generated *webhook secret* into this trigger's Secret field.
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
    data = body.get("data") or body
    return {
        "event": event_type or body.get("event_type") or "",
        "delivery": delivery_id or body.get("id") or "",
        "event_type": body.get("event_type"),
        "workspace_id": body.get("workspace"),
        "campaign_id": data.get("campaign_id") or data.get("campaign"),
        "lead_id": data.get("lead_id"),
        "lead_email": data.get("email") or data.get("lead_email"),
        "message_id": data.get("message_id"),
        "reply_content": data.get("reply_content"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.instantly_webhook",
    name="Instantly Webhook",
    description=(
        "Fires when Instantly posts a per-email event (opens, clicks, "
        "replies, bounces, lead status changes). Verified via HMAC-SHA256 "
        "in `x-instantly-signature`."
    ),
    icon_slug="instantly",
    color="#1c1c1c",
    provider="instantly_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="x-instantly-signature",
        secret_field="secret",
        prefix="",
    ),
    # Instantly doesn't ship an event header — event kind lives in the
    # JSON body's `event_type` field. The scaffold's body-path routing
    # extracts it before running the event filter.
    event_header="x-instantly-event",
    event_body_path="event_type",
    events=[
        WebhookEvent(value="email_sent", label="Email Sent"),
        WebhookEvent(value="email_opened", label="Email Opened"),
        WebhookEvent(value="email_bounced", label="Email Bounced"),
        WebhookEvent(value="link_clicked", label="Link Clicked"),
        WebhookEvent(value="reply_received", label="Reply Received"),
        WebhookEvent(value="auto_reply_received", label="Auto-Reply Received"),
        WebhookEvent(value="lead_interested", label="Lead Interested"),
        WebhookEvent(value="lead_meeting_booked", label="Meeting Booked"),
        WebhookEvent(value="lead_meeting_completed", label="Meeting Completed"),
        WebhookEvent(value="lead_neutral", label="Lead Neutral"),
        WebhookEvent(value="lead_no_show", label="Lead No Show"),
        WebhookEvent(value="lead_not_interested", label="Lead Not Interested"),
        WebhookEvent(value="lead_out_of_office", label="Lead Out of Office"),
        WebhookEvent(value="lead_unsubscribed", label="Lead Unsubscribed"),
        WebhookEvent(value="lead_wrong_person", label="Lead Wrong Person"),
        WebhookEvent(value="lead_closed", label="Lead Closed"),
        WebhookEvent(value="campaign_completed", label="Campaign Completed"),
        WebhookEvent(value="account_error", label="Account Error"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "campaign_id", "type": "string"},
        {"label": "lead_id", "type": "string"},
        {"label": "lead_email", "type": "string"},
        {"label": "message_id", "type": "string"},
        {"label": "reply_content", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
