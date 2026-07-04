"""AWS Secrets Manager action node — manifest form.

JSON protocol. POST `https://secretsmanager.{region}.amazonaws.com/`.
Content-Type `application/x-amz-json-1.1`. Every op ships its own
`X-Amz-Target: secretsmanager.<Action>` header.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://secretsmanager.{region}.amazonaws.com/"


MANIFEST = ProviderManifest(
    type="action.aws_secrets_manager",
    name="Secrets Manager",
    category="integration",
    description="AWS Secrets Manager — store and retrieve secrets via SigV4.",
    icon_slug="aws-secrets-manager",
    color="#1c1c1c",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="secretsmanager",
    aws_default_region="us-east-1",
    content_type="application/x-amz-json-1.1",
    fields=[
        FieldSpec(name="secret_id", label="Secret ID (name or ARN)", type="string"),
        FieldSpec(name="secret_string", label="Secret Value", type="string", secret=True),
        FieldSpec(name="description", label="Description", type="string", mode="advanced"),
        FieldSpec(name="version_id", label="Version ID", type="string", mode="advanced"),
        FieldSpec(name="version_stage", label="Version Stage", type="string", mode="advanced"),
        FieldSpec(
            name="max_results", label="Max Results", type="number", default=100, mode="advanced"
        ),
        FieldSpec(name="filter_key", label="Filter Key", type="string", mode="advanced"),
        FieldSpec(
            name="filter_values", label="Filter Values (JSON array)", type="json", mode="advanced"
        ),
    ],
    operations=[
        OpSpec(
            id="list_secrets",
            label="List Secrets",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "secretsmanager.ListSecrets"},
            visible_fields=["max_results", "filter_key", "filter_values"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "MaxResults": int(getattr(v, "max_results", 100) or 100),
                    "Filters": (
                        [
                            {
                                "Key": v.filter_key,
                                "Values": v.filter_values or [],
                            }
                        ]
                        if getattr(v, "filter_key", None)
                        else None
                    ),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_secret_value",
            label="Get Secret Value",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "secretsmanager.GetSecretValue"},
            visible_fields=["secret_id", "version_id", "version_stage"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "SecretId": getattr(v, "secret_id", None) or "",
                    "VersionId": getattr(v, "version_id", None),
                    "VersionStage": getattr(v, "version_stage", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="create_secret",
            label="Create Secret",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "secretsmanager.CreateSecret"},
            visible_fields=["secret_id", "secret_string", "description"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "Name": getattr(v, "secret_id", None) or "",
                    "SecretString": getattr(v, "secret_string", None) or "",
                    "Description": getattr(v, "description", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="put_secret_value",
            label="Put Secret Value",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "secretsmanager.PutSecretValue"},
            visible_fields=["secret_id", "secret_string"],
            body_builder=lambda v: {
                "SecretId": getattr(v, "secret_id", None) or "",
                "SecretString": getattr(v, "secret_string", None) or "",
            },
        ),
        OpSpec(
            id="delete_secret",
            label="Delete Secret",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "secretsmanager.DeleteSecret"},
            visible_fields=["secret_id"],
            body_builder=lambda v: {
                "SecretId": getattr(v, "secret_id", None) or "",
                "ForceDeleteWithoutRecovery": False,
            },
            success_payload_template={"deleted": True, "secret_id": "{secret_id}"},
        ),
        OpSpec(
            id="describe_secret",
            label="Describe Secret",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "secretsmanager.DescribeSecret"},
            visible_fields=["secret_id"],
            body_builder=lambda v: {"SecretId": getattr(v, "secret_id", None) or ""},
        ),
    ],
    outputs_schema=[
        {"label": "ARN", "type": "string"},
        {"label": "Name", "type": "string"},
        {"label": "SecretString", "type": "string"},
        {"label": "SecretList", "type": "array"},
        {"label": "VersionId", "type": "string"},
    ],
    allow_error=True,
)
