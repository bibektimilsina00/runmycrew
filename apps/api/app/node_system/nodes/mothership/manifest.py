"""Mothership action node — Mothership — freight shipment quoting and booking.

REST at https://api.mothership.com/v1. See sim-parity roadmap Phase 4.28.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.mothership",
    name="Mothership",
    category="integration",
    description="Mothership — freight shipment quoting and booking.",
    icon_slug="mothership",
    color="#1c1c1c",
    base_url="https://api.mothership.com/v1",
    credential_type="mothership_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="group_id", label="Group ID", type="string"),
        FieldSpec(name="user_principal_name", label="User Principal Name", type="string"),
        FieldSpec(name="display_name", label="Display Name", type="string"),
        FieldSpec(name="mail_nickname", label="Mail Nickname", type="string"),
        FieldSpec(name="password", label="Password", type="string", secret=True),
        FieldSpec(name="top", label="Top", type="number", default=25, mode="advanced"),
        FieldSpec(name="filter", label="Filter", type="string", mode="advanced"),
        FieldSpec(name="entity", label="Entity (plural)", type="string", placeholder="accounts"),
        FieldSpec(name="record_id", label="Record GUID", type="string"),
        FieldSpec(name="select", label="Select", type="string", mode="advanced"),
        FieldSpec(name="data", label="Data (JSON)", type="json", default={}),
        FieldSpec(name="service_desk_id", label="Service Desk ID", type="string"),
        FieldSpec(name="request_type_id", label="Request Type ID", type="string"),
        FieldSpec(name="summary", label="Summary", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="issue_key", label="Issue Key", type="string"),
        FieldSpec(
            name="request_status", label="Request Status", type="string", default="OPEN_REQUESTS"
        ),
        FieldSpec(name="comment_body", label="Comment Body", type="string"),
        FieldSpec(name="public", label="Public", type="boolean", default=True),
        FieldSpec(name="origin_zip", label="Origin ZIP", type="string"),
        FieldSpec(name="destination_zip", label="Destination ZIP", type="string"),
        FieldSpec(name="weight_lb", label="Weight (lb)", type="number"),
        FieldSpec(name="commodity", label="Commodity", type="string"),
        FieldSpec(name="quote_id", label="Quote ID", type="string"),
        FieldSpec(name="shipment_id", label="Shipment ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="create_quote",
            label="Create Freight Quote",
            method="POST",
            path="/quotes",
            visible_fields=["origin_zip", "destination_zip", "weight_lb", "commodity"],
            body_builder=lambda v: {
                "origin_zip": getattr(v, "origin_zip", "") or "",
                "destination_zip": getattr(v, "destination_zip", "") or "",
                "weight_lb": float(getattr(v, "weight_lb", 0) or 0),
                "commodity": getattr(v, "commodity", None) or None,
            },
        ),
        OpSpec(
            id="get_quote",
            label="Get Quote",
            method="GET",
            path="/quotes/{quote_id}",
            visible_fields=["quote_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="book_shipment",
            label="Book Shipment",
            method="POST",
            path="/shipments",
            visible_fields=["quote_id"],
            body_builder=lambda v: {"quote_id": getattr(v, "quote_id", "") or ""},
        ),
        OpSpec(
            id="get_shipment",
            label="Get Shipment",
            method="GET",
            path="/shipments/{shipment_id}",
            visible_fields=["shipment_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_shipments",
            label="List Shipments",
            method="GET",
            path="/shipments",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
