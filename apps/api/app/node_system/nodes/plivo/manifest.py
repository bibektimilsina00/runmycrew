"""Plivo action node — manifest form.

Plivo's REST API mirrors Twilio's shape — Basic auth with the
`auth_id` as username and `auth_token` as password. Accounts live
under `/v1/Account/{auth_id}/...`. Reuses the scaffold's
`auth_basic_username="{auth_id}"` resolution.

Bodies are JSON (unlike Twilio's form-encoded), so we leave
content_type at the JSON default.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.plivo",
    name="Plivo",
    category="integration",
    description="Plivo — SMS and voice (Twilio alternative).",
    icon_slug="plivo",
    color="#1c1c1c",
    base_url="https://api.plivo.com",
    credential_type="plivo_api_key",
    token_field=["auth_token"],
    auth="basic",
    auth_basic_username="{auth_id}",
    fields=[
        FieldSpec(name="src", label="From", type="string"),
        FieldSpec(name="dst", label="To", type="string", placeholder="+15551234567"),
        FieldSpec(name="text", label="Message text", type="string"),
        FieldSpec(name="url", label="TwiML/Answer URL", type="string"),
        FieldSpec(name="from_number", label="From (voice)", type="string"),
        FieldSpec(name="to_number", label="To (voice)", type="string"),
        FieldSpec(name="message_uuid", label="Message UUID", type="string"),
        FieldSpec(name="call_uuid", label="Call UUID", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=20, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/v1/Account/{auth_id}/Message/",
            visible_fields=["src", "dst", "text"],
            body_fields=["src", "dst", "text"],
        ),
        OpSpec(
            id="get_message",
            label="Get Message",
            method="GET",
            path="/v1/Account/{auth_id}/Message/{message_uuid}/",
            visible_fields=["message_uuid"],
        ),
        OpSpec(
            id="list_messages",
            label="List Messages",
            method="GET",
            path="/v1/Account/{auth_id}/Message/",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 20) or 20)},
        ),
        OpSpec(
            id="make_call",
            label="Make Call",
            method="POST",
            path="/v1/Account/{auth_id}/Call/",
            visible_fields=["from_number", "to_number", "url"],
            body_builder=lambda v: {
                "from": getattr(v, "from_number", None),
                "to": getattr(v, "to_number", None),
                "answer_url": getattr(v, "url", None),
            },
        ),
        OpSpec(
            id="get_call",
            label="Get Call",
            method="GET",
            path="/v1/Account/{auth_id}/Call/{call_uuid}/",
            visible_fields=["call_uuid"],
        ),
    ],
    outputs_schema=[
        {"label": "message_uuid", "type": "array"},
        {"label": "api_id", "type": "string"},
        {"label": "message", "type": "string"},
        {"label": "objects", "type": "array"},
        {"label": "from", "type": "string"},
        {"label": "to", "type": "string"},
    ],
    allow_error=True,
)
