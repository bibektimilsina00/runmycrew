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
    color="#ffffff",
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
        FieldSpec(
            name="member_role",
            label="Member Role (OWNER|MANAGER|MEMBER)",
            type="string",
            default="MEMBER",
        ),
        FieldSpec(name="alias_email", label="Alias Email", type="string"),
        FieldSpec(
            name="settings_body", label="Group Settings Body (JSON)", type="json", default={}
        ),
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
        OpSpec(
            id="update_group",
            label="Update Group",
            method="PUT",
            path="/groups/{group_key}",
            visible_fields=["group_key"],
            body_builder=lambda v: {
                "name": getattr(v, "name", None) or None,
                "description": getattr(v, "description", None) or None,
            },
        ),
        OpSpec(
            id="get_member",
            label="Get Group Member",
            method="GET",
            path="/groups/{group_key}/members/{member_key}",
            visible_fields=["group_key", "member_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_member",
            label="Update Group Member Role",
            method="PUT",
            path="/groups/{group_key}/members/{member_key}",
            visible_fields=["group_key", "member_key", "member_role"],
            body_builder=lambda v: {"role": getattr(v, "member_role", None) or "MEMBER"},
        ),
        OpSpec(
            id="has_member",
            label="Has Member",
            method="GET",
            path="/groups/{group_key}/hasMember/{member_key}",
            visible_fields=["group_key", "member_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_aliases",
            label="List Group Aliases",
            method="GET",
            path="/groups/{group_key}/aliases",
            visible_fields=["group_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="add_alias",
            label="Add Group Alias",
            method="POST",
            path="/groups/{group_key}/aliases",
            visible_fields=["group_key", "alias_email"],
            body_builder=lambda v: {"alias": getattr(v, "alias_email", "") or ""},
        ),
        OpSpec(
            id="remove_alias",
            label="Remove Group Alias",
            method="DELETE",
            path="/groups/{group_key}/aliases/{alias_email}",
            visible_fields=["group_key", "alias_email"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_settings",
            label="Get Group Settings",
            method="GET",
            path="https://www.googleapis.com/groups/v1/groups/{group_key}",
            visible_fields=["group_key"],
            query_builder=lambda v: {"alt": "json"},
        ),
        OpSpec(
            id="update_settings",
            label="Update Group Settings",
            method="PATCH",
            path="https://www.googleapis.com/groups/v1/groups/{group_key}",
            visible_fields=["group_key", "settings_body"],
            body_builder=lambda v: getattr(v, "settings_body", None) or {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
