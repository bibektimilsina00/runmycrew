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
    ],
    outputs_schema=[
        {"label": "items", "type": "array"},
        {"label": "count", "type": "number"},
    ],
    allow_error=True,
)
