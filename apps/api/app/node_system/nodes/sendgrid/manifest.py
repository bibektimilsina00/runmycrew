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
    color="#1c1c1c",
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
        FieldSpec(name="list_id", label="List ID", type="string"),
        FieldSpec(name="contacts", label="Contacts (JSON array)", type="json"),
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
