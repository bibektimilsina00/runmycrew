"""Postmark action node — manifest form.

Postmark is transactional-only — fast deliverability, simple body
shape. Auth is the custom `X-Postmark-Server-Token` header (one token
per server, not per-account), so we use the `header_token` scheme.

Three ops: send a single message, send with a template, and pull
delivery stats by message id.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.postmark import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.postmark",
    name=NAME,
    category="integration",
    description="Transactional email via Postmark — single sends, template sends, stats.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.postmarkapp.com",
    credential_type="postmark_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="X-Postmark-Server-Token",
    extra_headers={"Accept": "application/json"},
    fields=[
        FieldSpec(
            name="From",
            label="From",
            type="string",
            placeholder="you@yourdomain.com",
        ),
        FieldSpec(name="To", label="To", type="string"),
        FieldSpec(name="Subject", label="Subject", type="string"),
        FieldSpec(name="HtmlBody", label="HTML body", type="string"),
        FieldSpec(name="TextBody", label="Text body", type="string"),
        FieldSpec(name="Cc", label="CC", type="string", mode="advanced"),
        FieldSpec(name="Bcc", label="BCC", type="string", mode="advanced"),
        FieldSpec(name="ReplyTo", label="Reply-To", type="string", mode="advanced"),
        FieldSpec(name="Tag", label="Tag", type="string", mode="advanced"),
        FieldSpec(name="TemplateId", label="Template ID", type="number"),
        FieldSpec(name="TemplateAlias", label="Template Alias", type="string"),
        FieldSpec(name="TemplateModel", label="Template Model (JSON)", type="json"),
        FieldSpec(name="MessageID", label="Message ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="send_email",
            label="Send Email",
            method="POST",
            path="/email",
            visible_fields=[
                "From",
                "To",
                "Subject",
                "HtmlBody",
                "TextBody",
                "Cc",
                "Bcc",
                "ReplyTo",
                "Tag",
            ],
            body_fields=[
                "From",
                "To",
                "Subject",
                "HtmlBody",
                "TextBody",
                "Cc",
                "Bcc",
                "ReplyTo",
                "Tag",
            ],
        ),
        OpSpec(
            id="send_template",
            label="Send with Template",
            method="POST",
            path="/email/withTemplate",
            visible_fields=[
                "From",
                "To",
                "TemplateId",
                "TemplateAlias",
                "TemplateModel",
                "Cc",
                "Bcc",
                "ReplyTo",
                "Tag",
            ],
            body_fields=[
                "From",
                "To",
                "TemplateId",
                "TemplateAlias",
                "TemplateModel",
                "Cc",
                "Bcc",
                "ReplyTo",
                "Tag",
            ],
        ),
        OpSpec(
            id="get_message",
            label="Get Message Stats",
            method="GET",
            path="/messages/outbound/{MessageID}/details",
            visible_fields=["MessageID"],
        ),
    ],
    outputs_schema=[
        {"label": "MessageID", "type": "string"},
        {"label": "To", "type": "string"},
        {"label": "SubmittedAt", "type": "string"},
        {"label": "ErrorCode", "type": "number"},
        {"label": "Message", "type": "string"},
        {"label": "Status", "type": "string"},
    ],
    allow_error=True,
)
