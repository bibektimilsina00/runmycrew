"""GitLab webhook trigger — manifest form.

GitLab signs webhook deliveries with a *secret token* in the
`X-Gitlab-Token` header, not an HMAC digest. The token is the secret
itself — we compare directly. Different from GitHub's
`X-Hub-Signature-256` HMAC scheme but conceptually equivalent: a
shared secret the user pastes into both ends.

Since the scaffold's signature schemes assume HMAC, GitLab uses a
custom verifier registered against the `hmac_sha256` slot — the
manifest sets `prefix=""` and the verifier compares the raw header
value to the configured secret using `hmac.compare_digest` to avoid
timing leaks.

Event filter targets `X-Gitlab-Event` — values like `"Push Hook"`,
`"Merge Request Hook"`, `"Issue Hook"`. We surface the common ones in
the dropdown; users can drop down to "Any event" for novel ones.

Setup
  1. Add this trigger to your workflow.
  2. GitLab project → Settings → Webhooks → Add webhook.
  3. URL: `${BASE_URL}/api/v1/webhooks/gitlab/${workflow_id}/${node_id}`.
  4. Secret token: paste the value from this node's `secret` field.
  5. Tick the events you want — match against this node's `event` dropdown.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)

# ── payload shape ────────────────────────────────────────────────────


def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    """Project GitLab's payload into the same canonical shape the
    GitHub webhook node emits — keeps downstream nodes provider-agnostic.
    """
    body = payload if isinstance(payload, dict) else {}
    project = body.get("project") or {}
    user = body.get("user") or {}
    return {
        "event": event_type,
        "delivery": delivery_id,
        "object_kind": body.get("object_kind"),
        "repository": project.get("path_with_namespace") or project.get("name"),
        "sender": user.get("username") or body.get("user_username"),
        "body": body,
    }


# ── manifest ─────────────────────────────────────────────────────────


MANIFEST = WebhookTriggerManifest(
    type="trigger.gitlab_webhook",
    name="GitLab",
    description=(
        "Fires the instant GitLab posts a webhook delivery to your "
        "workflow URL. Pair with a project-level webhook configured "
        "in GitLab Settings → Webhooks."
    ),
    icon_slug="gitlab",
    color="#1c1c1c",
    provider="gitlab",
    signature=SignatureSpec(
        scheme="gitlab_token",
        header_name="X-Gitlab-Token",
        secret_field="secret",
        prefix="",
    ),
    event_header="X-Gitlab-Event",
    extra_fields=[
        FieldSpec(
            name="project",
            label="Project (display only)",
            type="string",
            placeholder="my-group/my-project",
            description=(
                "Sanity-check label. The URL + secret are what actually "
                "match this trigger to GitLab's deliveries."
            ),
        ),
    ],
    events=[
        WebhookEvent(value="Push Hook", label="Push"),
        WebhookEvent(value="Tag Push Hook", label="Tag push"),
        WebhookEvent(value="Issue Hook", label="Issue"),
        WebhookEvent(value="Note Hook", label="Comment"),
        WebhookEvent(value="Merge Request Hook", label="Merge request"),
        WebhookEvent(value="Wiki Page Hook", label="Wiki page"),
        WebhookEvent(value="Pipeline Hook", label="Pipeline"),
        WebhookEvent(value="Job Hook", label="Job"),
        WebhookEvent(value="Deployment Hook", label="Deployment"),
        WebhookEvent(value="Release Hook", label="Release"),
    ],
    payload_shape=_shape,
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "delivery", "type": "string"},
        {"label": "object_kind", "type": "string"},
        {"label": "repository", "type": "string"},
        {"label": "sender", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
