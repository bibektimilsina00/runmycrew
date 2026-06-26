---
name: new-integration
description: Scaffold a complete integration via the manifest scaffolds. Action node, polling trigger, webhook trigger — pick any combination. Emits manifest + entry + registry line + credential provider + smoke test. Usage:&nbsp;`/new-integration`
---

# new-integration skill

Phase 0 of the sim-parity roadmap shipped three scaffolds:

| Scaffold | File | Builds |
|---|---|---|
| REST action | `apps/api/app/node_system/scaffolds/rest_node_factory.py` | `action.<slug>` |
| Polling trigger | `apps/api/app/node_system/scaffolds/polling_node_factory.py` | `trigger.<slug>` |
| Webhook trigger | `apps/api/app/node_system/scaffolds/webhook_node_factory.py` | `trigger.<slug>_webhook` |

This skill drives all three. New REST integration ≈ one manifest file +
one entry line + one registry line. No router edits, no service edits,
no shared-state plumbing.

---

## Ask the user

1. **Slug** — snake_case, lowercase. Becomes the node namespace and provider id (`firecrawl`, `gitlab`, `notion`).
2. **Display name** — title case (`Firecrawl`, `Notion`).
3. **What it does** — one-sentence description for the inspector / node-picker tile.
4. **Auth type** — `apikey` | `oauth` | `none`.
   - `apikey`: stash a key in the credential vault, manifest reads `credential.api_key`.
   - `oauth`: bigger lift — needs an OAuth provider in `credential_manager/oauth/flow.py`. Manifest reads `credential.access_token`.
   - `none`: public-read API, no credential row.
5. **Icon slug** — theSVG slug (`firecrawl`, `gitlab`, `notion`). Optional — defaults to `Circle`.
6. **Color** — tile background hex. `#1c1c1c` for dark/monochrome marks, `#ffffff` for full-color brand marks.
7. **Base URL** — concrete request URL is `{base_url} + {op.path}`. For GraphQL providers, set this to the REST root and use custom handlers.
8. **Surfaces** — pick any combination:
   - `action` — REST or GraphQL via the REST scaffold.
   - `poll` — polling trigger via the polling scaffold.
   - `webhook` — webhook trigger via the webhook scaffold.
9. **Ops** (only if `action`) — comma-separated op slugs (`scrape, crawl, map`).
10. **Events** (only if `poll` or `webhook`) — comma-separated event slugs (`new_issue, new_pr, new_comment`).

Confirm everything before generating. Show the user the file list.

---

## Generate

### Files to create

```
apps/api/app/node_system/nodes/<slug>/
  __init__.py                                  (empty)
  manifest.py                                  ← action manifest        (only if 'action')
  <slug>_node.py                               ← action entry           (only if 'action')
  trigger_manifest.py                          ← polling manifest       (only if 'poll')
  <slug>_trigger.py                            ← polling entry          (only if 'poll')
  webhook_manifest.py                          ← webhook manifest       (only if 'webhook')
  <slug>_webhook.py                            ← webhook entry          (only if 'webhook')
```

Edit:

- `apps/api/app/node_system/registry/registry.py` — import + register every emitted node.
- `apps/api/app/credential_manager/api_keys.py` — append `APIKeyProvider` entry (only `apikey` auth).
- `apps/api/app/credential_manager/oauth/flow.py` — append `<Name>OAuthProvider` (only `oauth` auth — heavier lift, see template at end).
- `apps/api/app/execution_engine/scheduler/integration_polling.py` — add import to `eager_register_polling_providers()` (only when `poll` is in the surfaces).

Touch:

- `apps/api/tests/fixtures/node_metadata_snapshot.json` — refreshed by running the snapshot test with `RMC_UPDATE_NODE_SNAPSHOTS=1`.

---

## Manifest templates

### Action manifest (`manifest.py`)

