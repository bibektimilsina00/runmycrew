"""AWS Identity Center action node — AWS Identity Center (SSO) — users, groups, permissions.

REST at https://identitystore.{region}.amazonaws.com. See sim-parity roadmap Phase 4.25.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.identity_center",
    name="AWS Identity Center",
    category="integration",
    description="AWS Identity Center (SSO) — users, groups, permissions.",
    icon_slug="identity_center",
    color="#1c1c1c",
    base_url="https://identitystore.{region}.amazonaws.com",
    credential_type="aws_credentials",
    token_field=["api_key"],
    auth="aws_sigv4",
    aws_service="identitystore",
    extra_headers={"X-Amz-Target": "AWSIdentityStore.ListUsers"},
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
            method="POST",
            path="/",
            visible_fields=["identity_store_id"],
            body_builder=lambda v: {"IdentityStoreId": getattr(v, "identity_store_id", "") or ""},
        ),
        OpSpec(
            id="list_groups",
            label="List Groups",
            method="POST",
            path="/",
            visible_fields=["identity_store_id"],
            body_builder=lambda v: {"IdentityStoreId": getattr(v, "identity_store_id", "") or ""},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
