"""Twilio action node — manifest form.

Twilio's REST API uses Basic auth where the username is the
`account_sid` and the password is the `auth_token`. The scaffold's
`auth_basic_username="{account_sid}"` resolves the username from the
credential dict so the user only sees one credential row.

Bodies are `application/x-www-form-urlencoded` (legacy, not JSON).
Scaffold's content_type override routes the body through httpx's
`data=` argument.

Covers messaging + voice in one node — Twilio's account model treats
them as the same resource tree.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.twilio",
    name="Twilio",
    category="integration",
    description="Twilio — send SMS / WhatsApp messages and place voice calls.",
    icon_slug="twilio",
    color="#1c1c1c",
    base_url="https://api.twilio.com/2010-04-01",
    credential_type="twilio_api_key",
    token_field=["auth_token"],
    auth="basic",
    auth_basic_username="{account_sid}",
    content_type="application/x-www-form-urlencoded",
    fields=[
        FieldSpec(
            name="From", label="From", type="string", placeholder="+15551234567 or whatsapp:+1..."
        ),
        FieldSpec(name="To", label="To", type="string", placeholder="+15557654321"),
        FieldSpec(name="Body", label="Body", type="string", placeholder="Message text"),
        FieldSpec(name="MediaUrl", label="Media URL", type="string", mode="advanced"),
        FieldSpec(
            name="StatusCallback", label="Status callback URL", type="string", mode="advanced"
        ),
        FieldSpec(name="Url", label="TwiML URL", type="string"),
        FieldSpec(
            name="message_sid",
            label="Message SID",
            type="string",
            placeholder="SM...",
        ),
        FieldSpec(name="call_sid", label="Call SID", type="string", placeholder="CA..."),
        FieldSpec(name="limit", label="Limit", type="number", default=20, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/Accounts/{account_sid}/Messages.json",
            visible_fields=["From", "To", "Body", "MediaUrl", "StatusCallback"],
            body_fields=["From", "To", "Body", "MediaUrl", "StatusCallback"],
        ),
        OpSpec(
            id="get_message",
            label="Get Message",
            method="GET",
            path="/Accounts/{account_sid}/Messages/{message_sid}.json",
            visible_fields=["message_sid"],
        ),
        OpSpec(
            id="list_messages",
            label="List Messages",
            method="GET",
            path="/Accounts/{account_sid}/Messages.json",
            visible_fields=["limit"],
            query_builder=lambda v: {"PageSize": int(getattr(v, "limit", 20) or 20)},
        ),
        OpSpec(
            id="make_call",
            label="Make Call",
            method="POST",
            path="/Accounts/{account_sid}/Calls.json",
            visible_fields=["From", "To", "Url", "StatusCallback"],
            body_fields=["From", "To", "Url", "StatusCallback"],
        ),
        OpSpec(
            id="get_call",
            label="Get Call",
            method="GET",
            path="/Accounts/{account_sid}/Calls/{call_sid}.json",
            visible_fields=["call_sid"],
        ),
        OpSpec(
            id="list_calls",
            label="List Calls",
            method="GET",
            path="/Accounts/{account_sid}/Calls.json",
            visible_fields=["limit"],
            query_builder=lambda v: {"PageSize": int(getattr(v, "limit", 20) or 20)},
        ),
    ],
    outputs_schema=[
        {"label": "sid", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "from", "type": "string"},
        {"label": "to", "type": "string"},
        {"label": "body", "type": "string"},
        {"label": "messages", "type": "array"},
        {"label": "calls", "type": "array"},
        {"label": "date_created", "type": "string"},
    ],
    allow_error=True,
)
