"""Twilio webhook trigger — manifest form.

Twilio delivers events (inbound SMS, call status callbacks, etc.) as
form-encoded POSTs. Signature scheme: HMAC-SHA1 of
`{full_delivery_url}{sorted key=value form params concatenated}` under
the Twilio *auth token* as key, base64. Header: `X-Twilio-Signature`.

Because the signature includes the exact URL Twilio saw, any reverse
proxy in front of us has to preserve `X-Forwarded-Proto` and
`X-Forwarded-Host` — otherwise the digest we compute won't match.
Uvicorn's `--proxy-headers` flag covers this.

Twilio doesn't set an event-type header — deliveries route by *URL*
on Twilio's side (one URL per callback endpoint). We expose a
dropdown for documentation only; the receiver treats every delivery
as "any event" unless the user proxies-in a custom header.

Setup
  1. Twilio Console → Phone Numbers or Studio Flow → Messaging /
     Voice webhook URL: `${BASE_URL}/api/v1/webhooks/twilio/${wf}/${node}`.
  2. Paste the **Auth Token** from Twilio Console → Account → Auth
     Token into the trigger's Secret field.
"""

from __future__ import annotations

import contextlib
from typing import Any
from urllib.parse import parse_qsl

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    """Twilio form deliveries are dicts of MessageSid / From / To /
    Body / etc. When the JSON parse in the receiver fails, `payload`
    holds `{"raw": "<form string>"}` — reparse it here so downstream
    nodes always see a structured shape."""
    body = payload if isinstance(payload, dict) else {}
    if "raw" in body and isinstance(body["raw"], str):
        with contextlib.suppress(Exception):
            body = dict(parse_qsl(body["raw"], keep_blank_values=True))
    return {
        "event": event_type or body.get("EventType") or "",
        "delivery": delivery_id or body.get("MessageSid") or body.get("CallSid") or "",
        "from": body.get("From"),
        "to": body.get("To"),
        "text": body.get("Body"),
        "message_sid": body.get("MessageSid"),
        "call_sid": body.get("CallSid"),
        "status": body.get("MessageStatus") or body.get("CallStatus"),
        "account_sid": body.get("AccountSid"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.twilio_webhook",
    name="Twilio Webhook",
    description=(
        "Receives Twilio deliveries — inbound SMS, call status callbacks, "
        "Studio Flow events. Signature verified via HMAC-SHA1 of URL + form "
        "params (Twilio's `X-Twilio-Signature`)."
    ),
    icon_slug="twilio",
    color="#1c1c1c",
    provider="twilio",
    signature=SignatureSpec(
        scheme="twilio",
        header_name="X-Twilio-Signature",
        secret_field="secret",
        prefix="",
    ),
    # Twilio does not send an event-type header — the URL is the
    # routing signal on their side. Keeping the event dropdown for
    # display only; deliveries fall through the "Any event" branch.
    event_header="X-Twilio-Event-Type",
    extra_fields=[
        FieldSpec(
            name="phone_number",
            label="Phone Number (display only)",
            type="string",
            placeholder="+15551234567",
            description="Reminder of which Twilio number posts to this trigger.",
        ),
    ],
    events=[
        WebhookEvent(value="message.inbound", label="Inbound SMS / MMS"),
        WebhookEvent(value="message.status", label="Message Status Callback"),
        WebhookEvent(value="voice.status", label="Voice Status Callback"),
        WebhookEvent(value="studio.flow", label="Studio Flow Event"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "from", "type": "string"},
        {"label": "to", "type": "string"},
        {"label": "text", "type": "string"},
        {"label": "message_sid", "type": "string"},
        {"label": "call_sid", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
