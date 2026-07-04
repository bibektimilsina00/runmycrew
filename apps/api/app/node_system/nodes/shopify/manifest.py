"""Shopify action node — manifest form.

Shopify Admin REST API at
`https://{store}.myshopify.com/admin/api/2024-10`. Custom
`X-Shopify-Access-Token` header (not Bearer). Store subdomain rides
in the credential; the manifest resolves it via the scaffold's
`_PropCredView` and templates the full URL per op.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_STORE = "https://{store_domain}.myshopify.com/admin/api/2024-10"


MANIFEST = ProviderManifest(
    type="action.shopify",
    name="Shopify",
    category="integration",
    description="Shopify Admin — orders, products, customers, inventory.",
    icon_slug="shopify",
    color="#1c1c1c",
    base_url="",
    credential_type="shopify_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-Shopify-Access-Token",
    fields=[
        FieldSpec(name="order_id", label="Order ID", type="string"),
        FieldSpec(name="product_id", label="Product ID", type="string"),
        FieldSpec(name="customer_id", label="Customer ID", type="string"),
        FieldSpec(name="title", label="Product Title", type="string"),
        FieldSpec(
            name="status",
            label="Order Status",
            type="options",
            mode="advanced",
            options=[
                {"label": "any", "value": "any"},
                {"label": "open", "value": "open"},
                {"label": "closed", "value": "closed"},
                {"label": "cancelled", "value": "cancelled"},
            ],
        ),
        FieldSpec(
            name="financial_status", label="Financial Status", type="string", mode="advanced"
        ),
        FieldSpec(name="email", label="Customer Email", type="string"),
        FieldSpec(name="query", label="Search Query", type="string", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
        FieldSpec(name="product_data", label="Product Data (JSON)", type="json"),
        FieldSpec(name="customer_data", label="Customer Data (JSON)", type="json"),
    ],
    operations=[
        OpSpec(
            id="list_orders",
            label="List Orders",
            method="GET",
            path=f"{_STORE}/orders.json",
            visible_fields=["status", "financial_status", "limit"],
            query_fields=["status", "financial_status", "limit"],
        ),
        OpSpec(
            id="get_order",
            label="Get Order",
            method="GET",
            path=f"{_STORE}/orders/{{order_id}}.json",
            visible_fields=["order_id"],
        ),
        OpSpec(
            id="list_products",
            label="List Products",
            method="GET",
            path=f"{_STORE}/products.json",
            visible_fields=["title", "limit"],
            query_fields=["title", "limit"],
        ),
        OpSpec(
            id="get_product",
            label="Get Product",
            method="GET",
            path=f"{_STORE}/products/{{product_id}}.json",
            visible_fields=["product_id"],
        ),
        OpSpec(
            id="create_product",
            label="Create Product",
            method="POST",
            path=f"{_STORE}/products.json",
            visible_fields=["product_data"],
            body_builder=lambda v: {"product": getattr(v, "product_data", None) or {}},
        ),
        OpSpec(
            id="update_product",
            label="Update Product",
            method="PUT",
            path=f"{_STORE}/products/{{product_id}}.json",
            visible_fields=["product_id", "product_data"],
            body_builder=lambda v: {
                "product": {
                    "id": getattr(v, "product_id", None),
                    **(getattr(v, "product_data", None) or {}),
                }
            },
        ),
        OpSpec(
            id="delete_product",
            label="Delete Product",
            method="DELETE",
            path=f"{_STORE}/products/{{product_id}}.json",
            visible_fields=["product_id"],
            success_payload_template={"deleted": True, "id": "{product_id}"},
        ),
        OpSpec(
            id="list_customers",
            label="List Customers",
            method="GET",
            path=f"{_STORE}/customers.json",
            visible_fields=["limit"],
            query_fields=["limit"],
        ),
        OpSpec(
            id="search_customers",
            label="Search Customers",
            method="GET",
            path=f"{_STORE}/customers/search.json",
            visible_fields=["query", "limit"],
            query_fields=["query", "limit"],
        ),
        OpSpec(
            id="get_customer",
            label="Get Customer",
            method="GET",
            path=f"{_STORE}/customers/{{customer_id}}.json",
            visible_fields=["customer_id"],
        ),
        OpSpec(
            id="create_customer",
            label="Create Customer",
            method="POST",
            path=f"{_STORE}/customers.json",
            visible_fields=["customer_data"],
            body_builder=lambda v: {"customer": getattr(v, "customer_data", None) or {}},
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "number"},
        {"label": "name", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "orders", "type": "array"},
        {"label": "products", "type": "array"},
        {"label": "customers", "type": "array"},
        {"label": "total_price", "type": "string"},
    ],
    allow_error=True,
)
