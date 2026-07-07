"""Vercel webhook trigger — manifest form.

Vercel signs webhook deliveries with HMAC-SHA1 hex in
`x-vercel-signature` (no prefix). Event kind lives in the JSON body's
`type` field (e.g. `deployment.created`, `deployment.error`).

Full sim parity (7 events): deployment.created / .ready / .canceled /
.error / .succeeded / .promoted, plus project.created.

Setup
  1. Vercel Team Settings → Webhooks → Create Webhook.
  2. URL: `${BASE_URL}/api/v1/webhooks/vercel_webhook/${wf}/${node}`.
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
    payload_data = body.get("payload") or {}
    deployment = payload_data.get("deployment") or {}
    # `project` may be a full object (deployment events) or a bare id
    # string (project.created on some Vercel plans). Normalize to a
    # dict so `.get()` doesn't blow up on the string form.
    raw_project = payload_data.get("project")
    project = raw_project if isinstance(raw_project, dict) else {}
    project_id_from_string = raw_project if isinstance(raw_project, str) else None
    team = body.get("team") or {}
    user = body.get("user") or {}
    return {
        "event": event_type or body.get("type") or "",
        "delivery": delivery_id or body.get("id") or "",
        "type": body.get("type"),
        "team_id": team.get("id"),
        "user_id": user.get("id"),
        "deployment_id": deployment.get("id"),
        "deployment_url": deployment.get("url"),
        "deployment_state": payload_data.get("target") or deployment.get("state"),
        "project_id": project.get("id") or project_id_from_string,
        "project_name": project.get("name") or payload_data.get("name"),
        "region": payload_data.get("region"),
        "commit_sha": ((payload_data.get("deployment") or {}).get("meta") or {}).get(
            "githubCommitSha"
        ),
        "commit_message": ((payload_data.get("deployment") or {}).get("meta") or {}).get(
            "githubCommitMessage"
        ),
        "created_at": body.get("createdAt"),
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.vercel_webhook",
    name="Vercel",
    description=(
        "Fires when Vercel posts a webhook delivery — deployment lifecycle, "
        "project creation. HMAC-SHA1 verified via `x-vercel-signature`."
    ),
    icon_slug="vercel",
    color="#1c1c1c",
    provider="vercel_webhook",
    signature=SignatureSpec(
        scheme="hmac_sha1",
        header_name="x-vercel-signature",
        secret_field="secret",
        prefix="",
    ),
    event_header="x-vercel-event",
    event_body_path="type",
    events=[
        WebhookEvent(value="deployment.created", label="Deployment Created"),
        WebhookEvent(value="deployment.succeeded", label="Deployment Succeeded"),
        WebhookEvent(value="deployment.ready", label="Deployment Ready"),
        WebhookEvent(value="deployment.canceled", label="Deployment Canceled"),
        WebhookEvent(value="deployment.error", label="Deployment Error"),
        WebhookEvent(value="deployment.promoted", label="Deployment Promoted"),
        WebhookEvent(value="project.created", label="Project Created"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "deployment_id", "type": "string"},
        {"label": "deployment_url", "type": "string"},
        {"label": "deployment_state", "type": "string"},
        {"label": "project_id", "type": "string"},
        {"label": "project_name", "type": "string"},
        {"label": "commit_sha", "type": "string"},
        {"label": "commit_message", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
