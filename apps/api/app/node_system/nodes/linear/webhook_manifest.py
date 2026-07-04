"""Linear webhook trigger — manifest form.

Linear signs webhook deliveries with HMAC-SHA256 hex in
`Linear-Signature`. Event kind is composed from body's `type` (e.g.
`Issue`, `Comment`, `Cycle`) and `action` (`create`, `update`,
`remove`). We surface a composite `{type}.{action}` via a
`_composite_event` field the scaffold's body-path can read.

Full sim parity (14 events): Issue/Comment/Cycle/Project/Label/
CustomerRequest × create+update, plus IssueRemoved,
ProjectUpdateCreated. Delete/remove events unlock the deferred sim
events from Phase 4.2 polling.

Setup
  1. Linear Settings → API → Webhooks → New webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/linear_webhook/${wf}/${node}`.
  3. Copy the signing secret into this trigger's Secret field.
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
    data = body.get("data") or {}
    return {
        "event": event_type or f"{body.get('type', '')}.{body.get('action', '')}".strip("."),
        "delivery": delivery_id or body.get("webhookId") or "",
        "type": body.get("type"),
        "action": body.get("action"),
        "webhook_id": body.get("webhookId"),
        "organization_id": body.get("organizationId"),
        "id": data.get("id"),
        "identifier": data.get("identifier"),
        "title": data.get("title") or data.get("body") or data.get("name"),
        "url": data.get("url"),
        "priority": data.get("priority"),
        "state_name": (data.get("state") or {}).get("name")
        if isinstance(data.get("state"), dict)
        else None,
        "assignee_name": (data.get("assignee") or {}).get("name")
        if isinstance(data.get("assignee"), dict)
        else None,
        "team_key": (data.get("team") or {}).get("key")
        if isinstance(data.get("team"), dict)
        else None,
        "created_at": data.get("createdAt"),
        "updated_at": data.get("updatedAt"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.linear_webhook",
    name="Linear Webhook",
    description=(
        "Fires when Linear posts a webhook delivery. Full sim parity "
        "including delete/remove events (unlocks the events the Phase 4.2 "
        "poller couldn't observe). HMAC-SHA256 verified via `Linear-Signature`."
    ),
    icon_slug="linear",
    color="#1c1c1c",
    provider="linear_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha256",
        header_name="Linear-Signature",
        secret_field="secret",
        prefix="",
    ),
    # Linear composes event kind from body {type, action}. Scaffold's
    # list-form event_body_path joins with "." — gives us `Issue.create`.
    event_header="Linear-Event",
    event_body_path=["type", "action"],
    events=[
        WebhookEvent(value="Issue.create", label="Issue Created"),
        WebhookEvent(value="Issue.update", label="Issue Updated"),
        WebhookEvent(value="Issue.remove", label="Issue Removed"),
        WebhookEvent(value="Comment.create", label="Comment Created"),
        WebhookEvent(value="Comment.update", label="Comment Updated"),
        WebhookEvent(value="Cycle.create", label="Cycle Created"),
        WebhookEvent(value="Cycle.update", label="Cycle Updated"),
        WebhookEvent(value="Project.create", label="Project Created"),
        WebhookEvent(value="ProjectUpdate.create", label="Project Update Created"),
        WebhookEvent(value="IssueLabel.create", label="Label Created"),
        WebhookEvent(value="IssueLabel.update", label="Label Updated"),
        WebhookEvent(value="CustomerRequest.create", label="Customer Request Created"),
        WebhookEvent(value="CustomerRequest.update", label="Customer Request Updated"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "type", "type": "string"},
        {"label": "action", "type": "string"},
        {"label": "id", "type": "string"},
        {"label": "identifier", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "state_name", "type": "string"},
        {"label": "assignee_name", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
