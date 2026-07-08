"""Microsoft Entra ID action node — Microsoft Entra ID (Azure AD) — users, groups, apps via Graph.

REST at https://graph.microsoft.com/v1.0. See sim-parity roadmap Phase 4.28.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.microsoft_ad",
    name="Microsoft Entra ID",
    category="integration",
    description="Microsoft Entra ID (Azure AD) — users, groups, apps via Graph.",
    icon_slug="microsoft_ad",
    color="#ffffff",
    base_url="https://graph.microsoft.com/v1.0",
    credential_type="microsoft_oauth",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="group_id", label="Group ID", type="string"),
        FieldSpec(name="user_principal_name", label="User Principal Name", type="string"),
        FieldSpec(name="display_name", label="Display Name", type="string"),
        FieldSpec(name="mail_nickname", label="Mail Nickname", type="string"),
        FieldSpec(name="password", label="Password", type="string", secret=True),
        FieldSpec(name="top", label="Top", type="number", default=25, mode="advanced"),
        FieldSpec(name="filter", label="Filter", type="string", mode="advanced"),
        FieldSpec(name="entity", label="Entity (plural)", type="string", placeholder="accounts"),
        FieldSpec(name="record_id", label="Record GUID", type="string"),
        FieldSpec(name="select", label="Select", type="string", mode="advanced"),
        FieldSpec(name="data", label="Data (JSON)", type="json", default={}),
        FieldSpec(name="service_desk_id", label="Service Desk ID", type="string"),
        FieldSpec(name="request_type_id", label="Request Type ID", type="string"),
        FieldSpec(name="summary", label="Summary", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="issue_key", label="Issue Key", type="string"),
        FieldSpec(
            name="request_status", label="Request Status", type="string", default="OPEN_REQUESTS"
        ),
        FieldSpec(name="comment_body", label="Comment Body", type="string"),
        FieldSpec(name="public", label="Public", type="boolean", default=True),
        FieldSpec(name="origin_zip", label="Origin ZIP", type="string"),
        FieldSpec(name="destination_zip", label="Destination ZIP", type="string"),
        FieldSpec(name="weight_lb", label="Weight (lb)", type="number"),
        FieldSpec(name="commodity", label="Commodity", type="string"),
        FieldSpec(name="quote_id", label="Quote ID", type="string"),
        FieldSpec(name="shipment_id", label="Shipment ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_users",
            label="List Users",
            method="GET",
            path="/users",
            visible_fields=["top", "filter"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "$top": getattr(v, "top", None) or None,
                    "$filter": getattr(v, "filter", None) or None,
                }.items()
                if val
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
            visible_fields=["user_principal_name", "display_name", "mail_nickname", "password"],
            body_builder=lambda v: {
                "accountEnabled": True,
                "displayName": getattr(v, "display_name", "") or "",
                "mailNickname": getattr(v, "mail_nickname", "") or "",
                "userPrincipalName": getattr(v, "user_principal_name", "") or "",
                "passwordProfile": {
                    "forceChangePasswordNextSignIn": True,
                    "password": getattr(v, "password", "") or "",
                },
            },
        ),
        OpSpec(
            id="update_user",
            label="Update User",
            method="PATCH",
            path="/users/{user_id}",
            visible_fields=["user_id", "display_name"],
            body_builder=lambda v: {
                k: val
                for k, val in {"displayName": getattr(v, "display_name", None) or None}.items()
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
            id="list_groups",
            label="List Groups",
            method="GET",
            path="/groups",
            visible_fields=["top"],
            query_builder=lambda v: {
                k: val for k, val in {"$top": getattr(v, "top", None) or None}.items() if val
            },
        ),
        OpSpec(
            id="add_group_member",
            label="Add Group Member",
            method="POST",
            path="/groups/{group_id}/members/$ref",
            visible_fields=["group_id", "user_id"],
            body_builder=lambda v: {
                "@odata.id": "https://graph.microsoft.com/v1.0/directoryObjects/"
                + (getattr(v, "user_id", "") or "")
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
