"""Square action node — manifest form.

Square Connect API at `https://connect.squareup.com/v2`. Bearer
auth + pinned `Square-Version` header. Five ops cover the common
commerce flows: customer CRUD, payment / order lookup, catalog list.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.square",
    name="Square",
    category="integration",
    description="Square Connect — payments, orders, customers, catalog.",
    icon_slug="square",
    color="#1c1c1c",
    base_url="https://connect.squareup.com/v2",
    credential_type="square_api_key",
    token_field=["api_key"],
    auth="bearer",
    extra_headers={"Square-Version": "2024-10-17"},
    fields=[
        FieldSpec(name="customer_id", label="Customer ID", type="string"),
        FieldSpec(name="payment_id", label="Payment ID", type="string"),
        FieldSpec(name="order_id", label="Order ID", type="string"),
        FieldSpec(name="given_name", label="Given Name", type="string"),
        FieldSpec(name="family_name", label="Family Name", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="phone", label="Phone", type="string", mode="advanced"),
        FieldSpec(name="company", label="Company", type="string", mode="advanced"),
        FieldSpec(name="query", label="Search Query (JSON)", type="json", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
        FieldSpec(name="location_id", label="Location ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="create_customer",
            label="Create Customer",
            method="POST",
            path="/customers",
            visible_fields=["given_name", "family_name", "email", "phone", "company"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "given_name": getattr(v, "given_name", None),
                    "family_name": getattr(v, "family_name", None),
                    "email_address": getattr(v, "email", None),
                    "phone_number": getattr(v, "phone", None),
                    "company_name": getattr(v, "company", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_customer",
            label="Get Customer",
            method="GET",
            path="/customers/{customer_id}",
            visible_fields=["customer_id"],
        ),
        OpSpec(
            id="search_customers",
            label="Search Customers",
            method="POST",
            path="/customers/search",
            visible_fields=["query", "limit"],
            body_builder=lambda v: {
                "query": getattr(v, "query", None) or {},
                "limit": int(getattr(v, "limit", 50) or 50),
            },
        ),
        OpSpec(
            id="list_customers",
            label="List Customers",
            method="GET",
            path="/customers",
            visible_fields=["limit"],
            query_fields=["limit"],
        ),
        OpSpec(
            id="get_payment",
            label="Get Payment",
            method="GET",
            path="/payments/{payment_id}",
            visible_fields=["payment_id"],
        ),
        OpSpec(
            id="list_payments",
            label="List Payments",
            method="GET",
            path="/payments",
            visible_fields=["location_id", "limit"],
            query_fields=["location_id", "limit"],
        ),
        OpSpec(
            id="get_order",
            label="Get Order",
            method="GET",
            path="/orders/{order_id}",
            visible_fields=["order_id"],
        ),
        OpSpec(
            id="search_orders",
            label="Search Orders",
            method="POST",
            path="/orders/search",
            visible_fields=["query", "limit"],
            body_builder=lambda v: {
                "query": getattr(v, "query", None) or {},
                "limit": int(getattr(v, "limit", 50) or 50),
            },
        ),
        OpSpec(
            id="list_catalog",
            label="List Catalog",
            method="GET",
            path="/catalog/list",
        ),
        OpSpec(
            id="list_locations",
            label="List Locations",
            method="GET",
            path="/locations",
        ),
    ],
    outputs_schema=[
        {"label": "customer", "type": "object"},
        {"label": "payment", "type": "object"},
        {"label": "order", "type": "object"},
        {"label": "customers", "type": "array"},
        {"label": "payments", "type": "array"},
        {"label": "orders", "type": "array"},
        {"label": "objects", "type": "array"},
        {"label": "locations", "type": "array"},
    ],
    allow_error=True,
)
