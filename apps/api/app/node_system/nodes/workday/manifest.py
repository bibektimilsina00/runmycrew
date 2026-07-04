"""Workday action node — Workday — HR + finance ERP (RaaS + REST APIs).

REST at {tenant_url}/ccx/api/v1. See sim-parity roadmap Phase 4.24.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.workday",
    name="Workday",
    category="integration",
    description="Workday — HR + finance ERP (RaaS + REST APIs).",
    icon_slug="workday",
    color="#1c1c1c",
    base_url="{tenant_url}/ccx/api/v1",
    credential_type="workday_api_key",
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
            id="get_worker",
            label="Get Worker",
            method="GET",
            path="/{tenant}/workers/{worker_id}",
            visible_fields=["tenant", "worker_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_workers",
            label="List Workers",
            method="GET",
            path="/{tenant}/workers",
            visible_fields=["tenant", "limit", "offset"],
            query_builder=lambda v: {
                "limit": int(getattr(v, "limit", 25) or 25),
                "offset": int(getattr(v, "offset", 0) or 0),
            },
        ),
        OpSpec(
            id="run_raas_report",
            label="Run RaaS Report (URL)",
            method="GET",
            path="{raas_url}",
            visible_fields=["raas_url"],
            query_builder=lambda v: {"format": "json"},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "results", "type": "array"},
    ],
    allow_error=True,
)
