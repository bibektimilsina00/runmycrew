"""Microsoft Teams outgoing webhook trigger — manifest form.

Teams' *outgoing webhooks* deliver adaptive-card messages posted to a
Teams channel that @-mentions the webhook. Auth: Teams computes
HMAC-SHA256 of the raw JSON body under a base64-decoded shared secret,
then ships `Authorization: HMAC {base64_digest}`.

Uses the shared `hmac_sha256_b64` scheme with the `HMAC ` prefix.

Note: Teams *incoming* webhooks (posting messages TO Teams) are handled
by the action node — those don't fire back to us. This trigger is for
outgoing-webhooks (bot-style commands entered in a channel).

Setup
  1. Team → channel → "..." → Connectors → Outgoing Webhook.
  2. Callback URL: `${BASE_URL}/api/v1/webhooks/microsoft_teams/${wf}/${node}`.
  3. Copy the generated security token. That's what Teams will HMAC
     the body under — paste it into this trigger's Secret field.
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
    frm = body.get("from") or {}
    channel = (body.get("channelData") or {}).get("channel") or {}
    return {
        "event": event_type or body.get("type") or "message",
        "delivery": delivery_id or body.get("id") or "",
        "text": body.get("text"),
        "from_name": frm.get("name"),
        "from_id": frm.get("id"),
        "conversation_id": (body.get("conversation") or {}).get("id"),
        "channel_id": channel.get("id"),
        "channel_name": channel.get("name"),
        "timestamp": body.get("timestamp"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.microsoft_teams_webhook",
    name="Microsoft Teams Webhook",
    description=(
        "Fires when a Teams channel outgoing-webhook delivers a message. "
        "Verifies `Authorization: HMAC {base64_sha256}` against the webhook "
        "security token you configured in Teams."
    ),
    icon_slug="microsoft_teams",
    color="#1c1c1c",
    provider="microsoft_teams",
    signature=SignatureSpec(
        scheme="hmac_sha256_b64",
        header_name="Authorization",
        secret_field="secret",
        prefix="HMAC ",
    ),
    # Teams doesn't use an event-type header — outgoing webhooks
    # deliver a single "message" event kind.
    event_header="X-Teams-Event",
    events=[
        WebhookEvent(value="message", label="Message"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "text", "type": "string"},
        {"label": "from_name", "type": "string"},
        {"label": "from_id", "type": "string"},
        {"label": "conversation_id", "type": "string"},
        {"label": "channel_id", "type": "string"},
        {"label": "channel_name", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
