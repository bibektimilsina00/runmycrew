"""API-key credential registry — auto-discovered from node folders.

Each provider ships its own `credential.py` inside its `nodes/<slug>/`
folder. This module scans the tree once on import and stitches every
per-provider `PROVIDER` into `PROVIDERS`, keyed by the folder name.

Drop a `credential.py` into a new node folder — the provider registers
on next backend reload. No monolith to edit.
"""

from __future__ import annotations

import importlib
import pkgutil

from pydantic import BaseModel


class CredentialField(BaseModel):
    id: str
    label: str
    type: str
    placeholder: str = ""


_BRAND_FOLDERS = {"ai", "aws", "google", "microsoft", "atlassian", "twilio", "sap", "meta"}


class APIKeyProvider:
    def __init__(
        self,
        id: str,
        name: str,
        description: str,
        hint: str,
        fields: list[CredentialField],
        # Brand identity — frontend renders the theSVG mark by slug and
        # uses `color` for the tile background.
        icon_slug: str | None = None,
        color: str | None = None,
        ai_provider_id: str | None = None,
        default_model: str | None = None,
        supports_tools: bool = False,
        supports_response_format: bool = False,
        ai_api_type: str | None = None,
        chat_completions_url: str | None = None,
        models_url: str | None = None,
    ):
        self.id = id
        self.name = name
        self.type = "api_key"
        self.description = description
        self.icon_slug = icon_slug
        self.color = color
        self.hint = hint
        self.fields = fields
        self.ai_provider_id = ai_provider_id
        self.default_model = default_model
        self.supports_tools = supports_tools
        self.supports_response_format = supports_response_format
        self.ai_api_type = ai_api_type
        self.chat_completions_url = chat_completions_url
        self.models_url = models_url
        # Set by `_discover_providers` after import from the module path.
        # `None` = flat provider (no brand grouping in the picker).
        self.brand: str | None = None


def _discover_providers() -> dict[str, APIKeyProvider]:
    """Walk `apps.api.app.node_system.nodes.*` for a `credential` module
    exporting `PROVIDER`. Key by the folder name (matches legacy dict
    layout). A broken module logs a warning and is skipped so one bad
    file doesn't take the whole registry down."""
    from apps.api.app.core.logger import get_logger

    log = get_logger(__name__)
    root = importlib.import_module("apps.api.app.node_system.nodes")
    out: dict[str, APIKeyProvider] = {}

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
            if not m.name.endswith(".credential"):
                continue
            try:
                mod = importlib.import_module(m.name)
            except Exception as e:  # noqa: BLE001
                log.warning("skipping credential %s: %s", m.name, e)
                continue
            provider = getattr(mod, "PROVIDER", None)
            if not isinstance(provider, APIKeyProvider):
                continue
            # Module path is `apps.api.app.node_system.nodes.<...>.credential`.
            # Token right after `nodes.` marks a brand group when it's
            # one of the known brand folders (google/aws/…); otherwise
            # the provider stays ungrouped.
            parts = m.name.split(".")
            try:
                i = parts.index("nodes")
                brand_token = parts[i + 1] if i + 1 < len(parts) else None
            except ValueError:
                brand_token = None
            if brand_token in _BRAND_FOLDERS:
                provider.brand = brand_token
            slug = parts[-2]
            out[slug] = provider

    _walk(root)
    return out


PROVIDERS: dict[str, APIKeyProvider] = _discover_providers()


def get_ai_providers() -> list[APIKeyProvider]:
    return [provider for provider in PROVIDERS.values() if provider.ai_provider_id]


def get_ai_provider(provider_id: str) -> APIKeyProvider | None:
    return next(
        (provider for provider in get_ai_providers() if provider.ai_provider_id == provider_id),
        None,
    )


def get_ai_provider_ids() -> set[str]:
    return {provider.ai_provider_id for provider in get_ai_providers() if provider.ai_provider_id}
