"""Google Meet action node — Google Meet — meeting spaces + conference records.

REST at https://meet.googleapis.com/v2. See sim-parity roadmap Phase 4.26.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_meet",
    name="Google Meet",
    category="integration",
    description="Google Meet — meeting spaces + conference records.",
    icon_slug="google_meet",
    color="#1c1c1c",
    base_url="https://meet.googleapis.com/v2",
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
            id="create_space",
            label="Create Meeting Space",
            method="POST",
            path="/spaces",
            visible_fields=[],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="get_space",
            label="Get Meeting Space",
            method="GET",
            path="/spaces/{name}",
            visible_fields=["name"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="end_active_conference",
            label="End Active Conference",
            method="POST",
            path="/spaces/{name}:endActiveConference",
            visible_fields=["name"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_conference_records",
            label="List Conference Records",
            method="GET",
            path="/conferenceRecords",
            visible_fields=["filter"],
            query_builder=lambda v: {
                k: val for k, val in {"filter": getattr(v, "filter", None) or None}.items() if val
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
