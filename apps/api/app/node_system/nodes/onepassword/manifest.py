"""1Password Connect action node — 1Password — fetch secrets from a vault via Connect API.

REST at {host}/v1. See sim-parity roadmap Phase 4.25.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.onepassword",
    name="1Password Connect",
    category="integration",
    description="1Password — fetch secrets from a vault via Connect API.",
    icon_slug="onepassword",
    color="#1c1c1c",
    base_url="{host}/v1",
    credential_type="onepassword_api_key",
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
            id="list_vaults",
            label="List Vaults",
            method="GET",
            path="/vaults",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_items",
            label="List Items in Vault",
            method="GET",
            path="/vaults/{vault_id}/items",
            visible_fields=["vault_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_item",
            label="Get Item",
            method="GET",
            path="/vaults/{vault_id}/items/{item_id}",
            visible_fields=["vault_id", "item_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_item_by_title",
            label="Get Item by Title (via filter)",
            method="GET",
            path="/vaults/{vault_id}/items",
            visible_fields=["vault_id", "title"],
            query_builder=lambda v: {
                "filter": 'title eq "' + (getattr(v, "title", "") or "") + '"'
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
