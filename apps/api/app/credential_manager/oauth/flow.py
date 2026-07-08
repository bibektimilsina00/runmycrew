"""OAuth provider registry — auto-discovered from node folders.

Each provider ships its own `oauth.py` inside `nodes/<...>/` (brand-
level for shared flows like Google, per-node for one-offs like Slack).
This module scans the tree once on import and stitches every per-
provider `PROVIDER` into `PROVIDERS`, keyed by the folder-derived
service name.

Drop an `oauth.py` into a node folder — provider registers on next
backend reload. No monolith to edit.
"""

from __future__ import annotations

import importlib
import pkgutil
from typing import Any

# Re-export the shared base so old callers that did
# `from apps...oauth.flow import _SimpleOAuthProvider, REDIRECT_URI, ...`
# keep working without a codebase-wide rewrite.
from apps.api.app.credential_manager.oauth.base import (  # noqa: F401
    REDIRECT_URI,
    _SimpleOAuthProvider,
    logger,
    with_expiry_metadata,
)
from apps.api.app.node_system.base.base_node import BaseNode  # noqa: F401 (parity)


def _discover_providers() -> dict[str, Any]:
    """Walk `apps.api.app.node_system.nodes.*` for `oauth` modules
    exporting `PROVIDER`. Key by the provider's `id` with the trailing
    `_oauth` stripped — matches the legacy dict layout so callers that
    do `PROVIDERS["google"]` keep working. A broken module logs a
    warning and is skipped so one bad file can't take the registry
    down."""
    root = importlib.import_module("apps.api.app.node_system.nodes")
    out: dict[str, Any] = {}

    def _walk(pkg) -> None:
        for m in pkgutil.iter_modules(pkg.__path__, prefix=pkg.__name__ + "."):
            if m.ispkg:
                try:
                    sub = importlib.import_module(m.name)
                except Exception as e:  # noqa: BLE001
                    logger.warning("skipping subpackage %s: %s", m.name, e)
                    continue
                _walk(sub)
                continue
            if not m.name.endswith(".oauth"):
                continue
            try:
                mod = importlib.import_module(m.name)
            except Exception as e:  # noqa: BLE001
                logger.warning("skipping oauth %s: %s", m.name, e)
                continue
            provider = getattr(mod, "PROVIDER", None)
            if provider is None:
                continue
            pid = getattr(provider, "id", "") or ""
            key = pid.removesuffix("_oauth") if pid else m.name.split(".")[-2]
            out[key] = provider

    _walk(root)
    return out


PROVIDERS: dict[str, Any] = _discover_providers()


def get_oauth_provider(service_name: str):
    return PROVIDERS.get(service_name)
