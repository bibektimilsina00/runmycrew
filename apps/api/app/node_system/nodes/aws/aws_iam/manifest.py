"""AWS IAM action node — manifest form.

IAM uses AWS's Query protocol: POST to `https://iam.amazonaws.com/`
with `application/x-www-form-urlencoded` body carrying
`Action=<Name>&Version=2010-05-08&<params>`. SigV4 signs the encoded
body — the scaffold's SigV4 path handles form-encoded bodies via the
urlencode branch in `rest_request`.

IAM is global (single endpoint, region always us-east-1).
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://iam.amazonaws.com/"
_VERSION = "2010-05-08"


def _q(action: str, **params) -> dict:
    return {
        "Action": action,
        "Version": _VERSION,
        **{k: v for k, v in params.items() if v is not None},
    }


MANIFEST = ProviderManifest(
    type="action.aws_iam",
    name="AWS IAM",
    category="integration",
    description="AWS IAM — users, groups, roles, policies via SigV4.",
    icon_slug="aws-iam",
    color="#ffffff",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="iam",
    aws_default_region="us-east-1",  # IAM is global — always us-east-1
    content_type="application/x-www-form-urlencoded",
    fields=[
        FieldSpec(name="user_name", label="User Name", type="string"),
        FieldSpec(name="group_name", label="Group Name", type="string"),
        FieldSpec(name="role_name", label="Role Name", type="string"),
        FieldSpec(name="policy_arn", label="Policy ARN", type="string"),
        FieldSpec(name="policy_document", label="Policy Document (JSON)", type="json"),
        FieldSpec(
            name="assume_role_policy_document",
            label="Assume Role Policy Document (JSON)",
            type="json",
            mode="advanced",
        ),
        FieldSpec(name="max_items", label="Max Items", type="number", default=100, mode="advanced"),
        FieldSpec(name="marker", label="Marker (pagination)", type="string", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_users",
            label="List Users",
            method="POST",
            path=_HOST,
            visible_fields=["max_items", "marker"],
            body_builder=lambda v: _q(
                "ListUsers",
                MaxItems=int(getattr(v, "max_items", 100) or 100),
                Marker=getattr(v, "marker", None),
            ),
        ),
        OpSpec(
            id="get_user",
            label="Get User",
            method="POST",
            path=_HOST,
            visible_fields=["user_name"],
            body_builder=lambda v: _q("GetUser", UserName=getattr(v, "user_name", None) or ""),
        ),
        OpSpec(
            id="create_user",
            label="Create User",
            method="POST",
            path=_HOST,
            visible_fields=["user_name"],
            body_builder=lambda v: _q("CreateUser", UserName=getattr(v, "user_name", None) or ""),
        ),
        OpSpec(
            id="delete_user",
            label="Delete User",
            method="POST",
            path=_HOST,
            visible_fields=["user_name"],
            body_builder=lambda v: _q("DeleteUser", UserName=getattr(v, "user_name", None) or ""),
            success_payload_template={"deleted": True, "user_name": "{user_name}"},
        ),
        OpSpec(
            id="list_roles",
            label="List Roles",
            method="POST",
            path=_HOST,
            visible_fields=["max_items"],
            body_builder=lambda v: _q(
                "ListRoles", MaxItems=int(getattr(v, "max_items", 100) or 100)
            ),
        ),
        OpSpec(
            id="get_role",
            label="Get Role",
            method="POST",
            path=_HOST,
            visible_fields=["role_name"],
            body_builder=lambda v: _q("GetRole", RoleName=getattr(v, "role_name", None) or ""),
        ),
        OpSpec(
            id="create_role",
            label="Create Role",
            method="POST",
            path=_HOST,
            visible_fields=["role_name", "assume_role_policy_document"],
            body_builder=lambda v: _q(
                "CreateRole",
                RoleName=getattr(v, "role_name", None) or "",
                AssumeRolePolicyDocument=__import__("json").dumps(
                    getattr(v, "assume_role_policy_document", None) or {}
                ),
            ),
        ),
        OpSpec(
            id="attach_user_policy",
            label="Attach Managed Policy to User",
            method="POST",
            path=_HOST,
            visible_fields=["user_name", "policy_arn"],
            body_builder=lambda v: _q(
                "AttachUserPolicy",
                UserName=getattr(v, "user_name", None) or "",
                PolicyArn=getattr(v, "policy_arn", None) or "",
            ),
        ),
        OpSpec(
            id="attach_role_policy",
            label="Attach Managed Policy to Role",
            method="POST",
            path=_HOST,
            visible_fields=["role_name", "policy_arn"],
            body_builder=lambda v: _q(
                "AttachRolePolicy",
                RoleName=getattr(v, "role_name", None) or "",
                PolicyArn=getattr(v, "policy_arn", None) or "",
            ),
        ),
        OpSpec(
            id="list_groups",
            label="List Groups",
            method="POST",
            path=_HOST,
            visible_fields=["max_items"],
            body_builder=lambda v: _q(
                "ListGroups", MaxItems=int(getattr(v, "max_items", 100) or 100)
            ),
        ),
    ],
    outputs_schema=[
        {"label": "ListUsersResult", "type": "object"},
        {"label": "GetUserResult", "type": "object"},
        {"label": "CreateUserResult", "type": "object"},
        {"label": "ListRolesResult", "type": "object"},
        {"label": "ResponseMetadata", "type": "object"},
    ],
    allow_error=True,
)
