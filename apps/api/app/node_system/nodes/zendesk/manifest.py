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
        FieldSpec(name="zendesk_ticket_id", label="Ticket ID", type="string"),
        FieldSpec(name="tickets_body", label="Tickets (JSON array)", type="json", default=[]),
        FieldSpec(
            name="target_ticket_ids", label="Target Ticket IDs (JSON)", type="json", default=[]
        ),
        FieldSpec(name="zendesk_user_id", label="User ID", type="string"),
        FieldSpec(name="zendesk_user_query", label="User Search Query", type="string"),
        FieldSpec(name="users_body", label="Users (JSON array)", type="json", default=[]),
        FieldSpec(name="organization_id", label="Organization ID", type="string"),
        FieldSpec(name="organization_name", label="Organization Name", type="string"),
        FieldSpec(
            name="organization_body", label="Organization Body (JSON)", type="json", default={}
        ),
        FieldSpec(name="orgs_body", label="Organizations (JSON array)", type="json", default=[]),
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
        OpSpec(
            id="get_tickets",
            label="List Tickets",
            method="GET",
            path="/tickets.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_tickets_bulk",
            label="Create Tickets (bulk)",
            method="POST",
            path="/tickets/create_many.json",
            visible_fields=["tickets_body"],
            body_builder=lambda v: {"tickets": getattr(v, "tickets_body", []) or []},
        ),
        OpSpec(
            id="update_tickets_bulk",
            label="Update Tickets (bulk)",
            method="PUT",
            path="/tickets/update_many.json",
            visible_fields=["tickets_body"],
            body_builder=lambda v: {"tickets": getattr(v, "tickets_body", []) or []},
        ),
        OpSpec(
            id="merge_tickets",
            label="Merge Tickets",
            method="POST",
            path="/tickets/{zendesk_ticket_id}/merge.json",
            visible_fields=["zendesk_ticket_id", "target_ticket_ids"],
            body_builder=lambda v: {"ids": getattr(v, "target_ticket_ids", []) or []},
        ),
        OpSpec(
            id="get_users",
            label="List Users",
            method="GET",
            path="/users.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_current_user",
            label="Get Current User",
            method="GET",
            path="/users/me.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="search_users",
            label="Search Users",
            method="GET",
            path="/users/search.json",
            visible_fields=["zendesk_user_query"],
            query_builder=lambda v: {"query": getattr(v, "zendesk_user_query", "") or ""},
        ),
        OpSpec(
            id="create_users_bulk",
            label="Create Users (bulk)",
            method="POST",
            path="/users/create_many.json",
            visible_fields=["users_body"],
            body_builder=lambda v: {"users": getattr(v, "users_body", []) or []},
        ),
        OpSpec(
            id="update_users_bulk",
            label="Update Users (bulk)",
            method="PUT",
            path="/users/update_many.json",
            visible_fields=["users_body"],
            body_builder=lambda v: {"users": getattr(v, "users_body", []) or []},
        ),
        OpSpec(
            id="delete_user",
            label="Delete User",
            method="DELETE",
            path="/users/{zendesk_user_id}.json",
            visible_fields=["zendesk_user_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_organizations",
            label="List Organizations",
            method="GET",
            path="/organizations.json",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="autocomplete_organizations",
            label="Autocomplete Organizations",
            method="GET",
            path="/organizations/autocomplete.json",
            visible_fields=["organization_name"],
            query_builder=lambda v: {"name": getattr(v, "organization_name", "") or ""},
        ),
        OpSpec(
            id="create_organization",
            label="Create Organization",
            method="POST",
            path="/organizations.json",
            visible_fields=["organization_body"],
            body_builder=lambda v: {"organization": getattr(v, "organization_body", None) or {}},
        ),
        OpSpec(
            id="create_organizations_bulk",
            label="Create Organizations (bulk)",
            method="POST",
            path="/organizations/create_many.json",
            visible_fields=["orgs_body"],
            body_builder=lambda v: {"organizations": getattr(v, "orgs_body", []) or []},
        ),
        OpSpec(
            id="update_organization",
            label="Update Organization",
            method="PUT",
            path="/organizations/{organization_id}.json",
            visible_fields=["organization_id", "organization_body"],
            body_builder=lambda v: {"organization": getattr(v, "organization_body", None) or {}},
        ),
        OpSpec(
            id="delete_organization",
            label="Delete Organization",
            method="DELETE",
            path="/organizations/{organization_id}.json",
            visible_fields=["organization_id"],
            query_builder=lambda v: {},
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
