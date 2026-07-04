"""Brex action node — Brex — corporate cards + expense management.

REST at https://platform.brexapis.com/v2. See sim-parity roadmap Phase 4.24.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.brex",
    name="Brex",
    category="integration",
    description="Brex — corporate cards + expense management.",
    icon_slug="brex",
    color="#1c1c1c",
    base_url="https://platform.brexapis.com/v2",
    credential_type="brex_api_key",
    token_field=["api_key"],
    auth="bearer",
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
            id="list_transactions",
            label="List Card Transactions",
            method="GET",
            path="/transactions/card/primary",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="list_users",
            label="List Users",
            method="GET",
            path="/users",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="list_expenses",
            label="List Expenses",
            method="GET",
            path="/expenses/card",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="get_expense",
            label="Get Expense",
            method="GET",
            path="/expenses/card/{expense_id}",
            visible_fields=["expense_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_budgets",
            label="List Budgets",
            method="GET",
            path="/budgets",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "results", "type": "array"},
    ],
    allow_error=True,
)
