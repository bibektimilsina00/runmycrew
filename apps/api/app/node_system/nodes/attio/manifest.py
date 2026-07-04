"""Attio action node — manifest form.

Attio is a flexible-schema CRM exposing a Records-style API at
`https://api.attio.com/v2`. Bearer auth. Records belong to *objects*
(people, companies, deals, …), so every record op takes an
`object_slug` path segment.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.attio",
    name="Attio",
    category="integration",
    description="Attio CRM — manage records on any custom object schema.",
    icon_slug="attio",
    color="#1c1c1c",
    base_url="https://api.attio.com/v2",
    credential_type="attio_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="object_slug",
            label="Object",
            type="string",
            placeholder="people | companies | deals | custom_slug",
        ),
        FieldSpec(name="record_id", label="Record ID", type="string"),
        FieldSpec(name="data", label="Record values (JSON)", type="json"),
        FieldSpec(name="filter", label="Filter (JSON)", type="json", mode="advanced"),
        FieldSpec(name="sorts", label="Sorts (JSON)", type="json", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(name="offset", label="Offset", type="number", default=0, mode="advanced"),
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="entry_data", label="Entry values (JSON)", type="json"),
    ],
    operations=[
        OpSpec(
            id="create_record",
            label="Create Record",
            method="POST",
            path="/objects/{object_slug}/records",
            visible_fields=["object_slug", "data"],
            body_builder=lambda v: {"data": {"values": getattr(v, "data", None) or {}}},
        ),
        OpSpec(
            id="get_record",
            label="Get Record",
            method="GET",
            path="/objects/{object_slug}/records/{record_id}",
            visible_fields=["object_slug", "record_id"],
        ),
        OpSpec(
            id="update_record",
            label="Update Record",
            method="PATCH",
            path="/objects/{object_slug}/records/{record_id}",
            visible_fields=["object_slug", "record_id", "data"],
            body_builder=lambda v: {"data": {"values": getattr(v, "data", None) or {}}},
        ),
        OpSpec(
            id="delete_record",
            label="Delete Record",
            method="DELETE",
            path="/objects/{object_slug}/records/{record_id}",
            visible_fields=["object_slug", "record_id"],
            success_payload_template={"deleted": True, "id": "{record_id}"},
        ),
        OpSpec(
            id="list_records",
            label="Query Records",
            method="POST",
            path="/objects/{object_slug}/records/query",
            visible_fields=["object_slug", "filter", "sorts", "limit", "offset"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "filter": getattr(v, "filter", None),
                    "sorts": getattr(v, "sorts", None),
                    "limit": int(getattr(v, "limit", 25) or 25),
                    "offset": int(getattr(v, "offset", 0) or 0),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_objects",
            label="List Objects",
            method="GET",
            path="/objects",
        ),
        OpSpec(
            id="add_to_list",
            label="Add to List",
            method="POST",
            path="/lists/{list_id}/entries",
            visible_fields=["list_id", "entry_data"],
            body_builder=lambda v: {"data": {"entry_values": getattr(v, "entry_data", None) or {}}},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "object"},
        {"label": "items", "type": "array"},
    ],
    allow_error=True,
)
