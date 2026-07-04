"""Zendesk action node — manifest form.

Zendesk Support API at `https://{subdomain}.zendesk.com/api/v2`.
Basic auth using `{email}/token:{api_key}` — Zendesk's token
auth convention. We use auth_basic_username="{email}/token" to
resolve the email from the credential and append `/token`.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://{subdomain}.zendesk.com/api/v2"


MANIFEST = ProviderManifest(
    type="action.zendesk",
    name="Zendesk",
    category="integration",
    description="Zendesk Support — tickets, users, organizations.",
    icon_slug="zendesk",
    color="#1c1c1c",
    base_url="",
    credential_type="zendesk_api_key",
    token_field=["api_key"],
    auth="basic",
    # Zendesk uses `{email}/token:{token}` — the `/token` suffix tells
    # Zendesk to auth as an API token rather than a password.
    auth_basic_username="{email}/token",
    fields=[
        FieldSpec(name="ticket_id", label="Ticket ID", type="number"),
        FieldSpec(name="user_id", label="User ID", type="number"),
        FieldSpec(name="org_id", label="Organization ID", type="number"),
        FieldSpec(name="subject", label="Ticket Subject", type="string"),
        FieldSpec(name="comment", label="Ticket Comment (body)", type="string"),
        FieldSpec(
            name="priority",
            label="Priority",
            type="options",
            mode="advanced",
            options=[
                {"label": "Urgent", "value": "urgent"},
                {"label": "High", "value": "high"},
                {"label": "Normal", "value": "normal"},
                {"label": "Low", "value": "low"},
            ],
        ),
        FieldSpec(
            name="status",
            label="Ticket Status",
            type="options",
            mode="advanced",
            options=[
                {"label": "New", "value": "new"},
                {"label": "Open", "value": "open"},
                {"label": "Pending", "value": "pending"},
                {"label": "Hold", "value": "hold"},
                {"label": "Solved", "value": "solved"},
                {"label": "Closed", "value": "closed"},
            ],
        ),
        FieldSpec(name="requester_email", label="Requester Email", type="string"),
        FieldSpec(name="user_name", label="User Name", type="string"),
        FieldSpec(name="user_email", label="User Email", type="string"),
        FieldSpec(name="query", label="Search Query", type="string"),
        FieldSpec(name="per_page", label="Per Page", type="number", default=100, mode="advanced"),
        FieldSpec(name="page", label="Page", type="number", default=1, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_tickets",
            label="List Tickets",
            method="GET",
            path=_HOST + "/tickets.json",
            visible_fields=["per_page", "page"],
            query_fields=["per_page", "page"],
        ),
        OpSpec(
            id="get_ticket",
            label="Get Ticket",
            method="GET",
            path=_HOST + "/tickets/{ticket_id}.json",
            visible_fields=["ticket_id"],
        ),
        OpSpec(
            id="create_ticket",
            label="Create Ticket",
            method="POST",
            path=_HOST + "/tickets.json",
            visible_fields=["subject", "comment", "priority", "requester_email"],
            body_builder=lambda v: {
                "ticket": {
                    k: val
                    for k, val in {
                        "subject": getattr(v, "subject", None),
                        "comment": {"body": getattr(v, "comment", None) or ""},
                        "priority": getattr(v, "priority", None),
                        "requester": (
                            {"email": v.requester_email}
                            if getattr(v, "requester_email", None)
                            else None
                        ),
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="update_ticket",
            label="Update Ticket",
            method="PUT",
            path=_HOST + "/tickets/{ticket_id}.json",
            visible_fields=["ticket_id", "status", "priority", "comment"],
            body_builder=lambda v: {
                "ticket": {
                    k: val
                    for k, val in {
                        "status": getattr(v, "status", None),
                        "priority": getattr(v, "priority", None),
                        "comment": (
                            {"body": v.comment, "public": True}
                            if getattr(v, "comment", None)
                            else None
                        ),
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="delete_ticket",
            label="Delete Ticket",
            method="DELETE",
            path=_HOST + "/tickets/{ticket_id}.json",
            visible_fields=["ticket_id"],
            success_payload_template={"deleted": True, "ticket_id": "{ticket_id}"},
        ),
        OpSpec(
            id="search",
            label="Search",
            method="GET",
            path=_HOST + "/search.json",
            visible_fields=["query", "per_page"],
            query_builder=lambda v: {
                "query": getattr(v, "query", None) or "",
                "per_page": int(getattr(v, "per_page", 100) or 100),
            },
        ),
        OpSpec(
            id="list_users",
            label="List Users",
            method="GET",
            path=_HOST + "/users.json",
            visible_fields=["per_page", "page"],
            query_fields=["per_page", "page"],
        ),
        OpSpec(
            id="get_user",
            label="Get User",
            method="GET",
            path=_HOST + "/users/{user_id}.json",
            visible_fields=["user_id"],
        ),
        OpSpec(
            id="create_user",
            label="Create User",
            method="POST",
            path=_HOST + "/users.json",
            visible_fields=["user_name", "user_email"],
            body_builder=lambda v: {
                "user": {
                    "name": getattr(v, "user_name", None) or "",
                    "email": getattr(v, "user_email", None) or "",
                }
            },
        ),
        OpSpec(
            id="list_organizations",
            label="List Organizations",
            method="GET",
            path=_HOST + "/organizations.json",
            visible_fields=["per_page", "page"],
            query_fields=["per_page", "page"],
        ),
        OpSpec(
            id="get_organization",
            label="Get Organization",
            method="GET",
            path=_HOST + "/organizations/{org_id}.json",
            visible_fields=["org_id"],
        ),
    ],
    outputs_schema=[
        {"label": "ticket", "type": "object"},
        {"label": "tickets", "type": "array"},
        {"label": "user", "type": "object"},
        {"label": "users", "type": "array"},
        {"label": "organization", "type": "object"},
        {"label": "results", "type": "array"},
        {"label": "count", "type": "number"},
        {"label": "next_page", "type": "string"},
    ],
    allow_error=True,
)
