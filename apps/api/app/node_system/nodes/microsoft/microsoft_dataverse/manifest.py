"""Microsoft Dataverse action node — Microsoft Dataverse — read/write records in Power Platform tables.

REST at https://{org}.crm.dynamics.com/api/data/v9.2. See sim-parity roadmap Phase 4.28.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.microsoft_dataverse",
    name="Microsoft Dataverse",
    category="integration",
    description="Microsoft Dataverse — read/write records in Power Platform tables.",
    icon_slug="microsoft_dataverse",
    color="#ffffff",
    base_url="https://{org}.crm.dynamics.com/api/data/v9.2",
    credential_type="microsoft_oauth",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="user_id", label="User ID", type="string"),
        FieldSpec(name="group_id", label="Group ID", type="string"),
        FieldSpec(name="user_principal_name", label="User Principal Name", type="string"),
        FieldSpec(name="display_name", label="Display Name", type="string"),
        FieldSpec(name="mail_nickname", label="Mail Nickname", type="string"),
        FieldSpec(name="password", label="Password", type="string", secret=True),
        FieldSpec(name="top", label="Top", type="number", default=25, mode="advanced"),
        FieldSpec(name="filter", label="Filter", type="string", mode="advanced"),
        FieldSpec(
            name="entity",
            label="Entity",
            type="string",
            placeholder="accounts",
            remote=RemoteLookup(provider="dataverse", resource="entities"),
        ),
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
        FieldSpec(name="fetchxml", label="FetchXML Query", type="string"),
        FieldSpec(name="search_query", label="Search Query", type="string"),
        FieldSpec(name="action_name", label="Action Name", type="string"),
        FieldSpec(name="action_body", label="Action Body (JSON)", type="json", default={}),
        FieldSpec(name="function_name", label="Function Name", type="string"),
        FieldSpec(name="navigation_property", label="Navigation Property", type="string"),
        FieldSpec(name="target_entity", label="Target Entity", type="string"),
        FieldSpec(name="target_id", label="Target Record ID", type="string"),
        FieldSpec(name="multiple_body", label="Multiple Body (JSON)", type="json", default={}),
        FieldSpec(name="file_column", label="File Column Name", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_records",
            label="List Records",
            method="GET",
            path="/{entity}",
            visible_fields=["entity", "select", "filter", "top"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "$select": getattr(v, "select", None) or None,
                    "$filter": getattr(v, "filter", None) or None,
                    "$top": getattr(v, "top", None) or None,
                }.items()
                if val
            },
        ),
        OpSpec(
            id="get_record",
            label="Get Record",
            method="GET",
            path="/{entity}({record_id})",
            visible_fields=["entity", "record_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_record",
            label="Create Record",
            method="POST",
            path="/{entity}",
            visible_fields=["entity", "data"],
            body_builder=lambda v: getattr(v, "data", {}) or {},
        ),
        OpSpec(
            id="update_record",
            label="Update Record",
            method="PATCH",
            path="/{entity}({record_id})",
            visible_fields=["entity", "record_id", "data"],
            body_builder=lambda v: getattr(v, "data", {}) or {},
        ),
        OpSpec(
            id="delete_record",
            label="Delete Record",
            method="DELETE",
            path="/{entity}({record_id})",
            visible_fields=["entity", "record_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="upsert_record",
            label="Upsert Record",
            method="PATCH",
            path="/{entity}({record_id})",
            visible_fields=["entity", "record_id", "data"],
            body_builder=lambda v: getattr(v, "data", None) or {},
        ),
        OpSpec(
            id="create_multiple",
            label="Create Multiple Records",
            method="POST",
            path="/{entity}/Microsoft.Dynamics.CRM.CreateMultiple",
            visible_fields=["entity", "multiple_body"],
            body_builder=lambda v: getattr(v, "multiple_body", None) or {},
        ),
        OpSpec(
            id="update_multiple",
            label="Update Multiple Records",
            method="POST",
            path="/{entity}/Microsoft.Dynamics.CRM.UpdateMultiple",
            visible_fields=["entity", "multiple_body"],
            body_builder=lambda v: getattr(v, "multiple_body", None) or {},
        ),
        OpSpec(
            id="fetchxml_query",
            label="FetchXML Query",
            method="GET",
            path="/{entity}",
            visible_fields=["entity", "fetchxml"],
            query_builder=lambda v: {"fetchXml": getattr(v, "fetchxml", "") or ""},
        ),
        OpSpec(
            id="dv_search",
            label="Search Records",
            method="POST",
            path="/api/search/v1.0/query",
            visible_fields=["search_query"],
            body_builder=lambda v: {"search": getattr(v, "search_query", "") or ""},
        ),
        OpSpec(
            id="execute_action",
            label="Execute Action",
            method="POST",
            path="/{action_name}",
            visible_fields=["action_name", "action_body"],
            body_builder=lambda v: getattr(v, "action_body", None) or {},
        ),
        OpSpec(
            id="execute_function",
            label="Execute Function",
            method="GET",
            path="/{function_name}()",
            visible_fields=["function_name"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="upload_file",
            label="Upload File Column",
            method="PATCH",
            path="/{entity}({record_id})/{file_column}",
            visible_fields=["entity", "record_id", "file_column"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="download_file",
            label="Download File Column",
            method="GET",
            path="/{entity}({record_id})/{file_column}/$value",
            visible_fields=["entity", "record_id", "file_column"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="associate",
            label="Associate Records",
            method="POST",
            path="/{entity}({record_id})/{navigation_property}/$ref",
            visible_fields=[
                "entity",
                "record_id",
                "navigation_property",
                "target_entity",
                "target_id",
            ],
            body_builder=lambda v: {
                "@odata.id": "https://"
                + "dynamics.com/api/data/v9.2/"
                + (getattr(v, "target_entity", "") or "")
                + "("
                + (getattr(v, "target_id", "") or "")
                + ")"
            },
        ),
        OpSpec(
            id="disassociate",
            label="Disassociate Records",
            method="DELETE",
            path="/{entity}({record_id})/{navigation_property}({target_id})/$ref",
            visible_fields=["entity", "record_id", "navigation_property", "target_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="whoami",
            label="WhoAmI (current user)",
            method="GET",
            path="/WhoAmI",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
