"""Google Ads action node — Google Ads — campaigns, ad groups, keyword performance.

REST at https://googleads.googleapis.com/v17. See sim-parity roadmap Phase 4.26.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_ads",
    name="Google Ads",
    category="integration",
    description="Google Ads — campaigns, ad groups, keyword performance.",
    icon_slug="google_ads",
    color="#1c1c1c",
    base_url="https://googleads.googleapis.com/v17",
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
            id="list_customers",
            label="List Accessible Customers",
            method="GET",
            path="/customers:listAccessibleCustomers",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="search",
            label="Search (GAQL)",
            method="POST",
            path="/customers/{customer_id}/googleAds:search",
            visible_fields=["customer_id", "query"],
            body_builder=lambda v: {"query": getattr(v, "query", "") or ""},
        ),
        OpSpec(
            id="mutate_campaign",
            label="Mutate Campaign (raw ops)",
            method="POST",
            path="/customers/{customer_id}/campaigns:mutate",
            visible_fields=["customer_id", "operations"],
            body_builder=lambda v: {"operations": getattr(v, "operations", []) or []},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
