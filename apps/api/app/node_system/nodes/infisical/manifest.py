"""Infisical action node — Infisical — secrets management (open-source Vault alt).

REST at https://app.infisical.com/api/v3. See sim-parity roadmap Phase 4.25.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.infisical",
    name="Infisical",
    category="integration",
    description="Infisical — secrets management (open-source Vault alt).",
    icon_slug="infisical",
    color="#1c1c1c",
    base_url="https://app.infisical.com/api/v3",
    credential_type="infisical_api_key",
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
            id="list_secrets",
            label="List Secrets",
            method="GET",
            path="/secrets/raw",
            visible_fields=["workspace_id", "environment", "secret_path"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "workspaceId": getattr(v, "workspace_id", None) or None,
                    "environment": getattr(v, "environment", None) or None,
                    "secretPath": getattr(v, "secret_path", None) or "/",
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_secret",
            label="Get Secret",
            method="GET",
            path="/secrets/raw/{secret_name}",
            visible_fields=["secret_name", "workspace_id", "environment"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "workspaceId": getattr(v, "workspace_id", None) or None,
                    "environment": getattr(v, "environment", None) or None,
                    "secretPath": getattr(v, "secret_path", None) or "/",
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="create_secret",
            label="Create Secret",
            method="POST",
            path="/secrets/raw/{secret_name}",
            visible_fields=["secret_name", "workspace_id", "environment", "secret_value"],
            body_builder=lambda v: {
                "workspaceId": getattr(v, "workspace_id", "") or "",
                "environment": getattr(v, "environment", "") or "",
                "secretValue": getattr(v, "secret_value", "") or "",
                "secretPath": getattr(v, "secret_path", None) or "/",
            },
        ),
        OpSpec(
            id="update_secret",
            label="Update Secret",
            method="PATCH",
            path="/secrets/raw/{secret_name}",
            visible_fields=["secret_name", "workspace_id", "environment", "secret_value"],
            body_builder=lambda v: {
                "workspaceId": getattr(v, "workspace_id", "") or "",
                "environment": getattr(v, "environment", "") or "",
                "secretValue": getattr(v, "secret_value", "") or "",
                "secretPath": getattr(v, "secret_path", None) or "/",
            },
        ),
        OpSpec(
            id="delete_secret",
            label="Delete Secret",
            method="DELETE",
            path="/secrets/raw/{secret_name}",
            visible_fields=["secret_name", "workspace_id", "environment"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "workspaceId": getattr(v, "workspace_id", None) or None,
                    "environment": getattr(v, "environment", None) or None,
                }.items()
                if val is not None
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
