"""MessageBird action node — manifest form.

MessageBird (Bird) uses a custom `Authorization: AccessKey <key>`
header — straightforward bearer-style variant, handled via the
`bearer` scheme with a custom value template.

Three ops: send SMS, lookup balance, list messages.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.messagebird",
    name="MessageBird",
    category="integration",
    description="MessageBird — SMS, voice, and verification.",
    icon_slug="messagebird",
    color="#1c1c1c",
    base_url="https://rest.messagebird.com",
    credential_type="messagebird_api_key",
    token_field=["api_key"],
    auth="bearer",
    auth_value_template="AccessKey {token}",
    fields=[
        FieldSpec(name="originator", label="From", type="string", placeholder="MyApp or +15551234"),
        FieldSpec(
            name="recipients", label="Recipients (CSV)", type="string", placeholder="+15557654321"
        ),
        FieldSpec(name="body", label="Body", type="string"),
        FieldSpec(
            name="type",
            label="Type",
            type="options",
            default="sms",
            mode="advanced",
            options=[
                {"label": "SMS", "value": "sms"},
                {"label": "Voice", "value": "voice"},
            ],
        ),
        FieldSpec(name="message_id", label="Message ID", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=30, mode="advanced"),
        FieldSpec(name="offset", label="Offset", type="number", default=0, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/messages",
            visible_fields=["originator", "recipients", "body", "type"],
            body_builder=lambda v: {
                "originator": getattr(v, "originator", None),
                "recipients": [
                    r.strip() for r in (getattr(v, "recipients", "") or "").split(",") if r.strip()
                ],
                "body": getattr(v, "body", None),
                "type": getattr(v, "type", None) or "sms",
            },
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
            visible_fields=["limit", "offset"],
            query_fields=["limit", "offset"],
        ),
        OpSpec(
            id="get_balance",
            label="Get Balance",
            method="GET",
            path="/balance",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "recipients", "type": "object"},
        {"label": "items", "type": "array"},
        {"label": "amount", "type": "number"},
        {"label": "type", "type": "string"},
    ],
    allow_error=True,
)
