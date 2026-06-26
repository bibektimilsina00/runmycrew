"""Scaffolds that turn a per-provider manifest into a registered node.

Phase 0 of the sim-parity roadmap (`docs/sim-parity-roadmap.md`). Adding
a new REST integration is now a manifest file, not a 200-line class.

Quick start

    from apps.api.app.node_system.scaffolds import (
        build_rest_node, FieldSpec, OpSpec, ProviderManifest,
        register_flatten,
    )

    MANIFEST = ProviderManifest(
        type="action.firecrawl",
        name="Firecrawl",
        description="Scrape sites + crawl into clean markdown.",
        icon_slug="firecrawl",
        color="#1c1c1c",
        base_url="https://api.firecrawl.dev/v1",
        credential_type="firecrawl_api_key",
        fields=[
            FieldSpec(name="url", label="URL", type="string", required=True),
        ],
        operations=[
            OpSpec(
                id="scrape",
                label="Scrape",
                method="POST",
                path="/scrape",
                body_fields=["url"],
                visible_fields=["url"],
            ),
        ],
    )

    NODE = build_rest_node(MANIFEST)

Then register `NODE` in `node_system/registry/registry.py` as usual.
"""

from apps.api.app.node_system.scaffolds.polling_cursor import (
    diff_known_ids,
    diff_last_sha,
    diff_since_timestamp,
)
from apps.api.app.node_system.scaffolds.polling_manifest import (
    CursorStrategy,
    CustomDiff,
    PollingEvent,
    PollingTriggerManifest,
)
from apps.api.app.node_system.scaffolds.polling_node_factory import build_polling_trigger
from apps.api.app.node_system.scaffolds.rest_dispatch import (
    RESTError,
    build_auth,
    error_from_response,
    get_flatten,
    register_flatten,
    rest_request,
)
from apps.api.app.node_system.scaffolds.rest_manifest import (
    AuthScheme,
    CustomHandler,
    FieldSpec,
    OpSpec,
    ProviderManifest,
)
from apps.api.app.node_system.scaffolds.rest_node_factory import build_rest_node

__all__ = [
    "AuthScheme",
    "CursorStrategy",
    "CustomDiff",
    "CustomHandler",
    "FieldSpec",
    "OpSpec",
    "PollingEvent",
    "PollingTriggerManifest",
    "ProviderManifest",
    "RESTError",
    "build_auth",
    "build_polling_trigger",
    "build_rest_node",
    "diff_known_ids",
    "diff_last_sha",
    "diff_since_timestamp",
    "error_from_response",
    "get_flatten",
    "register_flatten",
    "rest_request",
]
