"""Resend action node — manifest form.

Resend is a transactional email API with a simple Bearer-auth REST
surface. Three ops cover the 95% case: send a one-shot message, send
a batch (up to 100 at once), and fetch a previously-sent email by id.

Audience + contact endpoints exist too but require workspace-level
admin scope — the user can extend this manifest if they need them.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.resend",
    name="Resend",
    category="integration",
    description="Transactional email via Resend — single sends, batch sends, and lookup.",
    icon_slug="resend",
    color="#1c1c1c",
    base_url="https://api.resend.com",
    credential_type="resend_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="email_id", label="Email ID", type="string", placeholder="re_..."),
        FieldSpec(name="from", label="From", type="string", placeholder="you@yourdomain.com"),
        FieldSpec(name="to", label="To (JSON array or string)", type="json"),
        FieldSpec(name="subject", label="Subject", type="string"),
        FieldSpec(name="html", label="HTML body", type="string"),
        FieldSpec(name="text", label="Text body", type="string"),
        FieldSpec(name="cc", label="CC (JSON array)", type="json", mode="advanced"),
        FieldSpec(name="bcc", label="BCC (JSON array)", type="json", mode="advanced"),
        FieldSpec(name="reply_to", label="Reply-To", type="string", mode="advanced"),
        FieldSpec(
            name="attachments",
            label="Attachments (JSON array)",
            type="json",
            mode="advanced",
        ),
        FieldSpec(name="tags", label="Tags (JSON array)", type="json", mode="advanced"),
        FieldSpec(name="batch", label="Emails (JSON array)", type="json"),
    ],
    operations=[
        OpSpec(
            id="send_email",
            label="Send Email",
            method="POST",
            path="/emails",
            visible_fields=[
                "from",
                "to",
                "subject",
                "html",
                "text",
                "cc",
                "bcc",
                "reply_to",
                "attachments",
                "tags",
            ],
            body_fields=[
                "from",
                "to",
                "subject",
                "html",
                "text",
                "cc",
                "bcc",
                "reply_to",
                "attachments",
                "tags",
            ],
        ),
        OpSpec(
            id="send_batch",
            label="Send Batch",
            method="POST",
            path="/emails/batch",
            visible_fields=["batch"],
            body_builder=lambda props: getattr(props, "batch", None) or [],
        ),
        OpSpec(
            id="get_email",
            label="Get Email",
            method="GET",
            path="/emails/{email_id}",
            visible_fields=["email_id"],
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "from", "type": "string"},
        {"label": "to", "type": "array"},
        {"label": "subject", "type": "string"},
        {"label": "created_at", "type": "string"},
        {"label": "last_event", "type": "string"},
        {"label": "data", "type": "array"},
    ],
    allow_error=True,
)
