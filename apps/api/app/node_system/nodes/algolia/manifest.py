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
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.algolia",
    name="Algolia",
    category="integration",
    description="Algolia — index, search, and manage records.",
    icon_slug="algolia",
    color="#ffffff",
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
        FieldSpec(
            name="index_name",
            label="Index",
            type="string",
            required=True,
            remote=RemoteLookup(provider="algolia", resource="indices"),
        ),
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
        FieldSpec(name="algolia_index", label="Index Name", type="string"),
        FieldSpec(name="algolia_query", label="Query", type="string"),
        FieldSpec(name="algolia_record", label="Record (JSON)", type="json", default={}),
        FieldSpec(name="algolia_object_id", label="Object ID", type="string"),
        FieldSpec(name="algolia_object_ids", label="Object IDs (JSON)", type="json", default=[]),
        FieldSpec(
            name="algolia_partial", label="Partial Update Body (JSON)", type="json", default={}
        ),
        FieldSpec(name="algolia_settings", label="Settings (JSON)", type="json", default={}),
        FieldSpec(name="algolia_batch", label="Batch Requests (JSON)", type="json", default=[]),
        FieldSpec(name="algolia_dest_index", label="Destination Index", type="string"),
        FieldSpec(
            name="algolia_operation", label="Operation (copy|move)", type="string", default="copy"
        ),
        FieldSpec(name="algolia_filter", label="Filter", type="string"),
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
        OpSpec(
            id="add_record",
            label="Add Record",
            method="POST",
            path="/1/indexes/{algolia_index}",
            visible_fields=["algolia_index", "algolia_record"],
            body_builder=lambda v: getattr(v, "algolia_record", None) or {},
        ),
        OpSpec(
            id="get_record",
            label="Get Record",
            method="GET",
            path="/1/indexes/{algolia_index}/{algolia_object_id}",
            visible_fields=["algolia_index", "algolia_object_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_records",
            label="Get Multiple Records",
            method="POST",
            path="/1/indexes/*/objects",
            visible_fields=["algolia_object_ids"],
            body_builder=lambda v: {"requests": getattr(v, "algolia_object_ids", []) or []},
        ),
        OpSpec(
            id="partial_update_record",
            label="Partial Update Record",
            method="POST",
            path="/1/indexes/{algolia_index}/{algolia_object_id}/partial",
            visible_fields=["algolia_index", "algolia_object_id", "algolia_partial"],
            body_builder=lambda v: getattr(v, "algolia_partial", None) or {},
        ),
        OpSpec(
            id="delete_record",
            label="Delete Record",
            method="DELETE",
            path="/1/indexes/{algolia_index}/{algolia_object_id}",
            visible_fields=["algolia_index", "algolia_object_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="browse_records",
            label="Browse Records",
            method="POST",
            path="/1/indexes/{algolia_index}/browse",
            visible_fields=["algolia_index"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="batch_operations",
            label="Batch Operations",
            method="POST",
            path="/1/indexes/{algolia_index}/batch",
            visible_fields=["algolia_index", "algolia_batch"],
            body_builder=lambda v: {"requests": getattr(v, "algolia_batch", []) or []},
        ),
        OpSpec(
            id="list_indices",
            label="List Indices",
            method="GET",
            path="/1/indexes",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_settings",
            label="Get Settings",
            method="GET",
            path="/1/indexes/{algolia_index}/settings",
            visible_fields=["algolia_index"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_settings",
            label="Update Settings",
            method="PUT",
            path="/1/indexes/{algolia_index}/settings",
            visible_fields=["algolia_index", "algolia_settings"],
            body_builder=lambda v: getattr(v, "algolia_settings", None) or {},
        ),
        OpSpec(
            id="delete_index",
            label="Delete Index",
            method="DELETE",
            path="/1/indexes/{algolia_index}",
            visible_fields=["algolia_index"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="copy_move_index",
            label="Copy or Move Index",
            method="POST",
            path="/1/indexes/{algolia_index}/operation",
            visible_fields=["algolia_index", "algolia_dest_index", "algolia_operation"],
            body_builder=lambda v: {
                "operation": getattr(v, "algolia_operation", None) or "copy",
                "destination": getattr(v, "algolia_dest_index", "") or "",
            },
        ),
        OpSpec(
            id="clear_records",
            label="Clear All Records",
            method="POST",
            path="/1/indexes/{algolia_index}/clear",
            visible_fields=["algolia_index"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="delete_by_filter",
            label="Delete by Filter",
            method="POST",
            path="/1/indexes/{algolia_index}/deleteByQuery",
            visible_fields=["algolia_index", "algolia_filter"],
            body_builder=lambda v: {"filters": getattr(v, "algolia_filter", "") or ""},
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
