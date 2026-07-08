"""Google Translate action node — Google Translate — translate text between languages.

REST at https://translation.googleapis.com/language/translate/v2. See sim-parity roadmap Phase 4.26.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_translate",
    name="Google Translate",
    category="integration",
    description="Google Translate — translate text between languages.",
    icon_slug="google_translate",
    color="#ffffff",
    base_url="https://translation.googleapis.com/language/translate/v2",
    credential_type="google_translate_api_key",
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
            id="translate",
            label="Translate",
            method="POST",
            path="",
            visible_fields=["text", "target", "source", "format"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "q": getattr(v, "text", "") or "",
                    "target": getattr(v, "target", "") or "",
                    "source": getattr(v, "source", None) or None,
                    "format": getattr(v, "format", None) or None,
                }.items()
                if val is not None and val != ""
            },
        ),
        OpSpec(
            id="detect",
            label="Detect Language",
            method="POST",
            path="/detect",
            visible_fields=["text"],
            body_builder=lambda v: {"q": getattr(v, "text", "") or ""},
        ),
        OpSpec(
            id="list_languages",
            label="List Supported Languages",
            method="GET",
            path="/languages",
            visible_fields=["target"],
            query_builder=lambda v: {
                k: val for k, val in {"target": getattr(v, "target", None) or None}.items() if val
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
