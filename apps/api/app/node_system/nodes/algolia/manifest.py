"""Algolia action node — manifest form.

Algolia's search/indexing API runs on per-app subdomains
(`https://{app_id}-dsn.algolia.net` for search-only reads,
`https://{app_id}.algolia.net` for writes). Two custom headers:

  - `X-Algolia-Application-Id` — app id from credential
  - `X-Algolia-API-Key` — secret key from credential

Both ride via extra_headers with credential-field substitution.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.algolia",
    name="Algolia",
    category="integration",
    description="Algolia — index, search, and manage records.",
    icon_slug="algolia",
    color="#1c1c1c",
    base_url="",
    credential_type="algolia_api_key",
    token_field=["api_key"],
    # Both auth headers ride via extra_headers — there's no single auth
    # scheme that captures Algolia's two-header pattern.
    auth="none",
    extra_headers={
        "X-Algolia-Application-Id": "{app_id}",
        "X-Algolia-API-Key": "{api_key}",
    },
    fields=[
        FieldSpec(name="index_name", label="Index", type="string", required=True),
        FieldSpec(name="object_id", label="Object ID", type="string"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(name="record", label="Record (JSON)", type="json"),
        FieldSpec(name="records", label="Records (JSON array)", type="json"),
        FieldSpec(name="filters", label="Filters", type="string", mode="advanced"),
        FieldSpec(
            name="hits_per_page", label="Hits per page", type="number", default=20, mode="advanced"
        ),
        FieldSpec(name="page", label="Page", type="number", default=0, mode="advanced"),
        FieldSpec(name="object_ids", label="Object IDs (JSON array)", type="json"),
    ],
    operations=[
        OpSpec(
            id="search",
            label="Search",
            method="POST",
            path="https://{app_id}-dsn.algolia.net/1/indexes/{index_name}/query",
            visible_fields=["index_name", "query", "filters", "hits_per_page", "page"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "query": getattr(v, "query", None) or "",
                    "filters": getattr(v, "filters", None),
                    "hitsPerPage": int(getattr(v, "hits_per_page", 20) or 20),
                    "page": int(getattr(v, "page", 0) or 0),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_object",
            label="Get Object",
            method="GET",
            path="https://{app_id}-dsn.algolia.net/1/indexes/{index_name}/{object_id}",
            visible_fields=["index_name", "object_id"],
        ),
        OpSpec(
            id="add_object",
            label="Add Object",
            method="POST",
            path="https://{app_id}.algolia.net/1/indexes/{index_name}",
            visible_fields=["index_name", "record"],
            body_builder=lambda v: getattr(v, "record", None) or {},
        ),
        OpSpec(
            id="save_object",
            label="Save Object (Upsert)",
            method="PUT",
            path="https://{app_id}.algolia.net/1/indexes/{index_name}/{object_id}",
            visible_fields=["index_name", "object_id", "record"],
            body_builder=lambda v: getattr(v, "record", None) or {},
        ),
        OpSpec(
            id="delete_object",
            label="Delete Object",
            method="DELETE",
            path="https://{app_id}.algolia.net/1/indexes/{index_name}/{object_id}",
            visible_fields=["index_name", "object_id"],
            success_payload_template={"deleted": True, "objectID": "{object_id}"},
        ),
        OpSpec(
            id="batch",
            label="Batch Operations",
            method="POST",
            path="https://{app_id}.algolia.net/1/indexes/{index_name}/batch",
            visible_fields=["index_name", "records"],
            body_builder=lambda v: {"requests": getattr(v, "records", None) or []},
        ),
        OpSpec(
            id="clear_index",
            label="Clear Index",
            method="POST",
            path="https://{app_id}.algolia.net/1/indexes/{index_name}/clear",
            visible_fields=["index_name"],
            success_payload_template={"cleared": True, "index": "{index_name}"},
        ),
    ],
    outputs_schema=[
        {"label": "hits", "type": "array"},
        {"label": "nbHits", "type": "number"},
        {"label": "page", "type": "number"},
        {"label": "objectID", "type": "string"},
        {"label": "taskID", "type": "number"},
    ],
    allow_error=True,
)
