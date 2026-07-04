"""Intercom action node — manifest form.

Intercom v2 REST API. Bearer auth + a pinned `Intercom-Version`
header (we default to `2.13`). Eight ops cover the typical workflow
use: contacts CRUD, message send, conversation reply, segment list.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.intercom",
    name="Intercom",
    category="integration",
    description="Intercom — manage contacts, conversations, and messages.",
    icon_slug="intercom",
    color="#1c1c1c",
    base_url="https://api.intercom.io",
    credential_type="intercom_api_key",
    token_field=["api_key"],
    auth="bearer",
    extra_headers={"Intercom-Version": "2.13"},
    fields=[
        FieldSpec(name="contact_id", label="Contact ID", type="string"),
        FieldSpec(name="external_id", label="External ID", type="string", mode="advanced"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="phone", label="Phone", type="string", mode="advanced"),
        FieldSpec(
            name="role",
            label="Role",
            type="options",
            mode="advanced",
            options=[
                {"label": "User", "value": "user"},
                {"label": "Lead", "value": "lead"},
            ],
        ),
        FieldSpec(
            name="custom_attributes", label="Custom Attributes (JSON)", type="json", mode="advanced"
        ),
        FieldSpec(name="conversation_id", label="Conversation ID", type="string"),
        FieldSpec(
            name="message_type",
            label="Message Type",
            type="options",
            default="comment",
            options=[
                {"label": "Comment", "value": "comment"},
                {"label": "Note", "value": "note"},
            ],
        ),
        FieldSpec(name="body", label="Body", type="string"),
        FieldSpec(name="admin_id", label="Admin ID (sender)", type="string"),
        FieldSpec(name="from_email", label="From email", type="string", mode="advanced"),
        FieldSpec(name="subject", label="Subject", type="string", mode="advanced"),
        FieldSpec(name="query", label="Search Query (JSON)", type="json", mode="advanced"),
        FieldSpec(name="limit", label="Per page", type="number", default=50, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="create_contact",
            label="Create Contact",
            method="POST",
            path="/contacts",
            visible_fields=["role", "email", "name", "external_id", "phone", "custom_attributes"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "role": getattr(v, "role", None) or "user",
                    "email": getattr(v, "email", None),
                    "name": getattr(v, "name", None),
                    "external_id": getattr(v, "external_id", None),
                    "phone": getattr(v, "phone", None),
                    "custom_attributes": getattr(v, "custom_attributes", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="get_contact",
            label="Get Contact",
            method="GET",
            path="/contacts/{contact_id}",
            visible_fields=["contact_id"],
        ),
        OpSpec(
            id="update_contact",
            label="Update Contact",
            method="PUT",
            path="/contacts/{contact_id}",
            visible_fields=["contact_id", "email", "name", "phone", "custom_attributes"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "email": getattr(v, "email", None),
                    "name": getattr(v, "name", None),
                    "phone": getattr(v, "phone", None),
                    "custom_attributes": getattr(v, "custom_attributes", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="search_contacts",
            label="Search Contacts",
            method="POST",
            path="/contacts/search",
            visible_fields=["query"],
            body_builder=lambda v: {"query": getattr(v, "query", None) or {}},
        ),
        OpSpec(
            id="list_contacts",
            label="List Contacts",
            method="GET",
            path="/contacts",
            visible_fields=["limit"],
            query_builder=lambda v: {"per_page": int(getattr(v, "limit", 50) or 50)},
        ),
        OpSpec(
            id="send_message",
            label="Send Message",
            method="POST",
            path="/messages",
            visible_fields=["from_email", "subject", "body", "email", "admin_id"],
            body_builder=lambda v: {
                "message_type": "email",
                "subject": getattr(v, "subject", None) or "",
                "body": getattr(v, "body", None) or "",
                "from": {"type": "admin", "id": getattr(v, "admin_id", None)},
                "to": {"type": "user", "email": getattr(v, "email", None)},
            },
        ),
        OpSpec(
            id="reply_conversation",
            label="Reply to Conversation",
            method="POST",
            path="/conversations/{conversation_id}/reply",
            visible_fields=["conversation_id", "message_type", "body", "admin_id"],
            body_builder=lambda v: {
                "message_type": getattr(v, "message_type", None) or "comment",
                "type": "admin",
                "admin_id": getattr(v, "admin_id", None),
                "body": getattr(v, "body", None) or "",
            },
        ),
        OpSpec(
            id="list_segments",
            label="List Segments",
            method="GET",
            path="/segments",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "type", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "data", "type": "array"},
        {"label": "segments", "type": "array"},
        {"label": "total_count", "type": "number"},
    ],
    allow_error=True,
)
