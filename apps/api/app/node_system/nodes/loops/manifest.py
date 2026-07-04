"""Loops action node — manifest form.

Loops.so handles product email + audience management. Three lanes:

  - Transactional sends — via a saved template id.
  - Contact upsert / lookup / delete — keyed on email.
  - Event firing — drives audience automations.

All Bearer-auth, all JSON bodies. Nothing exotic.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.loops",
    name="Loops",
    category="integration",
    description="Product email + audience automation via Loops.so.",
    icon_slug="loops",
    color="#1c1c1c",
    base_url="https://app.loops.so/api/v1",
    credential_type="loops_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="email", label="Email", type="string", placeholder="user@example.com"),
        FieldSpec(name="transactionalId", label="Template ID", type="string"),
        FieldSpec(name="dataVariables", label="Variables (JSON)", type="json"),
        FieldSpec(name="eventName", label="Event Name", type="string"),
        FieldSpec(name="eventProperties", label="Event Properties (JSON)", type="json"),
        FieldSpec(name="contactProperties", label="Contact Properties (JSON)", type="json"),
        FieldSpec(name="firstName", label="First Name", type="string", mode="advanced"),
        FieldSpec(name="lastName", label="Last Name", type="string", mode="advanced"),
        FieldSpec(
            name="mailingLists",
            label="Mailing Lists (JSON)",
            type="json",
            mode="advanced",
            description='Object mapping list id to membership boolean: {"abc123": true}',
        ),
    ],
    operations=[
        OpSpec(
            id="send_transactional",
            label="Send Transactional",
            method="POST",
            path="/transactional",
            visible_fields=["email", "transactionalId", "dataVariables"],
            body_fields=["email", "transactionalId", "dataVariables"],
        ),
        OpSpec(
            id="create_contact",
            label="Create Contact",
            method="POST",
            path="/contacts/create",
            visible_fields=[
                "email",
                "firstName",
                "lastName",
                "contactProperties",
                "mailingLists",
            ],
            body_fields=[
                "email",
                "firstName",
                "lastName",
                "contactProperties",
                "mailingLists",
            ],
        ),
        OpSpec(
            id="update_contact",
            label="Update Contact",
            method="PUT",
            path="/contacts/update",
            visible_fields=[
                "email",
                "firstName",
                "lastName",
                "contactProperties",
                "mailingLists",
            ],
            body_fields=[
                "email",
                "firstName",
                "lastName",
                "contactProperties",
                "mailingLists",
            ],
        ),
        OpSpec(
            id="find_contact",
            label="Find Contact",
            method="GET",
            path="/contacts/find",
            visible_fields=["email"],
            query_fields=["email"],
        ),
        OpSpec(
            id="delete_contact",
            label="Delete Contact",
            method="POST",
            path="/contacts/delete",
            visible_fields=["email"],
            body_fields=["email"],
            success_payload_template={"deleted": True, "email": "{email}"},
        ),
        OpSpec(
            id="send_event",
            label="Send Event",
            method="POST",
            path="/events/send",
            visible_fields=["email", "eventName", "eventProperties"],
            body_fields=["email", "eventName", "eventProperties"],
        ),
        OpSpec(
            id="list_lists",
            label="List Mailing Lists",
            method="GET",
            path="/lists",
        ),
    ],
    outputs_schema=[
        {"label": "success", "type": "boolean"},
        {"label": "id", "type": "string"},
        {"label": "email", "type": "string"},
        {"label": "lists", "type": "array"},
    ],
    allow_error=True,
)
