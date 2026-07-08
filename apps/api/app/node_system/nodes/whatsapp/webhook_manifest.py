"""WhatsApp Business Cloud webhook trigger — manifest form.

Meta's WhatsApp Cloud API signs webhook deliveries with HMAC-SHA256
hex, prefixed with `sha256=`, in `X-Hub-Signature-256`. Event kind
lives in the body under
`entry[0].changes[0].value.messages[0].type` — the receiver flattens
by dotted-path and matches against the configured event value.

Setup
  1. Meta Developer Portal → App → WhatsApp → Configuration → Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/whatsapp/${wf}/${node}`.
  3. Copy the *app secret* into this trigger's Secret field.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _first(coll: Any) -> Any:
    if isinstance(coll, list) and coll:
        return coll[0]
    return {}


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    entry = _first(body.get("entry"))
    change = _first(entry.get("changes"))
    value = change.get("value") or {}
    message = _first(value.get("messages"))
    contact = _first(value.get("contacts"))
    status = _first(value.get("statuses"))
    return {
        "event": event_type or message.get("type") or status.get("status") or "message",
        "delivery": delivery_id or message.get("id") or status.get("id") or "",
        "from": message.get("from") or contact.get("wa_id"),
        "phone_number_id": value.get("metadata", {}).get("phone_number_id"),
        "display_phone_number": value.get("metadata", {}).get("display_phone_number"),
        "message_id": message.get("id"),
        "message_type": message.get("type"),
        "text": message.get("text", {}).get("body")
        if isinstance(message.get("text"), dict)
        else None,
        "timestamp": message.get("timestamp") or status.get("timestamp"),
        "contact_name": contact.get("profile", {}).get("name")
        if isinstance(contact.get("profile"), dict)
        else None,
        "status": status.get("status"),
        "recipient_id": status.get("recipient_id"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.whatsapp",
    name="WhatsApp",
    description=(
        "Fires when Meta's WhatsApp Cloud API posts a message or status "
        "update. Verified via HMAC-SHA256 in `X-Hub-Signature-256`."
    ),
    icon_slug="whatsapp",
    color="#ffffff",
    provider="whatsapp",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="X-Hub-Signature-256",
        secret_field="secret",
        prefix="sha256=",
    ),
    event_header="X-WhatsApp-Event",
    event_body_path=[
        "entry.0.changes.0.value.messages.0.type",
        "entry.0.changes.0.value.statuses.0.status",
    ],
    events=[
        WebhookEvent(value="text", label="Text Message"),
        WebhookEvent(value="image", label="Image Message"),
        WebhookEvent(value="video", label="Video Message"),
        WebhookEvent(value="document", label="Document Message"),
        WebhookEvent(value="audio", label="Audio Message"),
        WebhookEvent(value="location", label="Location Message"),
        WebhookEvent(value="contacts", label="Contacts Message"),
        WebhookEvent(value="interactive", label="Interactive Reply"),
        WebhookEvent(value="button", label="Button Reply"),
        WebhookEvent(value="sent", label="Message Sent (status)"),
        WebhookEvent(value="delivered", label="Message Delivered (status)"),
        WebhookEvent(value="read", label="Message Read (status)"),
        WebhookEvent(value="failed", label="Message Failed (status)"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "from", "type": "string"},
        {"label": "message_id", "type": "string"},
        {"label": "text", "type": "string"},
        {"label": "message_type", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "phone_number_id", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
