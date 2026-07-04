"""Tinybird action node — manifest form.

Tinybird is a managed ClickHouse-backed analytics store. Single
base URL (regional variants: `api.tinybird.co`, `api.eu.tinybird.co`),
Bearer auth.

Ops cover the workflow basics: query (via a published pipe), append
to a data source, list pipes / data sources.

The `region` field lets users point at `api.eu.tinybird.co` without
needing a custom credential per region — falls back to the default
US host if blank.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.tinybird",
    name="Tinybird",
    category="integration",
    description="Tinybird — analytics queries + data source ingestion.",
    icon_slug="tinybird",
    color="#1c1c1c",
    base_url="https://api.tinybird.co",
    credential_type="tinybird_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="pipe_name", label="Pipe Name", type="string"),
        FieldSpec(name="datasource_name", label="Data Source Name", type="string"),
        FieldSpec(name="sql", label="SQL", type="string", mode="advanced"),
        FieldSpec(
            name="rows",
            label="Rows (newline-delimited JSON)",
            type="string",
            mode="advanced",
            description='One JSON object per line, e.g. {"id":1}\\n{"id":2}',
        ),
        FieldSpec(
            name="mode",
            label="Append mode",
            type="options",
            default="append",
            mode="advanced",
            options=[
                {"label": "append", "value": "append"},
                {"label": "replace", "value": "replace"},
            ],
        ),
        FieldSpec(name="format", label="Format", type="string", default="JSON", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="query_pipe",
            label="Query Pipe (JSON)",
            method="GET",
            path="/v0/pipes/{pipe_name}.json",
            visible_fields=["pipe_name"],
        ),
        OpSpec(
            id="query_sql",
            label="Run SQL",
            method="GET",
            path="/v0/sql",
            visible_fields=["sql", "format"],
            query_fields=["sql", "format"],
        ),
        OpSpec(
            id="append_rows",
            label="Append Rows",
            method="POST",
            path="/v0/events",
            visible_fields=["datasource_name", "rows"],
            query_builder=lambda v: {
                "name": getattr(v, "datasource_name", None),
            },
            body_builder=lambda v: getattr(v, "rows", None) or "",
        ),
        OpSpec(
            id="list_pipes",
            label="List Pipes",
            method="GET",
            path="/v0/pipes",
        ),
        OpSpec(
            id="list_datasources",
            label="List Data Sources",
            method="GET",
            path="/v0/datasources",
        ),
        OpSpec(
            id="get_pipe",
            label="Get Pipe",
            method="GET",
            path="/v0/pipes/{pipe_name}",
            visible_fields=["pipe_name"],
        ),
        OpSpec(
            id="get_datasource",
            label="Get Data Source",
            method="GET",
            path="/v0/datasources/{datasource_name}",
            visible_fields=["datasource_name"],
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "array"},
        {"label": "meta", "type": "array"},
        {"label": "rows", "type": "number"},
        {"label": "statistics", "type": "object"},
        {"label": "pipes", "type": "array"},
        {"label": "datasources", "type": "array"},
    ],
    allow_error=True,
)
