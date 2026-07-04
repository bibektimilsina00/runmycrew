"""Jira Service Management action node — Jira Service Management — requests, service desks, queues.

REST at https://{domain}/rest/servicedeskapi. See sim-parity roadmap Phase 4.28.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.jira_service_management",
    name="Jira Service Management",
    category="integration",
    description="Jira Service Management — requests, service desks, queues.",
    icon_slug="jira_service_management",
    color="#1c1c1c",
    base_url="https://{domain}/rest/servicedeskapi",
    credential_type="jira_service_management_api_key",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{email}",
    fields=[
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="group_id", label="Group ID", type="string"),
        FieldSpec(name="user_principal_name", label="User Principal Name", type="string"),
        FieldSpec(name="display_name", label="Display Name", type="string"),
        FieldSpec(name="mail_nickname", label="Mail Nickname", type="string"),
        FieldSpec(name="password", label="Password", type="string", secret=True),
        FieldSpec(name="top", label="Top", type="number", default=25, mode="advanced"),
        FieldSpec(name="filter", label="Filter", type="string", mode="advanced"),
        FieldSpec(name="entity", label="Entity (plural)", type="string", placeholder="accounts"),
        FieldSpec(name="record_id", label="Record GUID", type="string"),
        FieldSpec(name="select", label="Select", type="string", mode="advanced"),
        FieldSpec(name="data", label="Data (JSON)", type="json", default={}),
        FieldSpec(name="service_desk_id", label="Service Desk ID", type="string"),
        FieldSpec(name="request_type_id", label="Request Type ID", type="string"),
        FieldSpec(name="summary", label="Summary", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="issue_key", label="Issue Key", type="string"),
        FieldSpec(
            name="request_status", label="Request Status", type="string", default="OPEN_REQUESTS"
        ),
        FieldSpec(name="comment_body", label="Comment Body", type="string"),
        FieldSpec(name="public", label="Public", type="boolean", default=True),
        FieldSpec(name="origin_zip", label="Origin ZIP", type="string"),
        FieldSpec(name="destination_zip", label="Destination ZIP", type="string"),
        FieldSpec(name="weight_lb", label="Weight (lb)", type="number"),
        FieldSpec(name="commodity", label="Commodity", type="string"),
        FieldSpec(name="quote_id", label="Quote ID", type="string"),
        FieldSpec(name="shipment_id", label="Shipment ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_service_desks",
            label="List Service Desks",
            method="GET",
            path="/servicedesk",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_request_types",
            label="List Request Types",
            method="GET",
            path="/servicedesk/{service_desk_id}/requesttype",
            visible_fields=["service_desk_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_request",
            label="Create Request",
            method="POST",
            path="/request",
            visible_fields=["service_desk_id", "request_type_id", "summary", "description"],
            body_builder=lambda v: {
                "serviceDeskId": getattr(v, "service_desk_id", "") or "",
                "requestTypeId": getattr(v, "request_type_id", "") or "",
                "requestFieldValues": {
                    "summary": getattr(v, "summary", "") or "",
                    "description": getattr(v, "description", None) or "",
                },
            },
        ),
        OpSpec(
            id="get_request",
            label="Get Request",
            method="GET",
            path="/request/{issue_key}",
            visible_fields=["issue_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_requests",
            label="List My Requests",
            method="GET",
            path="/request",
            visible_fields=["service_desk_id", "request_status"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "serviceDeskId": getattr(v, "service_desk_id", None) or None,
                    "requestStatus": getattr(v, "request_status", None) or None,
                }.items()
                if val
            },
        ),
        OpSpec(
            id="add_comment",
            label="Add Comment to Request",
            method="POST",
            path="/request/{issue_key}/comment",
            visible_fields=["issue_key", "comment_body", "public"],
            body_builder=lambda v: {
                "body": getattr(v, "comment_body", "") or "",
                "public": bool(getattr(v, "public", True)),
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
