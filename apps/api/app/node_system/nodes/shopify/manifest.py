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
    color="#ffffff",
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
        FieldSpec(name="shopify_product_id", label="Product ID", type="string"),
        FieldSpec(
            name="shopify_product_body", label="Product Body (JSON)", type="json", default={}
        ),
        FieldSpec(name="shopify_order_id", label="Order ID", type="string"),
        FieldSpec(name="shopify_order_body", label="Order Body (JSON)", type="json", default={}),
        FieldSpec(name="shopify_customer_id", label="Customer ID", type="string"),
        FieldSpec(
            name="shopify_customer_body", label="Customer Body (JSON)", type="json", default={}
        ),
        FieldSpec(name="inventory_item_id", label="Inventory Item ID", type="string"),
        FieldSpec(name="location_id", label="Location ID", type="string"),
        FieldSpec(
            name="available_adjustment", label="Available Adjustment", type="number", default=0
        ),
        FieldSpec(
            name="fulfillment_body", label="Fulfillment Body (JSON)", type="json", default={}
        ),
        FieldSpec(name="collection_id", label="Collection ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="search_customers",
            label="Search Customers",
            method="GET",
            path=f"{_STORE}/customers/search.json",
            visible_fields=["query", "limit"],
            query_fields=["query", "limit"],
        ),
        OpSpec(
            id="create_product",
            label="Create Product",
            method="POST",
            path="/admin/api/2024-10/products.json",
            visible_fields=["shopify_product_body"],
            body_builder=lambda v: {"product": getattr(v, "shopify_product_body", None) or {}},
        ),
        OpSpec(
            id="get_product",
            label="Get Product",
            method="GET",
            path="/admin/api/2024-10/products/{shopify_product_id}.json",
            visible_fields=["shopify_product_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_products",
            label="List Products",
            method="GET",
            path="/admin/api/2024-10/products.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_product",
            label="Update Product",
            method="PUT",
            path="/admin/api/2024-10/products/{shopify_product_id}.json",
            visible_fields=["shopify_product_id", "shopify_product_body"],
            body_builder=lambda v: {"product": getattr(v, "shopify_product_body", None) or {}},
        ),
        OpSpec(
            id="delete_product",
            label="Delete Product",
            method="DELETE",
            path="/admin/api/2024-10/products/{shopify_product_id}.json",
            visible_fields=["shopify_product_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_order",
            label="Get Order",
            method="GET",
            path="/admin/api/2024-10/orders/{shopify_order_id}.json",
            visible_fields=["shopify_order_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_orders",
            label="List Orders",
            method="GET",
            path="/admin/api/2024-10/orders.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_order",
            label="Update Order",
            method="PUT",
            path="/admin/api/2024-10/orders/{shopify_order_id}.json",
            visible_fields=["shopify_order_id", "shopify_order_body"],
            body_builder=lambda v: {"order": getattr(v, "shopify_order_body", None) or {}},
        ),
        OpSpec(
            id="cancel_order",
            label="Cancel Order",
            method="POST",
            path="/admin/api/2024-10/orders/{shopify_order_id}/cancel.json",
            visible_fields=["shopify_order_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="create_customer",
            label="Create Customer",
            method="POST",
            path="/admin/api/2024-10/customers.json",
            visible_fields=["shopify_customer_body"],
            body_builder=lambda v: {"customer": getattr(v, "shopify_customer_body", None) or {}},
        ),
        OpSpec(
            id="get_customer",
            label="Get Customer",
            method="GET",
            path="/admin/api/2024-10/customers/{shopify_customer_id}.json",
            visible_fields=["shopify_customer_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_customers",
            label="List Customers",
            method="GET",
            path="/admin/api/2024-10/customers.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_customer",
            label="Update Customer",
            method="PUT",
            path="/admin/api/2024-10/customers/{shopify_customer_id}.json",
            visible_fields=["shopify_customer_id", "shopify_customer_body"],
            body_builder=lambda v: {"customer": getattr(v, "shopify_customer_body", None) or {}},
        ),
        OpSpec(
            id="delete_customer",
            label="Delete Customer",
            method="DELETE",
            path="/admin/api/2024-10/customers/{shopify_customer_id}.json",
            visible_fields=["shopify_customer_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_inventory_items",
            label="List Inventory Items",
            method="GET",
            path="/admin/api/2024-10/inventory_items.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_inventory_level",
            label="Get Inventory Level",
            method="GET",
            path="/admin/api/2024-10/inventory_levels.json",
            visible_fields=["inventory_item_id", "location_id"],
            query_builder=lambda v: {
                "inventory_item_ids": getattr(v, "inventory_item_id", "") or "",
                "location_ids": getattr(v, "location_id", "") or "",
            },
        ),
        OpSpec(
            id="adjust_inventory",
            label="Adjust Inventory",
            method="POST",
            path="/admin/api/2024-10/inventory_levels/adjust.json",
            visible_fields=["inventory_item_id", "location_id", "available_adjustment"],
            body_builder=lambda v: {
                "inventory_item_id": int(getattr(v, "inventory_item_id", 0) or 0),
                "location_id": int(getattr(v, "location_id", 0) or 0),
                "available_adjustment": int(getattr(v, "available_adjustment", 0) or 0),
            },
        ),
        OpSpec(
            id="list_locations",
            label="List Locations",
            method="GET",
            path="/admin/api/2024-10/locations.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_fulfillment",
            label="Create Fulfillment",
            method="POST",
            path="/admin/api/2024-10/fulfillments.json",
            visible_fields=["fulfillment_body"],
            body_builder=lambda v: {"fulfillment": getattr(v, "fulfillment_body", None) or {}},
        ),
        OpSpec(
            id="list_collections",
            label="List Collections",
            method="GET",
            path="/admin/api/2024-10/custom_collections.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_collection",
            label="Get Collection",
            method="GET",
            path="/admin/api/2024-10/custom_collections/{collection_id}.json",
            visible_fields=["collection_id"],
            query_builder=lambda v: {},
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
