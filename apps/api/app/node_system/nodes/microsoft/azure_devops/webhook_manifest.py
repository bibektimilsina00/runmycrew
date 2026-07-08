"""Azure DevOps webhook trigger — manifest form.

ADO service hooks POST JSON deliveries with Basic-auth in the
`Authorization` header. There is no HMAC digest — the user configures
a username/password when creating the service hook, and ADO sends
`Authorization: Basic base64(user:password)` on every delivery.

We reuse the `gitlab_token` scheme (bare-secret compare via
`hmac.compare_digest`) — the user pastes the full
`Basic base64(user:password)` string into the trigger's secret field.
Both sides then hold the same opaque value and constant-time compare.

Event routing: ADO puts the event kind in the JSON body's
`eventType` field, not a header. To keep the scaffold receiver header-
based, we surface the event via the `X-ADO-Event` header — ADO
doesn't send it, so every delivery is treated as "any". The manifest
still lists common event types for the dropdown, but the receiver
only routes when the header is set (i.e. by a proxy that lifts
`eventType` up).

Setup
  1. Add this trigger to your workflow.
  2. Azure DevOps → Project Settings → Service hooks → Web Hooks.
  3. Trigger: pick the ADO event (workitem.created, git.push, …).
  4. Settings → URL: `${BASE_URL}/api/v1/webhooks/azure_devops/${workflow_id}/${node_id}`.
  5. HTTP headers → username / password. Paste
     `Basic base64(user:password)` (the same encoded string) into
     this node's Secret field.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.nodes.microsoft.azure_devops import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    """ADO deliveries carry `eventType`, `resource`, `resourceContainers`
    at the top level. Surface the useful bits without dropping the raw
    body — downstream nodes may want details we didn't extract."""
    body = payload if isinstance(payload, dict) else {}
    resource = body.get("resource") or {}
    return {
        "event": event_type or body.get("eventType") or "",
        "delivery": delivery_id or body.get("id") or "",
        "event_type": body.get("eventType"),
        "resource_id": resource.get("id") or resource.get("workItemId"),
        "resource_url": resource.get("url"),
        "resource_title": resource.get("title")
        or (resource.get("fields") or {}).get("System.Title"),
        "sender": (body.get("createdBy") or {}).get("displayName"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.azure_devops_webhook",
    name=NAME,
    description=(
        "Fires when Azure DevOps posts a service-hook delivery. Configure "
        "Basic-auth on the ADO side and paste the same `Basic base64(...)` "
        "string into this node's Secret field."
    ),
    icon_slug=ICON_SLUG,
    color=COLOR,
    provider="azure_devops",
    signature=SignatureSpec(
        scheme="gitlab_token",
        header_name="Authorization",
        secret_field="secret",
        prefix="",
    ),
    # ADO doesn't ship the event kind in a header — `eventType` lives
    # inside the JSON body. Advanced users can put a proxy in front to
    # lift it into a header; without one, deliveries land under
    # "unknown" and the "Any event" dropdown option catches them.
    event_header="X-ADO-Event",
    extra_fields=[
        FieldSpec(
            name="organization",
            label="Organization (display only)",
            type="string",
            placeholder="my-org",
            description="Sanity-check label. URL + secret are what match this trigger to ADO.",
        ),
        FieldSpec(
            name="project",
            label="Project (display only)",
            type="string",
            placeholder="MyProject",
        ),
    ],
    events=[
        WebhookEvent(value="workitem.created", label="Work item created"),
        WebhookEvent(value="workitem.updated", label="Work item updated"),
        WebhookEvent(value="workitem.commented", label="Work item commented"),
        WebhookEvent(value="git.push", label="Code pushed"),
        WebhookEvent(value="git.pullrequest.created", label="Pull request created"),
        WebhookEvent(value="git.pullrequest.merged", label="Pull request merged"),
        WebhookEvent(value="build.complete", label="Build complete"),
        WebhookEvent(value="release.deployment.completed", label="Deployment completed"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "event_type", "type": "string"},
        {"label": "delivery", "type": "string"},
        {"label": "resource_id", "type": "string"},
        {"label": "resource_url", "type": "string"},
        {"label": "resource_title", "type": "string"},
        {"label": "sender", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
