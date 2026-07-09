"""SendGrid action node — manifest form.

SendGrid's email-send body is verbose — Personalizations + From +
Content arrays nested under `personalizations`. We expose a compact
prop schema (to, from, subject, html, text) and a body_builder folds
those into SendGrid's required envelope.

Contact and list ops are simpler — straight POST/GET with body_fields.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)


def _send_body(props: Any) -> dict[str, Any]:
    """Project the flat prop schema into SendGrid's mail/send envelope."""
    to_raw = getattr(props, "to", None) or []
    if isinstance(to_raw, str):
        to_raw = [to_raw]
    to_list = [{"email": t} if isinstance(t, str) else t for t in to_raw]

    content: list[dict[str, str]] = []
    text_body = getattr(props, "text", None)
    html_body = getattr(props, "html", None)
    if text_body:
        content.append({"type": "text/plain", "value": text_body})
    if html_body:
        content.append({"type": "text/html", "value": html_body})

    body: dict[str, Any] = {
        "personalizations": [{"to": to_list, "subject": getattr(props, "subject", None) or ""}],
        "from": {"email": getattr(props, "from_", None) or getattr(props, "from", None) or ""},
        "content": content or [{"type": "text/plain", "value": ""}],
    }
    return body


MANIFEST = ProviderManifest(
    type="action.sendgrid",
    name="SendGrid",
    category="integration",
    description="Transactional + marketing email via SendGrid — send, contacts, lists.",
    icon_slug="sendgrid",
    color="#ffffff",
    base_url="https://api.sendgrid.com/v3",
    credential_type="sendgrid_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        # `from_` because `from` is a Python keyword and Pydantic
        # synthesizes attributes via the field name.
        FieldSpec(name="from_", label="From", type="string", placeholder="you@yourdomain.com"),
        FieldSpec(name="to", label="To (JSON array of emails or strings)", type="json"),
        FieldSpec(name="subject", label="Subject", type="string"),
        FieldSpec(name="html", label="HTML body", type="string"),
        FieldSpec(name="text", label="Text body", type="string"),
        FieldSpec(name="contact_email", label="Contact email", type="string"),
        FieldSpec(
            name="list_id",
            label="List",
            type="string",
            remote=RemoteLookup(provider="sendgrid", resource="lists"),
        ),
        FieldSpec(name="contacts", label="Contacts (JSON array)", type="json"),
        FieldSpec(name="mail_body", label="Mail Body (JSON)", type="json", default={}),
        FieldSpec(name="contact_body", label="Contact Body (JSON)", type="json", default={}),
        FieldSpec(name="contact_ids", label="Contact IDs (JSON array)", type="json", default=[]),
        FieldSpec(name="list_name", label="List Name", type="string"),
        FieldSpec(name="template_name", label="Template Name", type="string"),
        FieldSpec(
            name="template_id",
            label="Template",
            type="string",
            remote=RemoteLookup(provider="sendgrid", resource="templates"),
        ),
        FieldSpec(
            name="template_version_body",
            label="Template Version Body (JSON)",
            type="json",
            default={},
        ),
        FieldSpec(name="query_text", label="Query", type="string"),
    ],
    operations=[
        OpSpec(
            id="send_email",
            label="Send Email",
            method="POST",
            path="/mail/send",
            visible_fields=["from_", "to", "subject", "html", "text"],
            body_builder=_send_body,
        ),
        OpSpec(
            id="add_contacts",
            label="Add / Update Contacts",
            method="PUT",
            path="/marketing/contacts",
            visible_fields=["contacts"],
            body_fields=["contacts"],
        ),
        OpSpec(
            id="list_lists",
            label="List Lists",
            method="GET",
            path="/marketing/lists",
        ),
        OpSpec(
            id="get_list",
            label="Get List",
            method="GET",
            path="/marketing/lists/{list_id}",
            visible_fields=["list_id"],
        ),
        OpSpec(
            id="search_contact",
            label="Search Contact by Email",
            method="POST",
            path="/marketing/contacts/search/emails",
            visible_fields=["contact_email"],
            body_template={"emails": ["{contact_email}"]},
        ),
        OpSpec(
            id="send_mail",
            label="Send Mail (v3)",
            method="POST",
            path="/v3/mail/send",
            visible_fields=["mail_body"],
            body_builder=lambda v: getattr(v, "mail_body", None) or {},
        ),
        OpSpec(
            id="add_contact",
            label="Add / Upsert Contact",
            method="PUT",
            path="/v3/marketing/contacts",
            visible_fields=["contact_body"],
            body_builder=lambda v: getattr(v, "contact_body", None) or {},
        ),
        OpSpec(
            id="get_contact",
            label="Get Contact",
            method="GET",
            path="/v3/marketing/contacts/{contact_id}",
            visible_fields=["contact_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="search_contacts",
            label="Search Contacts (SGQL)",
            method="POST",
            path="/v3/marketing/contacts/search",
            visible_fields=["query_text"],
            body_builder=lambda v: {"query": getattr(v, "query_text", "") or ""},
        ),
        OpSpec(
            id="delete_contacts",
            label="Delete Contacts",
            method="DELETE",
            path="/v3/marketing/contacts",
            visible_fields=["contact_ids"],
            query_builder=lambda v: {"ids": ",".join(getattr(v, "contact_ids", []) or [])},
        ),
        OpSpec(
            id="create_list",
            label="Create List",
            method="POST",
            path="/v3/marketing/lists",
            visible_fields=["list_name"],
            body_builder=lambda v: {"name": getattr(v, "list_name", "") or ""},
        ),
        OpSpec(
            id="list_all_lists",
            label="List All Lists",
            method="GET",
            path="/v3/marketing/lists",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="delete_list",
            label="Delete List",
            method="DELETE",
            path="/v3/marketing/lists/{list_id}",
            visible_fields=["list_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="add_contacts_to_list",
            label="Add Contacts to List",
            method="POST",
            path="/v3/marketing/lists/{list_id}",
            visible_fields=["list_id", "contact_ids"],
            body_builder=lambda v: {"contact_ids": getattr(v, "contact_ids", []) or []},
        ),
        OpSpec(
            id="remove_contacts_from_list",
            label="Remove Contacts from List",
            method="DELETE",
            path="/v3/marketing/lists/{list_id}/contacts",
            visible_fields=["list_id", "contact_ids"],
            query_builder=lambda v: {"contact_ids": ",".join(getattr(v, "contact_ids", []) or [])},
        ),
        OpSpec(
            id="create_template",
            label="Create Template",
            method="POST",
            path="/v3/templates",
            visible_fields=["template_name"],
            body_builder=lambda v: {
                "name": getattr(v, "template_name", "") or "",
                "generation": "dynamic",
            },
        ),
        OpSpec(
            id="get_template",
            label="Get Template",
            method="GET",
            path="/v3/templates/{template_id}",
            visible_fields=["template_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_templates",
            label="List Templates",
            method="GET",
            path="/v3/templates",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="delete_template",
            label="Delete Template",
            method="DELETE",
            path="/v3/templates/{template_id}",
            visible_fields=["template_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_template_version",
            label="Create Template Version",
            method="POST",
            path="/v3/templates/{template_id}/versions",
            visible_fields=["template_id", "template_version_body"],
            body_builder=lambda v: getattr(v, "template_version_body", None) or {},
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "result", "type": "array"},
        {"label": "lists", "type": "array"},
        {"label": "contact_count", "type": "number"},
        {"label": "job_id", "type": "string"},
    ],
    allow_error=True,
)
