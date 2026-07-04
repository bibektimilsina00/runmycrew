"""Clay action node — data enrichment via workspace tables.

Clay's public API is limited — the primary integration surface is
pushing rows into a Clay table via a workspace webhook. This action
node exposes that "add row" op. All heavy enrichment happens inside
Clay's own workflows on receipt.

REST at the Clay webhook URL configured per-user (stored on the
credential as `webhook_url`). No shared base URL — action reads the
URL from cred.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.clay",
    name="Clay",
    category="integration",
    description="Clay — push rows into a Clay workspace table for enrichment.",
    icon_slug="clay",
    color="#1c1c1c",
    base_url="",
    credential_type="clay_api_key",
    token_field=["api_key"],
    auth="none",
    fields=[
        FieldSpec(name="data", label="Row data (JSON)", type="json", required=True),
    ],
    operations=[
        OpSpec(
            id="push_row",
            label="Push Row to Clay Table",
            method="POST",
            path="{webhook_url}",
            visible_fields=["data"],
            body_builder=lambda v: getattr(v, "data", {}) or {},
        ),
    ],
    outputs_schema=[
        {"label": "success", "type": "boolean"},
        {"label": "row_id", "type": "string"},
    ],
    allow_error=True,
)
