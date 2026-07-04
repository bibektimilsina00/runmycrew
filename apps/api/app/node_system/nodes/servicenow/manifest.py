"""ServiceNow action node — manifest form.

ServiceNow Table API at `https://{instance}.service-now.com/api/now/table/{table}`.
Basic auth using `{username}:{password}` where password can be an
API token (recommended) or the user's real password (dev only).

Instance is per-customer, so the manifest's `base_url` is empty and
every op templates `{instance}` into its path — Zendesk pattern.

Common tables: `incident`, `change_request`, `problem`, `sc_task`
(catalog task), `sys_user`. The generic `get_record` / `list_records` /
`create_record` / `update_record` / `delete_record` ops take a
`table_name` prop so a workflow can hit any table. Specific
shortcuts (`create_incident`, `create_change_request`, etc.) fill in
the table name for the common cases.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://{instance}.service-now.com/api/now"


def _params(v, **static) -> dict:
    """Small helper — build a params dict, drop None values so the
    scaffold sends only what the user actually set. Static keys are
    always included."""
    out: dict = {}
    for k, val in static.items():
        if val is not None and val != "":
            out[k] = val
    return out


MANIFEST = ProviderManifest(
    type="action.servicenow",
    name="ServiceNow",
    category="integration",
    description="ServiceNow — ITSM records via Table API (incidents, changes, custom tables).",
    icon_slug="servicenow",
    color="#1c1c1c",
    base_url="",
    credential_type="servicenow_api_key",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{username}",
    fields=[
        FieldSpec(
            name="table_name",
            label="Table",
            type="string",
            placeholder="incident | change_request | problem | sc_task | ...",
        ),
        FieldSpec(name="sys_id", label="Record sys_id", type="string"),
        FieldSpec(
            name="query",
            label="Encoded Query (sysparm_query)",
            type="string",
            placeholder="active=true^priority=1",
            mode="advanced",
        ),
        FieldSpec(name="short_description", label="Short Description", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="caller_id", label="Caller ID", type="string"),
        FieldSpec(name="assignment_group", label="Assignment Group", type="string"),
        FieldSpec(name="assigned_to", label="Assigned To", type="string"),
        FieldSpec(
            name="priority",
            label="Priority",
            type="options",
            options=[
                {"label": "1 - Critical", "value": "1"},
                {"label": "2 - High", "value": "2"},
                {"label": "3 - Moderate", "value": "3"},
                {"label": "4 - Low", "value": "4"},
                {"label": "5 - Planning", "value": "5"},
            ],
            mode="advanced",
        ),
        FieldSpec(
            name="state",
            label="State",
            type="string",
            mode="advanced",
            placeholder="1 = New, 6 = Resolved, etc.",
        ),
        FieldSpec(name="category", label="Category", type="string", mode="advanced"),
        FieldSpec(name="record_data", label="Record fields (JSON)", type="json"),
        FieldSpec(
            name="fields", label="Return fields (comma-separated)", type="string", mode="advanced"
        ),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(name="offset", label="Offset", type="number", default=0, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="get_record",
            label="Get Record",
            method="GET",
            path=_HOST + "/table/{table_name}/{sys_id}",
            visible_fields=["table_name", "sys_id", "fields"],
            query_builder=lambda v: _params(
                v,
                sysparm_fields=getattr(v, "fields", None),
                sysparm_display_value="true",
            ),
        ),
        OpSpec(
            id="list_records",
            label="List Records",
            method="GET",
            path=_HOST + "/table/{table_name}",
            visible_fields=["table_name", "query", "fields", "limit", "offset"],
            query_builder=lambda v: _params(
                v,
                sysparm_query=getattr(v, "query", None),
                sysparm_fields=getattr(v, "fields", None),
                sysparm_limit=int(getattr(v, "limit", 25) or 25),
                sysparm_offset=int(getattr(v, "offset", 0) or 0),
                sysparm_display_value="true",
            ),
        ),
        OpSpec(
            id="create_record",
            label="Create Record",
            method="POST",
            path=_HOST + "/table/{table_name}",
            visible_fields=["table_name", "record_data"],
            body_builder=lambda v: getattr(v, "record_data", None) or {},
        ),
        OpSpec(
            id="update_record",
            label="Update Record",
            method="PATCH",
            path=_HOST + "/table/{table_name}/{sys_id}",
            visible_fields=["table_name", "sys_id", "record_data"],
            body_builder=lambda v: getattr(v, "record_data", None) or {},
        ),
        OpSpec(
            id="delete_record",
            label="Delete Record",
            method="DELETE",
            path=_HOST + "/table/{table_name}/{sys_id}",
            visible_fields=["table_name", "sys_id"],
        ),
        OpSpec(
            id="create_incident",
            label="Create Incident",
            method="POST",
            path=_HOST + "/table/incident",
            visible_fields=[
                "short_description",
                "description",
                "caller_id",
                "assignment_group",
                "assigned_to",
                "priority",
                "category",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "short_description": getattr(v, "short_description", None),
                    "description": getattr(v, "description", None),
                    "caller_id": getattr(v, "caller_id", None),
                    "assignment_group": getattr(v, "assignment_group", None),
                    "assigned_to": getattr(v, "assigned_to", None),
                    "priority": getattr(v, "priority", None),
                    "category": getattr(v, "category", None),
                }.items()
                if val
            },
        ),
        OpSpec(
            id="update_incident",
            label="Update Incident",
            method="PATCH",
            path=_HOST + "/table/incident/{sys_id}",
            visible_fields=[
                "sys_id",
                "short_description",
                "state",
                "priority",
                "assigned_to",
                "record_data",
            ],
            body_builder=lambda v: {
                **(getattr(v, "record_data", None) or {}),
                **{
                    k: val
                    for k, val in {
                        "short_description": getattr(v, "short_description", None),
                        "state": getattr(v, "state", None),
                        "priority": getattr(v, "priority", None),
                        "assigned_to": getattr(v, "assigned_to", None),
                    }.items()
                    if val
                },
            },
        ),
        OpSpec(
            id="get_incident",
            label="Get Incident",
            method="GET",
            path=_HOST + "/table/incident/{sys_id}",
            visible_fields=["sys_id"],
            query_builder=lambda v: {"sysparm_display_value": "true"},  # noqa: ARG005
        ),
        OpSpec(
            id="list_incidents",
            label="List Incidents",
            method="GET",
            path=_HOST + "/table/incident",
            visible_fields=["query", "limit"],
            query_builder=lambda v: _params(
                v,
                sysparm_query=getattr(v, "query", None) or "active=true",
                sysparm_limit=int(getattr(v, "limit", 25) or 25),
                sysparm_display_value="true",
            ),
        ),
        OpSpec(
            id="create_change_request",
            label="Create Change Request",
            method="POST",
            path=_HOST + "/table/change_request",
            visible_fields=[
                "short_description",
                "description",
                "assignment_group",
                "assigned_to",
                "priority",
                "category",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "short_description": getattr(v, "short_description", None),
                    "description": getattr(v, "description", None),
                    "assignment_group": getattr(v, "assignment_group", None),
                    "assigned_to": getattr(v, "assigned_to", None),
                    "priority": getattr(v, "priority", None),
                    "category": getattr(v, "category", None),
                }.items()
                if val
            },
        ),
    ],
    outputs_schema=[
        {"label": "result", "type": "object"},
        {"label": "sys_id", "type": "string"},
        {"label": "number", "type": "string"},
        {"label": "state", "type": "string"},
        {"label": "priority", "type": "string"},
    ],
    allow_error=True,
)
