"""Clerk action node — Clerk — user + org management (dev-first auth).

REST at https://api.clerk.com/v1. See sim-parity roadmap Phase 4.25.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.clerk",
    name="Clerk",
    category="integration",
    description="Clerk — user + org management (dev-first auth).",
    icon_slug="clerk",
    color="#ffffff",
    base_url="https://api.clerk.com/v1",
    credential_type="clerk_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="group_id", label="Group ID", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="password", label="Password", type="string", secret=True),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="vault_id", label="Vault ID", type="string"),
        FieldSpec(name="item_id", label="Item ID", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="identity_store_id", label="Identity Store ID", type="string"),
        FieldSpec(name="workspace_id", label="Workspace ID", type="string"),
        FieldSpec(name="environment", label="Environment slug", type="string"),
        FieldSpec(name="secret_path", label="Secret Path", type="string", default="/"),
        FieldSpec(name="secret_name", label="Secret Name", type="string"),
        FieldSpec(name="secret_value", label="Secret Value", type="string"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_users",
            label="List Users",
            method="GET",
            path="/users",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="get_user",
            label="Get User",
            method="GET",
            path="/users/{user_id}",
            visible_fields=["user_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_user",
            label="Create User",
            method="POST",
            path="/users",
            visible_fields=["email", "password", "first_name", "last_name"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email_address": [getattr(v, "email", "") or ""],
                    "password": getattr(v, "password", None) or None,
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="update_user",
            label="Update User",
            method="PATCH",
            path="/users/{user_id}",
            visible_fields=["user_id", "first_name", "last_name"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "first_name": getattr(v, "first_name", None) or None,
                    "last_name": getattr(v, "last_name", None) or None,
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_user",
            label="Delete User",
            method="DELETE",
            path="/users/{user_id}",
            visible_fields=["user_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_organizations",
            label="List Organizations",
            method="GET",
            path="/organizations",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
