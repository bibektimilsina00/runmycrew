"""Manifest schema for the webhook-trigger scaffold.

A webhook trigger is the *receiver* end of the contract — the
provider POSTs deliveries at our URL, we verify signature, filter by
event header, then dispatch a workflow execution. The manifest carries:

  - **Identity / brand** — same icon + color slots as the REST + polling
    manifests so a provider's full surface looks consistent in the UI.
  - **Signature scheme** — name + header + secret-field. The receiver
    looks the scheme up in `signature_schemes.py` and HMACs the raw
    body before doing anything else.
  - **Event header + dropdown** — the manifest declares which header
    carries the event name (`X-GitHub-Event`, `X-GitLab-Event`, …) and
    the list of events the inspector exposes for the event filter.
  - **Payload shape** — optional JSONPath-style projection so every
    delivery surfaces as a stable `{repository, sender, action, body}`
    shape regardless of provider quirks.

The factory turns one of these into a registered `BaseNode`. The
**receiver** (`features/webhooks/router.py`) doesn't need the node at
runtime — it reads the manifest registry by provider id, finds the
trigger node on the target workflow, verifies, and dispatches. Keeps
the receiver provider-agnostic.
"""

from __future__ import annotations

from collections.abc import Callable
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field

from apps.api.app.node_system.scaffolds.rest_manifest import FieldSpec

# ── signature schemes ────────────────────────────────────────────────


SignatureScheme = Literal[
    "hmac_sha256",
    "hmac_sha1",
    # base64-encoded HMAC-SHA256 with optional prefix strip. Used by
    # Microsoft Teams outgoing webhooks (`Authorization: HMAC {digest}`)
    # and any provider that ships sha256 base64 instead of hex.
    "hmac_sha256_b64",
    "stripe",
    "shopify",
    # `gitlab_token` is a bare-secret compare (no HMAC) since GitLab
    # ships the secret itself in `X-Gitlab-Token`. Verifier lives in
    # `features/webhooks/signature_schemes.py`.
    "gitlab_token",
    # Twilio signs `URL + sorted-form-params` under HMAC-SHA1, base64.
    # Needs the request URL — the verifier reads it from the extra
    # `url` kwarg the router now threads through.
    "twilio",
    # Webflow v2 signs `timestamp:body` under HMAC-SHA256 hex. Ships
    # the timestamp in `x-webflow-timestamp`. Includes an anti-replay
    # tolerance window like Stripe.
    "webflow",
    "none",
]


class SignatureSpec(BaseModel):
    """Where the signature lives + which scheme to verify it under.

    The receiver pulls the header named by `header_name`, strips
    `prefix`, and runs the named scheme. `secret_field` names the
    trigger-node property holding the HMAC secret.
    """

    model_config = ConfigDict(extra="forbid")

    scheme: SignatureScheme = "hmac_sha256"
    header_name: str = "X-Hub-Signature-256"
    secret_field: str = "secret"
    prefix: str = "sha256="


class WebhookEvent(BaseModel):
    """One row in the inspector's event-filter dropdown.

    The receiver compares the request's `event_header` value against
    `value` to decide whether to dispatch. Pick the magic `*` value to
    mean "any event".
    """

    model_config = ConfigDict(extra="forbid")

    value: str
    label: str


EVENT_ANY = "*"


# ── manifest ─────────────────────────────────────────────────────────


# Function that projects a webhook payload into the canonical shape the
# trigger output schema advertises. Receives the parsed body + raw
# event_type + delivery_id; returns the dict the workflow will see as
# its trigger input. Defaults to a generic flattener (see
# `webhook_node_factory._default_shape`) so most manifests don't need
# to set this.
PayloadShape = Callable[[Any, str, str], dict[str, Any]]


class WebhookTriggerManifest(BaseModel):
    """Top-level manifest for a webhook-trigger node."""

    model_config = ConfigDict(extra="forbid", arbitrary_types_allowed=True)

    # Identity.
    type: str  # e.g. "trigger.gitlab_webhook"
    name: str
    category: str = "trigger"
    description: str
    icon_slug: str | None = None
    color: str = "#1c1c1c"

    # `provider` is the URL segment + receiver dispatch key —
    # `/webhooks/<provider>/{workflow_id}/{node_id}`.
    provider: str

    # Verification.
    signature: SignatureSpec = Field(default_factory=SignatureSpec)
    event_header: str = "X-GitHub-Event"
    # Optional body path — dotted key path into the parsed JSON body
    # where the event kind lives. Used when the provider doesn't ship a
    # dedicated event header (Instantly's `event_type`, Lemlist's
    # `type`, Emailbison's `event`). Receiver tries `event_header`
    # first, falls back to this path if it comes back empty.
    #
    # Simple dotted paths only: "event_type", "meta.event", or "kind".
    # No array indexing.
    event_body_path: str | None = None

    # Inspector.
    credential_type: str | list[str] | None = None
    # Extra inspector fields beyond the implicit credential / event /
    # secret rows. E.g. owner, repo, project_id — anything the user
    # needs to confirm the URL is wired to the right resource. These
    # are display-only as far as the receiver is concerned; the URL +
    # secret are the source of truth.
    extra_fields: list[FieldSpec] = Field(default_factory=list)
    events: list[WebhookEvent] = Field(default_factory=list)
    # When True the manifest forces the receiver to require a secret on
    # the trigger node. Almost always True — but some providers (Slack
    # Events API) do their own verification before the body is parsed.
    require_secret: bool = True

    # Output projection.
    payload_shape: PayloadShape | None = None
    outputs_schema: list[dict[str, Any]] = Field(default_factory=list)


# ── module registry ──────────────────────────────────────────────────


_REGISTRY: dict[str, WebhookTriggerManifest] = {}


def register_webhook_manifest(manifest: WebhookTriggerManifest) -> None:
    """Stash a manifest under its `provider` so the receiver router can
    look it up without importing the node module."""
    _REGISTRY[manifest.provider] = manifest


def get_webhook_manifest(provider: str) -> WebhookTriggerManifest | None:
    return _REGISTRY.get(provider)


def all_webhook_manifests() -> dict[str, WebhookTriggerManifest]:
    return dict(_REGISTRY)
