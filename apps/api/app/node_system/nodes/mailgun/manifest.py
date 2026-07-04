"""Mailgun action node — manifest form.

Mailgun uses Basic auth with the literal username `api` and the
domain-scoped key as password. Body is form-encoded. Per-domain
sending lives at `/v3/{domain}/messages`.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.mailgun",
    name="Mailgun",
    category="integration",
    description="Mailgun — transactional + marketing email.",
    icon_slug="mailgun",
    color="#1c1c1c",
    base_url="https://api.mailgun.net/v3",
    credential_type="mailgun_api_key",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="api",
    content_type="application/x-www-form-urlencoded",
    fields=[
        FieldSpec(
            name="domain",
            label="Domain",
            type="string",
            required=True,
            placeholder="mg.example.com",
        ),
        FieldSpec(name="from_", label="From", type="string", placeholder='"You" <you@example.com>'),
        FieldSpec(name="to", label="To", type="string"),
        FieldSpec(name="cc", label="CC", type="string", mode="advanced"),
        FieldSpec(name="bcc", label="BCC", type="string", mode="advanced"),
        FieldSpec(name="subject", label="Subject", type="string"),
        FieldSpec(name="text", label="Text body", type="string"),
        FieldSpec(name="html", label="HTML body", type="string"),
        FieldSpec(name="template", label="Template", type="string", mode="advanced"),
        FieldSpec(
            name="template_variables",
            label="Template variables (JSON)",
            type="json",
            mode="advanced",
        ),
        FieldSpec(name="address", label="Email address", type="string"),
        FieldSpec(name="list_address", label="Mailing list", type="string"),
    ],
    operations=[
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/{domain}/messages",
            visible_fields=["domain", "from_", "to", "cc", "bcc", "subject", "text", "html"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "from": getattr(v, "from_", None),
                    "to": getattr(v, "to", None),
                    "cc": getattr(v, "cc", None),
                    "bcc": getattr(v, "bcc", None),
                    "subject": getattr(v, "subject", None),
                    "text": getattr(v, "text", None),
                    "html": getattr(v, "html", None),
                }.items()
                if val not in (None, "")
            },
        ),
        OpSpec(
            id="send_template",
            label="Send via Template",
            method="POST",
            path="/{domain}/messages",
            visible_fields=["domain", "from_", "to", "subject", "template", "template_variables"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "from": getattr(v, "from_", None),
                    "to": getattr(v, "to", None),
                    "subject": getattr(v, "subject", None),
                    "template": getattr(v, "template", None),
                    "h:X-Mailgun-Variables": __import__("json").dumps(
                        getattr(v, "template_variables", None) or {}
                    ),
                }.items()
                if val not in (None, "")
            },
        ),
        OpSpec(
            id="validate_email",
            label="Validate Email",
            method="GET",
            path="/address/validate",
            visible_fields=["address"],
            query_fields=["address"],
        ),
        OpSpec(
            id="list_mailing_lists",
            label="List Mailing Lists",
            method="GET",
            path="/lists/pages",
        ),
        OpSpec(
            id="get_list",
            label="Get Mailing List",
            method="GET",
            path="/lists/{list_address}",
            visible_fields=["list_address"],
        ),
        OpSpec(
            id="add_list_member",
            label="Add List Member",
            method="POST",
            path="/lists/{list_address}/members",
            visible_fields=["list_address", "address"],
            body_builder=lambda v: {"address": getattr(v, "address", None), "subscribed": "yes"},
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "message", "type": "string"},
        {"label": "items", "type": "array"},
        {"label": "is_valid", "type": "boolean"},
        {"label": "result", "type": "string"},
    ],
    allow_error=True,
)
