"""Rippling action node — Rippling — HR platform (employees, orgs, payroll).

REST at https://api.rippling.com. See sim-parity roadmap Phase 4.24.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.rippling",
    name="Rippling",
    category="integration",
    description="Rippling — HR platform (employees, orgs, payroll).",
    icon_slug="rippling",
    color="#1c1c1c",
    base_url="https://api.rippling.com",
    credential_type="rippling_api_key",
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
            id="list_employees",
            label="List Employees",
            method="GET",
            path="/platform/api/employees",
            visible_fields=["limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 25) or 25)},
        ),
        OpSpec(
            id="get_employee",
            label="Get Employee",
            method="GET",
            path="/platform/api/employees/{employee_id}",
            visible_fields=["employee_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_departments",
            label="List Departments",
            method="GET",
            path="/platform/api/departments",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_teams",
            label="List Teams",
            method="GET",
            path="/platform/api/teams",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_work_locations",
            label="List Work Locations",
            method="GET",
            path="/platform/api/work_locations",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "results", "type": "array"},
    ],
    allow_error=True,
)
