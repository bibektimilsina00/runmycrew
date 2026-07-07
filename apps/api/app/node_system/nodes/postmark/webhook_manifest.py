"""Postmark webhook trigger — manifest form.

Postmark signs webhook deliveries with base64(HMAC-SHA1(body)) in
`X-Postmark-Signature`. The scaffold's `hmac_sha1_b64` scheme covers
the shape.

Event kind lives in the JSON body's `RecordType` field
(`Delivery` / `Bounce` / `Open` / `Click` / `SpamComplaint` /
`SubscriptionChange` / `ManualSuppression`). Body-path routing.

Setup
  1. Postmark Server Settings → Webhooks → Add Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/postmark_webhook/${wf}/${node}`.
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
        "event": event_type or body.get("RecordType") or "",
        "delivery": delivery_id or body.get("MessageID") or "",
        "message_id": body.get("MessageID"),
        "record_type": body.get("RecordType"),
        "recipient": body.get("Recipient") or body.get("Email"),
        "email": body.get("Email"),
        "server_id": body.get("ServerID"),
        "message_stream": body.get("MessageStream"),
        "tag": body.get("Tag"),
        "delivered_at": body.get("DeliveredAt"),
        "bounce_type": body.get("Type"),
        "bounce_description": body.get("Description"),
        "click_link": body.get("OriginalLink"),
        "user_agent": (body.get("UserAgent") or (body.get("Client") or {}).get("Name")),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.postmark_webhook",
    name="Postmark",
    description=(
        "Fires when Postmark posts a delivery event (Delivery, Bounce, "
        "Open, Click, SpamComplaint, SubscriptionChange, ManualSuppression). "
        "Verified via base64 HMAC-SHA1 in `X-Postmark-Signature`."
    ),
    icon_slug="postmark",
    color="#1c1c1c",
    provider="postmark_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha1_b64",
        header_name="X-Postmark-Signature",
        secret_field="secret",
        prefix="",
    ),
    event_header="X-Postmark-Event",
    event_body_path="RecordType",
    events=[
        WebhookEvent(value="Delivery", label="Delivery"),
        WebhookEvent(value="Bounce", label="Bounce"),
        WebhookEvent(value="Open", label="Open"),
        WebhookEvent(value="Click", label="Click"),
        WebhookEvent(value="SpamComplaint", label="Spam Complaint"),
        WebhookEvent(value="SubscriptionChange", label="Subscription Change"),
        WebhookEvent(value="ManualSuppression", label="Manual Suppression"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "message_id", "type": "string"},
        {"label": "recipient", "type": "string"},
        {"label": "delivered_at", "type": "string"},
        {"label": "bounce_type", "type": "string"},
        {"label": "click_link", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
