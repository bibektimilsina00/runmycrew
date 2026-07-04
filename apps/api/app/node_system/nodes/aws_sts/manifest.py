"""AWS STS action node — manifest form.

Query protocol at `https://sts.amazonaws.com/`. Version `2011-06-15`.
STS is global (single endpoint, region us-east-1).

Standard STS ops: `GetCallerIdentity`, `AssumeRole`,
`AssumeRoleWithWebIdentity`. Federated + session token ops for
cross-account access.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://sts.amazonaws.com/"
_VERSION = "2011-06-15"


def _q(action: str, **params) -> dict:
    return {
        "Action": action,
        "Version": _VERSION,
        **{k: v for k, v in params.items() if v is not None},
    }


MANIFEST = ProviderManifest(
    type="action.aws_sts",
    name="AWS STS",
    category="integration",
    description="AWS STS — get caller identity, assume roles, session tokens.",
    icon_slug="aws-sts",
    color="#1c1c1c",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="sts",
    aws_default_region="us-east-1",
    content_type="application/x-www-form-urlencoded",
    fields=[
        FieldSpec(name="role_arn", label="Role ARN", type="string"),
        FieldSpec(name="session_name", label="Role Session Name", type="string"),
        FieldSpec(
            name="duration_seconds",
            label="Duration Seconds",
            type="number",
            default=3600,
            mode="advanced",
        ),
        FieldSpec(name="external_id", label="External ID", type="string", mode="advanced"),
        FieldSpec(name="policy", label="Session Policy (JSON)", type="json", mode="advanced"),
        FieldSpec(
            name="web_identity_token", label="Web Identity Token", type="string", mode="advanced"
        ),
    ],
    operations=[
        OpSpec(
            id="get_caller_identity",
            label="Get Caller Identity",
            method="POST",
            path=_HOST,
            body_builder=lambda v: _q("GetCallerIdentity"),
        ),
        OpSpec(
            id="assume_role",
            label="Assume Role",
            method="POST",
            path=_HOST,
            visible_fields=[
                "role_arn",
                "session_name",
                "duration_seconds",
                "external_id",
                "policy",
            ],
            body_builder=lambda v: _q(
                "AssumeRole",
                RoleArn=getattr(v, "role_arn", None) or "",
                RoleSessionName=getattr(v, "session_name", None) or "",
                DurationSeconds=int(getattr(v, "duration_seconds", 3600) or 3600),
                ExternalId=getattr(v, "external_id", None),
                Policy=(
                    __import__("json").dumps(v.policy)
                    if getattr(v, "policy", None) is not None
                    else None
                ),
            ),
        ),
        OpSpec(
            id="assume_role_with_web_identity",
            label="Assume Role with Web Identity",
            method="POST",
            path=_HOST,
            visible_fields=["role_arn", "session_name", "web_identity_token", "duration_seconds"],
            body_builder=lambda v: _q(
                "AssumeRoleWithWebIdentity",
                RoleArn=getattr(v, "role_arn", None) or "",
                RoleSessionName=getattr(v, "session_name", None) or "",
                WebIdentityToken=getattr(v, "web_identity_token", None) or "",
                DurationSeconds=int(getattr(v, "duration_seconds", 3600) or 3600),
            ),
        ),
        OpSpec(
            id="get_session_token",
            label="Get Session Token",
            method="POST",
            path=_HOST,
            visible_fields=["duration_seconds"],
            body_builder=lambda v: _q(
                "GetSessionToken",
                DurationSeconds=int(getattr(v, "duration_seconds", 3600) or 3600),
            ),
        ),
    ],
    outputs_schema=[
        {"label": "GetCallerIdentityResult", "type": "object"},
        {"label": "AssumeRoleResult", "type": "object"},
        {"label": "Credentials", "type": "object"},
        {"label": "AssumedRoleUser", "type": "object"},
        {"label": "ResponseMetadata", "type": "object"},
    ],
    allow_error=True,
)
