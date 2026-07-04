"""Google Groups action node — Google Groups — Directory API groups/members admin.

REST at https://admin.googleapis.com/admin/directory/v1. See sim-parity roadmap Phase 4.27.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.google_groups",
    name="Google Groups",
    category="integration",
    description="Google Groups — Directory API groups/members admin.",
    icon_slug="google_groups",
    color="#4285F4",
    base_url="https://admin.googleapis.com/admin/directory/v1",
    credential_type="google_oauth",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="url", label="URL", type="string"),
        FieldSpec(name="strategy", label="Strategy", type="string", default="mobile"),
        FieldSpec(name="category", label="Category", type="string", default="performance"),
        FieldSpec(name="query", label="Query", type="string"),
        FieldSpec(
            name="max_results", label="Max Results", type="number", default=10, mode="advanced"
        ),
        FieldSpec(name="volume_id", label="Volume ID", type="string"),
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="customer", label="Customer", type="string", default="my_customer"),
        FieldSpec(name="group_key", label="Group Key", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="role", label="Role", type="string", default="MEMBER"),
        FieldSpec(name="member_key", label="Member Key", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_groups",
            label="List Groups",
            method="GET",
            path="/groups",
            visible_fields=["domain", "customer"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "domain": getattr(v, "domain", None) or None,
                    "customer": getattr(v, "customer", None) or None,
                }.items()
                if val
            },
        ),
        OpSpec(
            id="get_group",
            label="Get Group",
            method="GET",
            path="/groups/{group_key}",
            visible_fields=["group_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_group",
            label="Create Group",
            method="POST",
            path="/groups",
            visible_fields=["email", "name", "description"],
            body_builder=lambda v: {
                "email": getattr(v, "email", "") or "",
                "name": getattr(v, "name", None) or None,
                "description": getattr(v, "description", None) or None,
            },
        ),
        OpSpec(
            id="delete_group",
            label="Delete Group",
            method="DELETE",
            path="/groups/{group_key}",
            visible_fields=["group_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_members",
            label="List Members",
            method="GET",
            path="/groups/{group_key}/members",
            visible_fields=["group_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="add_member",
            label="Add Member",
            method="POST",
            path="/groups/{group_key}/members",
            visible_fields=["group_key", "email", "role"],
            body_builder=lambda v: {
                "email": getattr(v, "email", "") or "",
                "role": (getattr(v, "role", None) or "MEMBER").upper(),
            },
        ),
        OpSpec(
            id="remove_member",
            label="Remove Member",
            method="DELETE",
            path="/groups/{group_key}/members/{member_key}",
            visible_fields=["group_key", "member_key"],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
