"""Google BigQuery action node — Google BigQuery — datasets, tables, and SQL queries.

REST at https://bigquery.googleapis.com/bigquery/v2. See sim-parity roadmap Phase 4.26.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.google_bigquery",
    name="Google BigQuery",
    category="integration",
    description="Google BigQuery — datasets, tables, and SQL queries.",
    icon_slug="google_bigquery",
    color="#ffffff",
    base_url="https://bigquery.googleapis.com/bigquery/v2",
    credential_type="google_oauth",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="customer_id", label="Customer ID", type="string"),
        FieldSpec(name="query", label="Query / GAQL / SQL", type="string"),
        FieldSpec(name="operations", label="Operations (JSON array)", type="json", default=[]),
        FieldSpec(name="project_id", label="Project ID", type="string"),
        FieldSpec(
            name="dataset_id",
            label="Dataset",
            type="string",
            remote=RemoteLookup(
                provider="bigquery",
                resource="datasets",
                params={"project_id": "${project_id}"},
                depends_on=["project_id"],
            ),
        ),
        FieldSpec(
            name="table_id",
            label="Table",
            type="string",
            remote=RemoteLookup(
                provider="bigquery",
                resource="tables",
                params={"project_id": "${project_id}", "dataset_id": "${dataset_id}"},
                depends_on=["project_id", "dataset_id"],
            ),
        ),
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
            id="run_query",
            label="Run Query",
            method="POST",
            path="/projects/{project_id}/queries",
            visible_fields=["project_id", "query", "use_legacy_sql"],
            body_builder=lambda v: {
                "query": getattr(v, "query", "") or "",
                "useLegacySql": bool(getattr(v, "use_legacy_sql", False)),
            },
        ),
        OpSpec(
            id="list_datasets",
            label="List Datasets",
            method="GET",
            path="/projects/{project_id}/datasets",
            visible_fields=["project_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_tables",
            label="List Tables",
            method="GET",
            path="/projects/{project_id}/datasets/{dataset_id}/tables",
            visible_fields=["project_id", "dataset_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_table",
            label="Get Table Metadata",
            method="GET",
            path="/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}",
            visible_fields=["project_id", "dataset_id", "table_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="insert_all",
            label="Streaming Insert Rows",
            method="POST",
            path="/projects/{project_id}/datasets/{dataset_id}/tables/{table_id}/insertAll",
            visible_fields=["project_id", "dataset_id", "table_id", "rows"],
            body_builder=lambda v: {"rows": [{"json": r} for r in (getattr(v, "rows", []) or [])]},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
