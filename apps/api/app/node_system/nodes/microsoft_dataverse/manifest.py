"""Microsoft Dataverse action node — Microsoft Dataverse — read/write records in Power Platform tables.

REST at https://{org}.crm.dynamics.com/api/data/v9.2. See sim-parity roadmap Phase 4.28.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.microsoft_dataverse",
    name="Microsoft Dataverse",
    category="integration",
    description="Microsoft Dataverse — read/write records in Power Platform tables.",
    icon_slug="microsoft_dataverse",
    color="#1c1c1c",
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
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
    ],
    allow_error=True,
)
