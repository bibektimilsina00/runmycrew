"""Wealthbox action node — Wealthbox — CRM for financial advisors.

REST at https://api.crmworkspace.com/v1. See sim-parity roadmap Phase 4.24.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.wealthbox",
    name="Wealthbox",
    category="integration",
    description="Wealthbox — CRM for financial advisors.",
    icon_slug="wealthbox",
    color="#1c1c1c",
    base_url="https://api.crmworkspace.com/v1",
    credential_type="wealthbox_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="ACCESS_TOKEN",
    fields=[
        FieldSpec(name="employee_id", label="Employee ID", type="string"),
        FieldSpec(name="worker_id", label="Worker ID", type="string"),
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="contact_id", label="Contact ID", type="string"),
        FieldSpec(name="tenant", label="Tenant", type="string"),
        FieldSpec(name="raas_url", label="RaaS Report URL", type="string"),
        FieldSpec(name="report_id", label="Report ID", type="string"),
        FieldSpec(name="expense_id", label="Expense ID", type="string"),
        FieldSpec(name="first_name", label="First Name", type="string"),
        FieldSpec(name="last_name", label="Last Name", type="string"),
        FieldSpec(name="email", label="Email", type="string"),
        FieldSpec(name="content", label="Content", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(name="offset", label="Offset", type="number", default=0, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_contacts",
            label="List Contacts",
            method="GET",
            path="/contacts",
            visible_fields=["limit"],
            query_builder=lambda v: {"per_page": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="get_contact",
            label="Get Contact",
            method="GET",
            path="/contacts/{contact_id}",
            visible_fields=["contact_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_contact",
            label="Create Contact",
            method="POST",
            path="/contacts",
            visible_fields=["first_name", "last_name", "email"],
            body_builder=lambda v: {
                "first_name": getattr(v, "first_name", "") or "",
                "last_name": getattr(v, "last_name", "") or "",
                "email_addresses": [{"address": getattr(v, "email", "") or "", "kind": "Work"}]
                if getattr(v, "email", None)
                else [],
            },
        ),
        OpSpec(
            id="list_notes",
            label="List Notes",
            method="GET",
            path="/notes",
            visible_fields=["limit"],
            query_builder=lambda v: {"per_page": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="create_note",
            label="Create Note",
            method="POST",
            path="/notes",
            visible_fields=["content", "contact_id"],
            body_builder=lambda v: {
                "content": getattr(v, "content", "") or "",
                "linked_to": [{"type": "Contact", "id": int(getattr(v, "contact_id", 0) or 0)}]
                if getattr(v, "contact_id", None)
                else [],
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "results", "type": "array"},
    ],
    allow_error=True,
)
