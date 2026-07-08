"""Airtable provider manifest — wired through the REST-tool scaffold.

Mirrors the original `airtable_node.py` op set (six ops covering records
on a base+table). Custom builders cover the two quirks the declarative
form can't express:

- `list_records` / `search_records` rename `max_records` →
  `maxRecords` and `filter_formula` → `filterByFormula` for Airtable's
  query string. Plain `query_fields` would pass the prop names verbatim.
- `create_record` / `update_record` wrap the user-supplied `fields` dict
  in a top-level `{"fields": …}` envelope — Airtable's body shape.

Output flatteners normalize list/search responses into
`{records, count}` so downstream nodes don't have to know the API shape.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    register_flatten,
)

# ── output flatteners ────────────────────────────────────────────────


def _flatten_records(body: Any) -> dict[str, Any]:
    """`{"records": […]}` → `{records, count}`."""
    records = (body or {}).get("records", []) if isinstance(body, dict) else []
    return {"records": records, "count": len(records)}


def _flatten_create(body: Any) -> dict[str, Any]:
    """`{id, fields, …}` → `{id, record}` so it lines up with the node's
    advertised `outputs_schema`."""
    if not isinstance(body, dict):
        return {}
    return {"id": body.get("id"), "record": body}


register_flatten("airtable.records", _flatten_records)
register_flatten("airtable.create", _flatten_create)

# ── query / body builders ────────────────────────────────────────────


def _list_params(props: Any) -> dict[str, Any]:
    """Map list-records props onto Airtable's query keys."""
    params: dict[str, Any] = {}
    max_records = getattr(props, "max_records", None)
    if max_records is not None:
        params["maxRecords"] = min(int(max_records), 100)
    formula = getattr(props, "filter_formula", None)
    if formula:
        params["filterByFormula"] = formula
    view = getattr(props, "view", None)
    if view:
        params["view"] = view
    return params


def _fields_body(props: Any) -> dict[str, Any]:
    """Wrap the user-supplied `fields` dict in Airtable's envelope."""
    fields = getattr(props, "fields", None) or {}
    return {"fields": fields}


# ── manifest ─────────────────────────────────────────────────────────

MANIFEST = ProviderManifest(
    type="action.airtable",
    name="Airtable",
    category="integration",
    description="Read and write Airtable bases, tables, and records.",
    icon_slug="airtable",
    color="#ffffff",
    base_url="https://api.airtable.com/v0",
    credential_type="airtable_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="base_id",
            label="Base ID",
            type="string",
            required=True,
            placeholder="appXXXXXXXX",
        ),
        FieldSpec(
            name="table_name",
            label="Table Name",
            type="string",
            required=True,
            placeholder="Contacts",
        ),
        FieldSpec(
            name="record_id",
            label="Record ID",
            type="string",
        ),
        FieldSpec(
            name="fields",
            label="Fields (JSON)",
            type="json",
            placeholder='{"Name": "John", "Email": "john@example.com"}',
        ),
        FieldSpec(
            name="filter_formula",
            label="Filter Formula",
            type="string",
            mode="advanced",
            placeholder="{Status} = 'Active'",
        ),
        FieldSpec(
            name="view",
            label="View",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="max_records",
            label="Max Records",
            type="number",
            default=100,
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="list_records",
            label="List Records",
            method="GET",
            path="/{base_id}/{table_name}",
            visible_fields=["base_id", "table_name", "filter_formula", "view", "max_records"],
            query_builder=_list_params,
            output_flatten="airtable.records",
        ),
        OpSpec(
            id="get_record",
            label="Get Record",
            method="GET",
            path="/{base_id}/{table_name}/{record_id}",
            visible_fields=["base_id", "table_name", "record_id"],
        ),
        OpSpec(
            id="create_record",
            label="Create Record",
            method="POST",
            path="/{base_id}/{table_name}",
            visible_fields=["base_id", "table_name", "fields"],
            body_builder=_fields_body,
            output_flatten="airtable.create",
        ),
        OpSpec(
            id="update_record",
            label="Update Record",
            method="PATCH",
            path="/{base_id}/{table_name}/{record_id}",
            visible_fields=["base_id", "table_name", "record_id", "fields"],
            body_builder=_fields_body,
        ),
        OpSpec(
            id="delete_record",
            label="Delete Record",
            method="DELETE",
            path="/{base_id}/{table_name}/{record_id}",
            visible_fields=["base_id", "table_name", "record_id"],
            success_payload_template={"deleted": True, "id": "{record_id}"},
        ),
        OpSpec(
            id="search_records",
            label="Search Records (formula)",
            method="GET",
            path="/{base_id}/{table_name}",
            visible_fields=["base_id", "table_name", "filter_formula", "view", "max_records"],
            query_builder=_list_params,
            output_flatten="airtable.records",
        ),
    ],
    outputs_schema=[
        {"label": "records", "type": "array"},
        {"label": "record", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "count", "type": "number"},
    ],
    allow_error=True,
)
