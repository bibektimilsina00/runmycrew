"""SAP Concur action node — SAP Concur — travel + expense management.

REST at https://us.api.concursolutions.com. See sim-parity roadmap Phase 4.24.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.sap_concur",
    name="SAP Concur",
    category="integration",
    description="SAP Concur — travel + expense management.",
    icon_slug="sap_concur",
    color="#1c1c1c",
    base_url="https://us.api.concursolutions.com",
    credential_type="sap_concur_api_key",
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
        FieldSpec(name="context", label="Context (TRAVELER|APPROVER|PROCESSOR)", type="string"),
        FieldSpec(name="entry_id", label="Entry ID", type="string"),
        FieldSpec(name="booking_id", label="Booking ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_reports",
            label="List Expense Reports",
            method="GET",
            path="/api/v3.0/expense/reports",
            visible_fields=["user_id"],
            query_builder=lambda v: {
                k: val for k, val in {"user": getattr(v, "user_id", None) or None}.items() if val
            },
        ),
        OpSpec(
            id="get_report",
            label="Get Expense Report",
            method="GET",
            path="/api/v3.0/expense/reports/{report_id}",
            visible_fields=["report_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_entries",
            label="List Entries in Report",
            method="GET",
            path="/api/v3.0/expense/entries",
            visible_fields=["report_id"],
            query_builder=lambda v: {"reportID": getattr(v, "report_id", "") or ""},
        ),
        OpSpec(
            id="get_report_details",
            label="Get Report Details",
            method="GET",
            path="/expensereports/v4/users/{user_id}/context/{context}/reports/{report_id}",
            visible_fields=["user_id", "context", "report_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_expenses",
            label="List Expense Entries",
            method="GET",
            path="/api/v3.0/expense/entries",
            visible_fields=["report_id"],
            query_builder=lambda v: {
                k: val
                for k, val in {"reportID": getattr(v, "report_id", None) or None}.items()
                if val
            },
        ),
        OpSpec(
            id="get_expense",
            label="Get Expense Entry",
            method="GET",
            path="/api/v3.0/expense/entries/{entry_id}",
            visible_fields=["entry_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_receipts",
            label="List Receipt Images",
            method="GET",
            path="/api/v3.0/expense/receiptimages",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_users",
            label="List Users",
            method="GET",
            path="/api/v3.0/common/users",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_user",
            label="Get User",
            method="GET",
            path="/api/v3.0/common/users/{user_id}",
            visible_fields=["user_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_travel_bookings",
            label="List Travel Bookings",
            method="GET",
            path="/api/travel/v1.1/bookings",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_travel_booking",
            label="Get Travel Booking",
            method="GET",
            path="/api/travel/v1.1/bookings/{booking_id}",
            visible_fields=["booking_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_itemization_types",
            label="List Itemization Types",
            method="GET",
            path="/api/v3.0/expense/itemizationtypes",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_expense_types",
            label="List Expense Types",
            method="GET",
            path="/api/v3.0/expense/expensetypes",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_currency_codes",
            label="List Currency Codes",
            method="GET",
            path="/api/v3.0/common/enums/currencies",
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
