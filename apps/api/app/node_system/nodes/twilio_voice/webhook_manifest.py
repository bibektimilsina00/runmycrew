"""Twilio Voice webhook trigger — manifest form.

Twilio signs webhook deliveries with `X-Twilio-Signature`: HMAC-SHA1
of URL + sorted-form-params (or JSON body), base64. The receiver's
`twilio` scheme validates via the URL kwarg it threads through.

Twilio Voice sends the call status/event as form-encoded body — the
event field is `CallStatus` (`initiated`/`ringing`/`answered`/
`completed`/`busy`/`failed`/`no-answer`).

Setup
  1. Twilio Console → Phone Numbers → Manage → Active Numbers →
     Voice Configuration → set the *Status Callback URL* to
     `${BASE_URL}/api/v1/webhooks/twilio_voice/${wf}/${node}`.
  2. Copy the Twilio *Auth Token* into this trigger's Secret field.
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
        "event": event_type or body.get("CallStatus") or "",
        "delivery": delivery_id or body.get("CallSid") or "",
        "call_sid": body.get("CallSid"),
        "account_sid": body.get("AccountSid"),
        "from_number": body.get("From"),
        "to_number": body.get("To"),
        "call_status": body.get("CallStatus"),
        "call_duration": body.get("CallDuration"),
        "direction": body.get("Direction"),
        "answered_by": body.get("AnsweredBy"),
        "recording_url": body.get("RecordingUrl"),
        "recording_sid": body.get("RecordingSid"),
        "recording_duration": body.get("RecordingDuration"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.twilio_voice",
    name="Twilio Voice Webhook",
    description=(
        "Fires when Twilio posts a Voice call status callback (initiated, "
        "ringing, answered, completed, ...). Verified via HMAC-SHA1 of "
        "URL + sorted-form-params in `X-Twilio-Signature`."
    ),
    icon_slug="twilio",
    color="#F22F46",
    provider="twilio_voice",
    signature=SignatureSpec(
        scheme="twilio",
        header_name="X-Twilio-Signature",
        secret_field="secret",
        prefix="",
    ),
    event_header="X-Twilio-Voice-Event",
    event_body_path="CallStatus",
    events=[
        WebhookEvent(value="initiated", label="Initiated"),
        WebhookEvent(value="ringing", label="Ringing"),
        WebhookEvent(value="answered", label="Answered"),
        WebhookEvent(value="in-progress", label="In Progress"),
        WebhookEvent(value="completed", label="Completed"),
        WebhookEvent(value="busy", label="Busy"),
        WebhookEvent(value="failed", label="Failed"),
        WebhookEvent(value="no-answer", label="No Answer"),
        WebhookEvent(value="canceled", label="Canceled"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "call_sid", "type": "string"},
        {"label": "from_number", "type": "string"},
        {"label": "to_number", "type": "string"},
        {"label": "call_status", "type": "string"},
        {"label": "call_duration", "type": "string"},
        {"label": "direction", "type": "string"},
        {"label": "recording_url", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
