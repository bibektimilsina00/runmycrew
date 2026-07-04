"""AWS S3 action node — manifest form.

S3 REST API — path-style URLs against the regional endpoint
`https://s3.{region}.amazonaws.com`. All requests signed with SigV4.
The scaffold's `aws_sigv4` scheme + `aws_service="s3"` handles signing;
the manifest just declares the routes.

Ops cover the workflow-common surface: list objects, get/put/delete
object, head object metadata, list + create + delete buckets.

Uploads default to signed payloads (safer). For very large uploads,
set `aws_unsigned_payload=True` on the manifest at ship time — worth
the tradeoff for TB-scale streams; not worth it for typical bodies.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

# `{region}` resolves via _PropCredView from credential.region; if
# missing it falls through unresolved so misconfiguration is loud
# instead of silently defaulting to a wrong bucket location.
_S3_HOST = "https://s3.{region}.amazonaws.com"


MANIFEST = ProviderManifest(
    type="action.aws_s3",
    name="S3",
    category="integration",
    description="AWS S3 — buckets and objects via SigV4.",
    icon_slug="aws-s3",
    color="#1c1c1c",
    base_url="",
    credential_type="aws_credentials",
    # SigV4 reads access_key_id + secret_access_key from the credential
    # directly; `token_field` still needs a non-empty pointer so the
    # scaffold's "credential connected" check passes.
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="s3",
    aws_default_region="us-east-1",
    fields=[
        FieldSpec(name="bucket", label="Bucket", type="string", required=True),
        FieldSpec(name="key", label="Object Key", type="string"),
        FieldSpec(name="body", label="Body (text)", type="string"),
        FieldSpec(
            name="content_type",
            label="Object Content-Type",
            type="string",
            default="application/octet-stream",
            mode="advanced",
        ),
        FieldSpec(name="prefix", label="Prefix", type="string", mode="advanced"),
        FieldSpec(name="delimiter", label="Delimiter", type="string", mode="advanced"),
        FieldSpec(name="max_keys", label="Max Keys", type="number", default=1000, mode="advanced"),
        FieldSpec(
            name="continuation_token",
            label="Continuation Token",
            type="string",
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="list_buckets",
            label="List Buckets",
            method="GET",
            path=_S3_HOST + "/",
        ),
        OpSpec(
            id="create_bucket",
            label="Create Bucket",
            method="PUT",
            path=_S3_HOST + "/{bucket}",
            visible_fields=["bucket"],
        ),
        OpSpec(
            id="delete_bucket",
            label="Delete Bucket",
            method="DELETE",
            path=_S3_HOST + "/{bucket}",
            visible_fields=["bucket"],
            success_payload_template={"deleted": True, "bucket": "{bucket}"},
        ),
        OpSpec(
            id="list_objects",
            label="List Objects",
            method="GET",
            path=_S3_HOST + "/{bucket}",
            visible_fields=["bucket", "prefix", "delimiter", "max_keys", "continuation_token"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "list-type": "2",
                    "prefix": getattr(v, "prefix", None),
                    "delimiter": getattr(v, "delimiter", None),
                    "max-keys": int(getattr(v, "max_keys", 1000) or 1000),
                    "continuation-token": getattr(v, "continuation_token", None),
                }.items()
                if val not in (None, "")
            },
        ),
        OpSpec(
            id="head_object",
            label="Head Object (metadata)",
            method="HEAD",
            path=_S3_HOST + "/{bucket}/{key}",
            visible_fields=["bucket", "key"],
        ),
        OpSpec(
            id="get_object",
            label="Get Object",
            method="GET",
            path=_S3_HOST + "/{bucket}/{key}",
            visible_fields=["bucket", "key"],
        ),
        OpSpec(
            id="put_object",
            label="Put Object",
            method="PUT",
            path=_S3_HOST + "/{bucket}/{key}",
            visible_fields=["bucket", "key", "body", "content_type"],
            body_builder=lambda v: getattr(v, "body", None) or "",
        ),
        OpSpec(
            id="delete_object",
            label="Delete Object",
            method="DELETE",
            path=_S3_HOST + "/{bucket}/{key}",
            visible_fields=["bucket", "key"],
            success_payload_template={"deleted": True, "key": "{key}"},
        ),
    ],
    outputs_schema=[
        {"label": "Key", "type": "string"},
        {"label": "Size", "type": "number"},
        {"label": "ETag", "type": "string"},
        {"label": "LastModified", "type": "string"},
        {"label": "Contents", "type": "array"},
        {"label": "Buckets", "type": "array"},
    ],
    # S3 returns XML by default. We accept the raw text through via
    # rest_request's fallback branch; parsing XML → JSON is a future
    # scaffold add-on. For now downstream nodes can JSON-transform.
    content_type="application/octet-stream",
    allow_error=True,
)
