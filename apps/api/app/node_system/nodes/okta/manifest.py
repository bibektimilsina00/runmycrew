"""Okta action node — Okta — identity users, groups, apps, MFA.

REST at https://{domain}/api/v1. See sim-parity roadmap Phase 4.25.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.okta",
    name="Okta",
    category="integration",
    description="Okta — identity users, groups, apps, MFA.",
    icon_slug="okta",
    color="#1c1c1c",
    base_url="https://{domain}/api/v1",
    credential_type="okta_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="Authorization",
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
            visible_fields=["limit", "query"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "limit": int(getattr(v, "limit", 25) or 25),
                    "q": getattr(v, "query", None) or None,
                }.items()
                if val is not None
            },
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
            visible_fields=["email", "first_name", "last_name"],
            body_builder=lambda v: {
                "profile": {
                    "email": getattr(v, "email", "") or "",
                    "login": getattr(v, "email", "") or "",
                    "firstName": getattr(v, "first_name", "") or "",
                    "lastName": getattr(v, "last_name", "") or "",
                }
            },
        ),
        OpSpec(
            id="deactivate_user",
            label="Deactivate User",
            method="POST",
            path="/users/{user_id}/lifecycle/deactivate",
            visible_fields=["user_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_groups",
            label="List Groups",
            method="GET",
            path="/groups",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="assign_group",
            label="Assign User to Group",
            method="PUT",
            path="/groups/{group_id}/users/{user_id}",
            visible_fields=["group_id", "user_id"],
            body_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
