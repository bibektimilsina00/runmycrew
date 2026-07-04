"""Google Vault action node — Google Vault — eDiscovery matters, holds, exports.

REST at https://vault.googleapis.com/v1. See sim-parity roadmap Phase 4.26.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_vault",
    name="Google Vault",
    category="integration",
    description="Google Vault — eDiscovery matters, holds, exports.",
    icon_slug="google_vault",
    color="#1c1c1c",
    base_url="https://vault.googleapis.com/v1",
    credential_type="google_oauth",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="customer_id", label="Customer ID", type="string"),
        FieldSpec(name="query", label="Query / GAQL / SQL", type="string"),
        FieldSpec(name="operations", label="Operations (JSON array)", type="json", default=[]),
        FieldSpec(name="project_id", label="Project ID", type="string"),
        FieldSpec(name="dataset_id", label="Dataset ID", type="string"),
        FieldSpec(name="table_id", label="Table ID", type="string"),
        FieldSpec(name="rows", label="Rows (JSON array)", type="json", default=[]),
        FieldSpec(
            name="use_legacy_sql",
            label="Use Legacy SQL",
            type="boolean",
            default=False,
            mode="advanced",
        ),
        FieldSpec(name="address", label="Address", type="string"),
        FieldSpec(name="latlng", label="Lat,Lng", type="string"),
        FieldSpec(name="place_id", label="Place ID", type="string"),
        FieldSpec(name="origins", label="Origins", type="string"),
        FieldSpec(name="destinations", label="Destinations", type="string"),
        FieldSpec(name="mode", label="Mode", type="string", default="driving"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="filter", label="Filter", type="string"),
        FieldSpec(name="text", label="Text", type="string"),
        FieldSpec(name="target", label="Target Language", type="string"),
        FieldSpec(name="source", label="Source Language", type="string"),
        FieldSpec(name="format", label="Format (text|html)", type="string", default="text"),
        FieldSpec(name="matter_id", label="Matter ID", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_matters",
            label="List Matters",
            method="GET",
            path="/matters",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_matter",
            label="Get Matter",
            method="GET",
            path="/matters/{matter_id}",
            visible_fields=["matter_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_matter",
            label="Create Matter",
            method="POST",
            path="/matters",
            visible_fields=["name", "description"],
            body_builder=lambda v: {
                "name": getattr(v, "name", "") or "",
                "description": getattr(v, "description", None) or None,
            },
        ),
        OpSpec(
            id="list_holds",
            label="List Holds on Matter",
            method="GET",
            path="/matters/{matter_id}/holds",
            visible_fields=["matter_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_exports",
            label="List Exports on Matter",
            method="GET",
            path="/matters/{matter_id}/exports",
            visible_fields=["matter_id"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