```python
"""<Display Name> action node — manifest form.

<one-line description of what makes this provider's API shape interesting,
or 'pure declarative REST' if there's nothing special>.
"""

from __future__ import annotations

from typing import Any  # only if you write builders/flatteners

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    register_flatten,  # only if you register an output flatten
)


# ── output flatteners ────────────────────────────────────────────────
# Only if at least one op needs output shaping. Register by name so the
# manifest stays pure-data; the factory looks the name up at runtime.

def _flatten_<op_id>(body: Any) -> dict[str, Any]:
    """Project <provider>'s <op> response into the node's output shape."""
    if not isinstance(body, dict):
        return {}
    return {
        "id": body.get("id"),
        # ...
    }


register_flatten("<slug>.<op_id>", _flatten_<op_id>)


# ── query / body builders ────────────────────────────────────────────
# Only when a declarative `query_fields` / `body_fields` list won't
# capture the API quirk (rename, envelope, computed values).

def _<op_id>_params(props: Any) -> dict[str, Any]:
    return {"<ApiName>": getattr(props, "<our_field>", None)}


# ── manifest ─────────────────────────────────────────────────────────


MANIFEST = ProviderManifest(
    type="action.<slug>",
    name="<Display Name>",
    category="integration",
    description="<one sentence — what the node does>",
    icon_slug="<icon_slug>",
    color="<hex>",
    base_url="<base_url>",

    # auth=apikey  → credential_type="<slug>_api_key", token_field=["api_key"]
    # auth=oauth   → credential_type="<slug>_oauth",   token_field=["access_token"]
    # auth=none    → credential_type=None,             public_ops=[<all ops>]
    credential_type="<slug>_api_key",
    token_field=["api_key"],
    auth="bearer",
    # auth_header_name="Authorization",
    # auth_value_template="Bearer {token}",
    # extra_headers={"X-Foo": "bar"},

    public_ops=[],

    fields=[
        FieldSpec(name="<field>", label="<Label>", type="string", required=True),
        # FieldSpec(..., mode="advanced") for less-used props.
        # FieldSpec(..., type="json") for free-form dicts.
        # FieldSpec(..., load_options_url="/integrations/<slug>/<resource>",
        #              load_options_depends_on=["credential"]) for dropdowns.
    ],

    operations=[
        # Declarative form
        OpSpec(
            id="<op_id>",
            label="<Op Label>",
            method="POST",
            path="/<resource>",
            visible_fields=["<field>"],
            # query_fields=["page", "per_page"],
            # body_fields=["<field>"],
            # body_template={"static": "value", "templated": "{<field>}"},
            # query_builder=_<op_id>_params,
            # body_builder=_<op_id>_body,
            # output_flatten="<slug>.<op_id>",
            # success_payload_template={"deleted": True, "id": "{<id_field>}"},
        ),
        # Custom handler form — use when declarative doesn't fit
        # (GraphQL, multi-call ops, signed requests).
        # OpSpec(
        #     id="<op_id>",
        #     label="<Op Label>",
        #     visible_fields=["<field>"],
        #     handler=_<op_id>_handler,
        # ),
    ],

    outputs_schema=[
        {"label": "id", "type": "string"},
        # ...
    ],
    allow_error=True,
)
```

### Action entry (`<slug>_node.py`)

```python
"""<Display Name> action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.<slug>.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

<Name>Node = build_rest_node(MANIFEST)
```

### Polling-trigger manifest (`trigger_manifest.py`)

```python
"""<Display Name> polling trigger — manifest form."""

from __future__ import annotations

from typing import Any  # only if you write a custom diff/paginator

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


# Register a flattener for each event that needs output shaping.
def _flatten_item(item: Any) -> dict[str, Any]:
    return {"id": item.get("id"), "title": item.get("title")}


register_flatten("<slug>.item", _flatten_item)


MANIFEST = PollingTriggerManifest(
    type="trigger.<slug>",
    name="<Display Name>",
    description="<what fires the trigger>",
    icon_slug="<icon_slug>",
    color="<hex>",
    base_url="<base_url>",
    credential_type="<slug>_oauth",          # or "<slug>_api_key"
    token_field=["access_token"],            # or ["api_key"]
    auth="bearer",
    provider="<slug>",                        # scheduler tag
    default_poll_interval_seconds=60,
    common_fields=[
        # FieldSpec(name="owner", label="Owner", type="string", required=True),
    ],
    events=[
        PollingEvent(
            id="<event_id>",
            label="<Event Label>",
            list_path="/<resource>",
            # list_params={"state": "all"},
            strategy="known_ids",            # or "since_timestamp" or "last_sha"
            id_field="id",
            # timestamp_field="updated_at",  # only for since_timestamp
            flatten="<slug>.item",
            # filter_fn=lambda item, props: "pull_request" not in item,
            # diff_handler=_custom_diff,     # only when builtin strategies don't fit
            # extra_fields=["branch"],       # fields shown only for this event
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "event_type", "type": "string"},
    ],
    # paginate_fn=_walk_pages,               # only for multi-page list endpoints
)
```

