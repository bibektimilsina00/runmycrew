"""AWS SES action node — manifest form.

SES v2 REST API at `https://email.{region}.amazonaws.com/v2/email/...`.
SigV4 signed. Covers send_email + template + identity ops that show
up in most workflows.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_SES_HOST = "https://email.{region}.amazonaws.com/v2"


def _send_body(props):
    to = getattr(props, "to", None) or ""
    to_list = [addr.strip() for addr in str(to).split(",") if addr.strip()]
    return {
        "FromEmailAddress": getattr(props, "from_", None) or "",
        "Destination": {"ToAddresses": to_list},
        "Content": {
            "Simple": {
                "Subject": {"Data": getattr(props, "subject", None) or ""},
                "Body": {
                    k: {"Data": v}
                    for k, v in {
                        "Html": getattr(props, "html", None),
                        "Text": getattr(props, "text", None),
                    }.items()
                    if v
                },
            }
        },
    }


MANIFEST = ProviderManifest(
    type="action.aws_ses",
    name="Amazon SES",
    category="integration",
    description="Amazon SES — transactional email via SigV4.",
    icon_slug="aws-ses",
    color="#1c1c1c",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="ses",
    aws_default_region="us-east-1",
    fields=[
        FieldSpec(name="from_", label="From", type="string", placeholder="you@yourdomain.com"),
        FieldSpec(name="to", label="To (CSV)", type="string"),
        FieldSpec(name="subject", label="Subject", type="string"),
        FieldSpec(name="html", label="HTML body", type="string"),
        FieldSpec(name="text", label="Text body", type="string"),
        FieldSpec(name="template_name", label="Template Name", type="string"),
        FieldSpec(name="template_data", label="Template Data (JSON)", type="json"),
        FieldSpec(
            name="identity", label="Identity", type="string", placeholder="you@yourdomain.com"
        ),
    ],
    operations=[
        OpSpec(
            id="send_email",
            label="Send Email",
            method="POST",
            path=_SES_HOST + "/email/outbound-emails",
            visible_fields=["from_", "to", "subject", "html", "text"],
            body_builder=_send_body,
        ),
        OpSpec(
            id="send_templated",
            label="Send Templated Email",
            method="POST",
            path=_SES_HOST + "/email/outbound-emails",
            visible_fields=["from_", "to", "template_name", "template_data"],
            body_builder=lambda v: {
                "FromEmailAddress": getattr(v, "from_", None) or "",
                "Destination": {
                    "ToAddresses": [
                        a.strip() for a in str(getattr(v, "to", "") or "").split(",") if a.strip()
                    ]
                },
                "Content": {
                    "Template": {
                        "TemplateName": getattr(v, "template_name", None) or "",
                        "TemplateData": __import__("json").dumps(
                            getattr(v, "template_data", None) or {}
                        ),
                    }
                },
            },
        ),
        OpSpec(
            id="list_identities",
            label="List Email Identities",
            method="GET",
            path=_SES_HOST + "/email/identities",
        ),
        OpSpec(
            id="create_identity",
            label="Create Email Identity",
            method="POST",
            path=_SES_HOST + "/email/identities",
            visible_fields=["identity"],
            body_builder=lambda v: {"EmailIdentity": getattr(v, "identity", None) or ""},
        ),
        OpSpec(
            id="delete_identity",
            label="Delete Email Identity",
            method="DELETE",
            path=_SES_HOST + "/email/identities/{identity}",
            visible_fields=["identity"],
            success_payload_template={"deleted": True, "identity": "{identity}"},
        ),
    ],
    outputs_schema=[
        {"label": "MessageId", "type": "string"},
        {"label": "EmailIdentities", "type": "array"},
        {"label": "IdentityType", "type": "string"},
    ],
    allow_error=True,
)
