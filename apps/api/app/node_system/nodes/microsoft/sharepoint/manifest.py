"""SharePoint action node — manifest form.

Graph endpoints at `/v1.0/sites/{site_id}/...`. The user supplies the
site id (lookup-able via the search op). Lists and pages are the
primary objects we cover.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.sharepoint",
    name="SharePoint",
    category="integration",
    description="SharePoint — sites, lists, list items, pages.",
    icon_slug="sharepoint",
    color="#ffffff",
    base_url="https://graph.microsoft.com/v1.0",
    credential_type="microsoft_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(name="site_id", label="Site ID", type="string"),
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="item_id", label="Item ID", type="string"),
        FieldSpec(name="search_query", label="Search Sites", type="string"),
        FieldSpec(name="fields", label="Item Fields (JSON)", type="json"),
        FieldSpec(name="display_name", label="List Display Name", type="string"),
        FieldSpec(
            name="list_template",
            label="List Template",
            type="options",
            default="genericList",
            mode="advanced",
            options=[
                {"label": "Generic List", "value": "genericList"},
                {"label": "Document Library", "value": "documentLibrary"},
                {"label": "Tasks", "value": "tasks"},
            ],
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="search_sites",
            label="Search Sites",
            method="GET",
            path="/sites",
            visible_fields=["search_query"],
            query_builder=lambda v: {"search": getattr(v, "search_query", None) or ""},
        ),
        OpSpec(
            id="get_site",
            label="Get Site",
            method="GET",
            path="/sites/{site_id}",
            visible_fields=["site_id"],
        ),
        OpSpec(
            id="list_lists",
            label="List Lists on Site",
            method="GET",
            path="/sites/{site_id}/lists",
            visible_fields=["site_id"],
        ),
        OpSpec(
            id="get_list",
            label="Get List",
            method="GET",
            path="/sites/{site_id}/lists/{list_id}",
            visible_fields=["site_id", "list_id"],
        ),
        OpSpec(
            id="create_list",
            label="Create List",
            method="POST",
            path="/sites/{site_id}/lists",
            visible_fields=["site_id", "display_name", "list_template"],
            body_builder=lambda v: {
                "displayName": getattr(v, "display_name", None) or "",
                "list": {"template": getattr(v, "list_template", None) or "genericList"},
            },
        ),
        OpSpec(
            id="list_items",
            label="List Items",
            method="GET",
            path="/sites/{site_id}/lists/{list_id}/items",
            visible_fields=["site_id", "list_id", "limit"],
            query_builder=lambda v: {
                "$top": int(getattr(v, "limit", 50) or 50),
                "$expand": "fields",
            },
        ),
        OpSpec(
            id="create_item",
            label="Create List Item",
            method="POST",
            path="/sites/{site_id}/lists/{list_id}/items",
            visible_fields=["site_id", "list_id", "fields"],
            body_builder=lambda v: {"fields": getattr(v, "fields", None) or {}},
        ),
        OpSpec(
            id="update_item",
            label="Update List Item Fields",
            method="PATCH",
            path="/sites/{site_id}/lists/{list_id}/items/{item_id}/fields",
            visible_fields=["site_id", "list_id", "item_id", "fields"],
            body_builder=lambda v: getattr(v, "fields", None) or {},
        ),
        OpSpec(
            id="delete_item",
            label="Delete List Item",
            method="DELETE",
            path="/sites/{site_id}/lists/{list_id}/items/{item_id}",
            visible_fields=["site_id", "list_id", "item_id"],
            success_payload_template={"deleted": True, "id": "{item_id}"},
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "displayName", "type": "string"},
        {"label": "webUrl", "type": "string"},
        {"label": "value", "type": "array"},
        {"label": "fields", "type": "object"},
    ],
    allow_error=True,
)
