"""Supabase action node — manifest form.

Supabase routes everything through PostgREST under
`<project_url>/rest/v1/`. The URL is *per-project*, so the manifest
declares an empty `base_url` and resolves the full path via the
credential — same trick GitLab-style `gitlab_token` scheme uses on the
webhook side.

Two header oddities:
  - `Authorization: Bearer <key>` carries the auth contract.
  - `apikey: <key>` is duplicated because PostgREST checks both
    independently. Without the duplicate, Supabase 401s.

Both headers carry the same key (anon or service-role). The manifest
fills the `apikey` header via `{token}` substitution in `extra_headers`
— added to the scaffold for exactly this kind of dual-header provider.

Three ops cover 80% of workflow use: insert / select / patch rows on
a named table. The PostgREST `filter` field accepts the full PostgREST
operator syntax (`?id=eq.5`, `?name=ilike.*alice*`).
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)


def _parse_postgrest_filter(raw: Any) -> dict[str, str]:
    """Split `id=eq.5&name=ilike.alice` into a `{key: value}` dict so
    PostgREST's filter syntax rides on the URL's query string the way
    httpx expects.
    """
    if not raw:
        return {}
    out: dict[str, str] = {}
    for chunk in str(raw).split("&"):
        chunk = chunk.strip()
        if not chunk or "=" not in chunk:
            continue
        key, value = chunk.split("=", 1)
        out[key.strip()] = value.strip()
    return out


MANIFEST = ProviderManifest(
    type="action.supabase",
    name="Supabase",
    category="integration",
    description="Read and write Supabase tables through PostgREST.",
    icon_slug="supabase",
    color="#1c1c1c",
    base_url="",
    credential_type="supabase_api_key",
    token_field=["api_key"],
    auth="bearer",
    # `apikey` header is the Supabase oddity — same value as Authorization
    # but PostgREST requires both. {token} resolves to the credential key.
    extra_headers={"apikey": "{token}"},
    fields=[
        FieldSpec(name="table", label="Table", type="string", required=True, placeholder="users"),
        FieldSpec(name="row", label="Row (JSON object)", type="json"),
        FieldSpec(name="rows", label="Rows (JSON array for batch insert)", type="json"),
        FieldSpec(
            name="filter",
            label="Filter",
            type="string",
            placeholder="id=eq.5 or name=ilike.*alice*",
            mode="advanced",
            description="PostgREST filter syntax. Multiple filters AND-join via &.",
        ),
        FieldSpec(
            name="select",
            label="Select (CSV columns)",
            type="string",
            default="*",
            mode="advanced",
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
        FieldSpec(name="order", label="Order", type="string", mode="advanced"),
        FieldSpec(name="sb_table", label="Table Name", type="string"),
        FieldSpec(name="row_id", label="Row ID", type="string"),
        FieldSpec(name="row_body", label="Row Body (JSON)", type="json", default={}),
        FieldSpec(name="select", label="Select Fields", type="string", default="*"),
        FieldSpec(name="sb_filter", label="Filter (PostgREST syntax)", type="string"),
        FieldSpec(name="search_column", label="Search Column", type="string"),
        FieldSpec(name="search_query", label="Search Query", type="string"),
        FieldSpec(name="function_name", label="Function Name", type="string"),
        FieldSpec(name="rpc_args", label="RPC Args (JSON)", type="json", default={}),
        FieldSpec(name="invoke_body", label="Invoke Body (JSON)", type="json", default={}),
        FieldSpec(name="bucket_name", label="Bucket Name", type="string"),
        FieldSpec(name="storage_path", label="Storage Path", type="string"),
        FieldSpec(name="storage_prefix", label="Storage Prefix", type="string"),
        FieldSpec(name="storage_destination", label="Storage Destination Key", type="string"),
        FieldSpec(name="file_content", label="File Content (base64/bytes)", type="string"),
        FieldSpec(
            name="expires_in", label="Signed URL Expiry (seconds)", type="number", default=3600
        ),
        FieldSpec(name="bucket_public", label="Public Bucket", type="boolean", default=False),
    ],
    operations=[
        OpSpec(
            id="select_rows",
            label="Select Rows",
            method="GET",
            path="{project_url}/rest/v1/{table}",
            visible_fields=["table", "filter", "select", "limit", "order"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "select": getattr(v, "select", None),
                    "limit": int(getattr(v, "limit", None) or 100),
                    "order": getattr(v, "order", None),
                    **_parse_postgrest_filter(getattr(v, "filter", None)),
                }.items()
                if val not in (None, "")
            },
        ),
        OpSpec(
            id="insert_row",
            label="Insert Row",
            method="POST",
            path="{project_url}/rest/v1/{table}",
            visible_fields=["table", "row"],
            body_builder=lambda v: getattr(v, "row", None) or {},
        ),
        OpSpec(
            id="insert_rows",
            label="Insert Rows (batch)",
            method="POST",
            path="{project_url}/rest/v1/{table}",
            visible_fields=["table", "rows"],
            body_builder=lambda v: getattr(v, "rows", None) or [],
        ),
        OpSpec(
            id="update_rows",
            label="Update Rows",
            method="PATCH",
            path="{project_url}/rest/v1/{table}",
            visible_fields=["table", "filter", "row"],
            query_builder=lambda v: _parse_postgrest_filter(getattr(v, "filter", None)),
            body_builder=lambda v: getattr(v, "row", None) or {},
        ),
        OpSpec(
            id="delete_rows",
            label="Delete Rows",
            method="DELETE",
            path="{project_url}/rest/v1/{table}",
            visible_fields=["table", "filter"],
            query_builder=lambda v: _parse_postgrest_filter(getattr(v, "filter", None)),
        ),
        OpSpec(
            id="query",
            label="Query Rows (Select)",
            method="GET",
            path="/rest/v1/{sb_table}",
            visible_fields=["sb_table", "select", "sb_filter"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "select": getattr(v, "select", None) or "*",
                    "filter": getattr(v, "sb_filter", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_row",
            label="Get Row by ID",
            method="GET",
            path="/rest/v1/{sb_table}",
            visible_fields=["sb_table", "row_id"],
            query_builder=lambda v: {"id": "eq." + (getattr(v, "row_id", "") or "")},
        ),
        OpSpec(
            id="insert",
            label="Insert Row(s)",
            method="POST",
            path="/rest/v1/{sb_table}",
            visible_fields=["sb_table", "row_body"],
            body_builder=lambda v: getattr(v, "row_body", None) or {},
        ),
        OpSpec(
            id="update",
            label="Update Rows",
            method="PATCH",
            path="/rest/v1/{sb_table}",
            visible_fields=["sb_table", "sb_filter", "row_body"],
            body_builder=lambda v: getattr(v, "row_body", None) or {},
        ),
        OpSpec(
            id="delete",
            label="Delete Rows",
            method="DELETE",
            path="/rest/v1/{sb_table}",
            visible_fields=["sb_table", "sb_filter"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="upsert",
            label="Upsert Row(s)",
            method="POST",
            path="/rest/v1/{sb_table}",
            visible_fields=["sb_table", "row_body"],
            body_builder=lambda v: getattr(v, "row_body", None) or {},
        ),
        OpSpec(
            id="count",
            label="Count Rows",
            method="GET",
            path="/rest/v1/{sb_table}",
            visible_fields=["sb_table"],
            query_builder=lambda v: {"select": "count"},
        ),
        OpSpec(
            id="text_search",
            label="Full-text Search",
            method="GET",
            path="/rest/v1/{sb_table}",
            visible_fields=["sb_table", "search_column", "search_query"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    (getattr(v, "search_column", None) or "") + ".fts": getattr(
                        v, "search_query", None
                    )
                    or None
                }.items()
                if val
            },
        ),
        OpSpec(
            id="rpc",
            label="Call RPC Function",
            method="POST",
            path="/rest/v1/rpc/{function_name}",
            visible_fields=["function_name", "rpc_args"],
            body_builder=lambda v: getattr(v, "rpc_args", None) or {},
        ),
        OpSpec(
            id="invoke_function",
            label="Invoke Edge Function",
            method="POST",
            path="/functions/v1/{function_name}",
            visible_fields=["function_name", "invoke_body"],
            body_builder=lambda v: getattr(v, "invoke_body", None) or {},
        ),
        OpSpec(
            id="introspect",
            label="Introspect Schema (via OpenAPI)",
            method="GET",
            path="/rest/v1/",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="storage_upload",
            label="Upload to Storage",
            method="POST",
            path="/storage/v1/object/{bucket_name}/{storage_path}",
            visible_fields=["bucket_name", "storage_path", "file_content"],
            body_builder=lambda v: getattr(v, "file_content", "") or "",
        ),
        OpSpec(
            id="storage_download",
            label="Download from Storage",
            method="GET",
            path="/storage/v1/object/{bucket_name}/{storage_path}",
            visible_fields=["bucket_name", "storage_path"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="storage_list",
            label="List Storage Objects",
            method="POST",
            path="/storage/v1/object/list/{bucket_name}",
            visible_fields=["bucket_name", "storage_prefix"],
            body_builder=lambda v: {
                "prefix": getattr(v, "storage_prefix", None) or "",
                "limit": 100,
            },
        ),
        OpSpec(
            id="storage_delete",
            label="Delete Storage Object",
            method="DELETE",
            path="/storage/v1/object/{bucket_name}/{storage_path}",
            visible_fields=["bucket_name", "storage_path"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="storage_move",
            label="Move Storage Object",
            method="POST",
            path="/storage/v1/object/move",
            visible_fields=["bucket_name", "storage_path", "storage_destination"],
            body_builder=lambda v: {
                "bucketId": getattr(v, "bucket_name", "") or "",
                "sourceKey": getattr(v, "storage_path", "") or "",
                "destinationKey": getattr(v, "storage_destination", "") or "",
            },
        ),
        OpSpec(
            id="storage_copy",
            label="Copy Storage Object",
            method="POST",
            path="/storage/v1/object/copy",
            visible_fields=["bucket_name", "storage_path", "storage_destination"],
            body_builder=lambda v: {
                "bucketId": getattr(v, "bucket_name", "") or "",
                "sourceKey": getattr(v, "storage_path", "") or "",
                "destinationKey": getattr(v, "storage_destination", "") or "",
            },
        ),
        OpSpec(
            id="storage_get_public_url",
            label="Get Public Storage URL",
            method="GET",
            path="/storage/v1/object/public/{bucket_name}/{storage_path}",
            visible_fields=["bucket_name", "storage_path"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="storage_create_signed_url",
            label="Create Signed URL",
            method="POST",
            path="/storage/v1/object/sign/{bucket_name}/{storage_path}",
            visible_fields=["bucket_name", "storage_path", "expires_in"],
            body_builder=lambda v: {"expiresIn": int(getattr(v, "expires_in", 3600) or 3600)},
        ),
        OpSpec(
            id="storage_create_bucket",
            label="Create Storage Bucket",
            method="POST",
            path="/storage/v1/bucket",
            visible_fields=["bucket_name", "bucket_public"],
            body_builder=lambda v: {
                "name": getattr(v, "bucket_name", "") or "",
                "public": bool(getattr(v, "bucket_public", False)),
            },
        ),
        OpSpec(
            id="storage_list_buckets",
            label="List Storage Buckets",
            method="GET",
            path="/storage/v1/bucket",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="storage_delete_bucket",
            label="Delete Storage Bucket",
            method="DELETE",
            path="/storage/v1/bucket/{bucket_name}",
            visible_fields=["bucket_name"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "items", "type": "array"},
        {"label": "count", "type": "number"},
    ],
    allow_error=True,
)