### Polling entry (`<slug>_trigger.py`)

```python
"""<Display Name> polling trigger — built from a manifest via the polling scaffold."""

from apps.api.app.node_system.nodes.<slug>.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

<Name>TriggerNode = build_polling_trigger(MANIFEST)
```

After emitting the polling files, add the import to
`eager_register_polling_providers()` so worker processes see the
poller after restart:

```python
def eager_register_polling_providers() -> None:
    ...
    from apps.api.app.node_system.nodes.<slug> import (
        <slug>_trigger as _<slug>_trigger,  # noqa: F401
    )
```

### Webhook-trigger manifest (`webhook_manifest.py`)

```python
"""<Display Name> webhook trigger — manifest form."""

from __future__ import annotations

from typing import Any  # only if you write a custom payload_shape

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    SignatureSpec,
    WebhookEvent,
    WebhookTriggerManifest,
)


# Optional — custom payload projector. Default folds GitHub-shaped
# bodies into {repository, sender, body}; most providers need this
# rewritten.
def _shape(payload: Any, event_type: str, delivery_id: str) -> dict[str, Any]:
    body = payload if isinstance(payload, dict) else {}
    return {
        "event": event_type,
        "delivery": delivery_id,
        "repository": ...,
        "sender": ...,
        "body": body,
    }


MANIFEST = WebhookTriggerManifest(
    type="trigger.<slug>_webhook",
    name="<Display Name> Webhook",
    description="<one sentence — what GitHub/Stripe/etc. posts to the URL>",
    icon_slug="<icon_slug>",
    color="<hex>",
    provider="<slug>",                        # URL segment
    signature=SignatureSpec(
        scheme="hmac_sha256",                # or "hmac_sha1" | "stripe" | "shopify" | "gitlab_token" | "none"
        header_name="X-Hub-Signature-256",
        secret_field="secret",
        prefix="sha256=",
    ),
    event_header="X-<Slug>-Event",
    extra_fields=[
        # FieldSpec(name="project", label="Project", type="string"),
    ],
    events=[
        WebhookEvent(value="<event>", label="<Event Label>"),
    ],
    payload_shape=_shape,                    # omit to use the default GitHub-shaped projector
    outputs_schema=[
        {"label": "event", "type": "string"},
        {"label": "body", "type": "object"},
    ],
)
```

### Webhook entry (`<slug>_webhook.py`)

```python
"""<Display Name> webhook trigger — built from a manifest via the webhook scaffold."""

from apps.api.app.node_system.nodes.<slug>.webhook_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_webhook_trigger

<Name>WebhookTriggerNode = build_webhook_trigger(MANIFEST)
```

The webhook receiver router (`apps/api/app/features/webhooks/router.py`)
is already mounted at `/api/v1/webhooks/{provider}/{workflow_id}/{node_id}`
— no router edits needed.

---

## Credential providers

### API key (`credential_manager/api_keys.py`)

```python
"<slug>": APIKeyProvider(
    id="<slug>_api_key",
    name="<Display Name>",
    icon_slug="<icon_slug>",
    color="<hex>",
    description="<one-line>",
    hint="<prefix>...",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="<prefix>...",
        )
    ],
),
```

### OAuth (`credential_manager/oauth/flow.py`)

OAuth is heavier — needs a class with `id`, `name`, `type="oauth"`,
`description`, `icon_slug`, `color`, `scopes`, `get_authorization_url`,
`exchange_code`. Pattern: copy the `GitHubOAuthProvider` (or any
existing provider) and adapt. Also:

- Add `<NAME>_CLIENT_ID` + `<NAME>_CLIENT_SECRET` to
  `apps/api/app/core/config.py` and `.env.example`.
- Append `"<slug>": <Name>OAuthProvider()` to `OAUTH_PROVIDERS`.
- Manifest sets `credential_type="<slug>_oauth"` and
  `token_field=["access_token"]`.

