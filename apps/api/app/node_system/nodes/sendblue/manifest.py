"""Sendblue action node — manifest form.

Sendblue (iMessage / SMS over the green-bubble fallback) ships two
custom headers: `sb-api-key-id` and `sb-api-secret-key`. Both ride
extra_headers with the new credential-field substitution — same trick
used for Supabase's dual `Authorization`+`apikey` headers.

Ops: send message, retrieve a message, list messages.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.sendblue",
    name="Sendblue",
    category="integration",
    description="Sendblue — iMessage + SMS fallback messaging API.",
    icon_slug="sendblue",
    color="#ffffff",
    base_url="https://api.sendblue.co/api",
    credential_type="sendblue_api_key",
    # Sendblue's API key ID rides one header, the secret rides another.
    # We pick api_secret_key as the "token" for traceability; both ship
    # via extra_headers below.
    token_field=["api_secret_key"],
    auth="none",
    extra_headers={
        "sb-api-key-id": "{api_key_id}",
        "sb-api-secret-key": "{api_secret_key}",
    },
    fields=[
        FieldSpec(name="number", label="To (phone)", type="string", placeholder="+15551234567"),
        FieldSpec(name="content", label="Message content", type="string"),
        FieldSpec(name="media_url", label="Media URL", type="string", mode="advanced"),
        FieldSpec(name="status_callback", label="Status callback", type="string", mode="advanced"),
        FieldSpec(name="send_style", label="Send style", type="string", mode="advanced"),
        FieldSpec(name="message_id", label="Message ID", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/send-message",
            visible_fields=["number", "content", "media_url", "status_callback", "send_style"],
            body_fields=["number", "content", "media_url", "status_callback", "send_style"],
        ),
        OpSpec(
            id="get_message",
            label="Get Message",
            method="GET",
            path="/messages/{message_id}",
            visible_fields=["message_id"],
        ),
        OpSpec(
            id="list_messages",
            label="List Messages",
            method="GET",
            path="/messages",
            visible_fields=["limit"],
            query_fields=["limit"],
        ),
    ],
    outputs_schema=[
        {"label": "message_id", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "from_number", "type": "string"},
        {"label": "number", "type": "string"},
        {"label": "content", "type": "string"},
        {"label": "messages", "type": "array"},
    ],
    allow_error=True,
)
