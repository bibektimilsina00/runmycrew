"""Google Maps action node — Google Maps — geocoding, places, distance matrix.

REST at https://maps.googleapis.com/maps/api. See sim-parity roadmap Phase 4.26.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_maps",
    name="Google Maps",
    category="integration",
    description="Google Maps — geocoding, places, distance matrix.",
    icon_slug="google_maps",
    color="#1c1c1c",
    base_url="https://maps.googleapis.com/maps/api",
    credential_type="google_maps_api_key",
    token_field=["api_key"],
    auth="query_token",
    auth_query_param="key",
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
            id="geocode",
            label="Geocode Address",
            method="GET",
            path="/geocode/json",
            visible_fields=["address"],
            query_builder=lambda v: {"address": getattr(v, "address", "") or ""},
        ),
        OpSpec(
            id="reverse_geocode",
            label="Reverse Geocode",
            method="GET",
            path="/geocode/json",
            visible_fields=["latlng"],
            query_builder=lambda v: {"latlng": getattr(v, "latlng", "") or ""},
        ),
        OpSpec(
            id="place_search",
            label="Place Text Search",
            method="GET",
            path="/place/textsearch/json",
            visible_fields=["query"],
            query_builder=lambda v: {"query": getattr(v, "query", "") or ""},
        ),
        OpSpec(
            id="place_details",
            label="Place Details",
            method="GET",
            path="/place/details/json",
            visible_fields=["place_id"],
            query_builder=lambda v: {"place_id": getattr(v, "place_id", "") or ""},
        ),
        OpSpec(
            id="distance_matrix",
            label="Distance Matrix",
            method="GET",
            path="/distancematrix/json",
            visible_fields=["origins", "destinations", "mode"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "origins": getattr(v, "origins", None) or None,
                    "destinations": getattr(v, "destinations", None) or None,
                    "mode": getattr(v, "mode", None) or None,
                }.items()
                if val
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