OAuth scaffolding doesn't live in the manifest scaffold yet — Phase 2
of the roadmap (`docs/sim-parity-roadmap.md`) tackles the Microsoft +
AWS family with shared OAuth helpers. Until then, OAuth providers
copy from an existing one.

---

## Register

```python
# apps/api/app/node_system/registry/registry.py

from apps.api.app.node_system.nodes.<slug>.<slug>_node import <Name>Node
from apps.api.app.node_system.nodes.<slug>.<slug>_trigger import <Name>TriggerNode  # if poll
from apps.api.app.node_system.nodes.<slug>.<slug>_webhook import <Name>WebhookTriggerNode  # if webhook

node_registry.register(<Name>Node)
node_registry.register(<Name>TriggerNode)
node_registry.register(<Name>WebhookTriggerNode)
```

---

## Validate

After the files are written, every new integration goes through this
mandatory gauntlet — do not skip any step:

```bash
# 1. Lint + format.
env -u VIRTUAL_ENV uv run ruff check --fix apps/api/app/node_system/nodes/<slug>/

# 2. Smoke import — confirms the manifest builds + registry picks it up.
env -u VIRTUAL_ENV uv run python -c "
from apps.api.app.node_system.registry.registry import node_registry
for t in ['action.<slug>', 'trigger.<slug>', 'trigger.<slug>_webhook']:
    if t in node_registry._nodes:
        m = node_registry._nodes[t].get_metadata()
        print(f'{t}: ok ({len(m.properties)} props)')
"

# 3. Refresh metadata snapshot — confirms new node lands in the locked set.
env -u VIRTUAL_ENV RMC_UPDATE_NODE_SNAPSHOTS=1 uv run pytest apps/api/tests/test_node_metadata_snapshot.py -q

# 4. Full backend test suite — catches anything the snapshot missed.
env -u VIRTUAL_ENV uv run pytest apps/api/tests/ -x -q

# 5. Frontend typecheck (free — webhook URL won't render right if metadata is wrong).
pnpm --filter runmycrew-web exec tsc --noEmit
```

If any step fails: fix the manifest, re-run. Never push a red gauntlet.

---

## Checklist before finishing

- [ ] Slug consistent across manifest type, file paths, provider id, and credential type
- [ ] `icon_slug` + `color` set (frontend uses these to render the brand tile)
- [ ] At least one entry in `operations` (action) or `events` (trigger)
- [ ] `visible_fields` (action) / `extra_fields` (poll) drive per-op visibility — don't hand-write `condition` blocks
- [ ] `output_flatten` (action) / `flatten` (poll) registered via `register_flatten(...)` for any op/event whose response shape needs trimming
- [ ] API key auth → credential provider entry added; OAuth auth → provider class + env vars
- [ ] Polling triggers → `eager_register_polling_providers()` updated
- [ ] Registry imports + `node_registry.register(...)` calls added
- [ ] Snapshot fixture refreshed (`RMC_UPDATE_NODE_SNAPSHOTS=1`)
- [ ] Full backend test suite green; `tsc --noEmit` green

## When the manifest doesn't fit

The three scaffolds cover ~85% of providers. The remaining 15% — GraphQL,
multi-call ops, signed AWS requests, Slack's URL-verification handshake —
fit through escape hatches:

- **Action**: `OpSpec.handler` replaces declarative `method`/`path`. Receives the live node + httpx client + auth headers, returns a `NodeResult`. Example: `apps/api/app/node_system/nodes/linear/manifest.py`.
- **Polling**: `PollingEvent.diff_handler` replaces builtin cursor strategies. Example: `apps/api/app/node_system/nodes/gpeople/trigger_manifest.py` (etag-map cursor).
- **Polling pagination**: `PollingTriggerManifest.paginate_fn` replaces the default single-page fetcher. Example: same gpeople file.
- **Webhook signature**: drop down to one of the five named schemes (`hmac_sha256`, `hmac_sha1`, `stripe`, `shopify`, `gitlab_token`, `none`), or extend the scheme literal in `webhook_manifest.py` and register a new verifier in `features/webhooks/signature_schemes.py`.

When you reach for an escape hatch, leave a comment explaining *why
the declarative form can't express it* — future contributors should
default to declarative and only break glass with cause.
