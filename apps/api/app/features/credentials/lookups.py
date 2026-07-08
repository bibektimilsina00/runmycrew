"""Remote-picker lookup registry — one endpoint, many providers.

Every "give me the Owner / Repo / Channel / Database / … for this
credential" dropdown in the inspector routes through a single backend
endpoint (`/credentials/{id}/lookup/{provider}/{resource}`). The
endpoint is provider-agnostic: it decrypts the credential once (auto-
refreshing the OAuth token via `CredentialService`) and hands the token
+ any query params to a per-provider handler registered here.

Handlers ship inside their node's folder — e.g. GitHub's owners/repos
live at `apps.api.app.node_system.nodes.github.lookups`. We walk the
node tree once at import time (same pattern as
`credential_manager/api_keys.py`) and stitch every module's `LOOKUPS`
dict into the registry.

Adding a picker in a future PR = 1 handler function + `LOOKUPS[...] =
handler` + `remote=RemoteLookup(...)` on the manifest field. No monolith
to edit; nothing hand-registered in a global router.
"""

from __future__ import annotations

import importlib
import pkgutil
from collections.abc import Awaitable, Callable
from typing import Any

import httpx
from pydantic import BaseModel


class LookupItem(BaseModel):
    """One row in a remote-picker dropdown.

    `id` is what gets written to the workflow-graph field on select;
    `label` is what the dropdown shows. `sublabel` is optional
    secondary text (e.g. a repo's description, a channel's purpose)
    and `icon_slug` overrides the brand icon on a per-item basis
    (rare — most rows inherit the picker's provider icon).
    """

    id: str
    label: str
    sublabel: str | None = None
    icon_slug: str | None = None


class LookupResponse(BaseModel):
    """One page of lookup results.

    `cursor` + `has_more` support the frontend's infinite-scroll
    fetch. Providers that don't paginate leave both at their defaults.
    """

    items: list[LookupItem]
    cursor: str | None = None
    has_more: bool = False


# Handler signature. `cred` is the decrypted credential dict — token
# refresh has already run in `CredentialService.get_decrypted_credential`
# so handlers can trust `access_token` (or the api-key equivalent) to be
# live. `params` carries the query-param bag the frontend sent (after
# stripping the reserved `q` + `cursor` keys, which are passed
# separately for ergonomics).
LookupHandler = Callable[
    [httpx.AsyncClient, dict[str, Any], dict[str, str], str | None, str | None],
    Awaitable[LookupResponse],
]


def _discover_lookups() -> dict[str, dict[str, LookupHandler]]:
    """Walk `apps.api.app.node_system.nodes.*` for a `lookups` module
    exporting a `LOOKUPS` dict, and index by (provider, resource).

    Each module owns exactly one provider — it reports its provider key
    via `PROVIDER = "github"` (module-level string). The registry then
    keys handlers by that provider + the dict key inside `LOOKUPS`. A
    broken module logs a warning and is skipped so one bad file doesn't
    take the whole registry down.
    """
    from apps.api.app.core.logger import get_logger

    log = get_logger(__name__)
    root = importlib.import_module("apps.api.app.node_system.nodes")
    out: dict[str, dict[str, LookupHandler]] = {}

    def _walk(pkg) -> None:
        for m in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):
            if m.ispkg:
                try:
                    sub = importlib.import_module(m.name)
                except Exception as e:  # noqa: BLE001
                    log.warning("skipping subpackage %s: %s", m.name, e)
                    continue
                _walk(sub)
                continue
            if not m.name.endswith(".lookups"):
                continue
            try:
                mod = importlib.import_module(m.name)
            except Exception as e:  # noqa: BLE001
                log.warning("skipping lookups %s: %s", m.name, e)
                continue
            provider = getattr(mod, "PROVIDER", None)
            lookups = getattr(mod, "LOOKUPS", None)
            if not isinstance(provider, str) or not isinstance(lookups, dict):
                continue
            bucket = out.setdefault(provider, {})
            for resource, handler in lookups.items():
                if not callable(handler):
                    log.warning("skipping non-callable lookup %s:%s", provider, resource)
                    continue
                # Later-loaded modules overwrite earlier ones for the
                # same (provider, resource) — deterministic per walk
                # order.
                bucket[resource] = handler

    _walk(root)
    return out


LOOKUP_REGISTRY: dict[str, dict[str, LookupHandler]] = _discover_lookups()


def get_lookup_handler(provider: str, resource: str) -> LookupHandler | None:
    """Return the registered handler for a (provider, resource) pair,
    or `None` when the pair is unknown. Callers should surface a 404 —
    the frontend renderer treats a missing handler as a hard misconfig
    and shows an error tile.
    """
    return LOOKUP_REGISTRY.get(provider, {}).get(resource)
