"""Microsoft Excel action node — manifest form.

Graph endpoints at `/v1.0/me/drive/items/{workbook_id}/workbook/...`.
Workbook is identified by a Drive item id. Worksheet, range, and
table ops cover the common read/write patterns.

Ranges use Excel A1 notation. The Graph API splits update payloads
between `values`, `formulas`, and `numberFormat` arrays — we accept
all three as optional JSON props.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.microsoft_excel",
    name="Microsoft Excel",
    category="integration",
    description="Microsoft Excel workbooks — worksheets, ranges, tables.",
    icon_slug="microsoft-excel",
    color="#ffffff",
    base_url="https://graph.microsoft.com/v1.0",
    credential_type="microsoft_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="workbook_id",
            label="Workbook",
            type="string",
            remote=RemoteLookup(provider="microsoft", resource="excel_workbooks"),
        ),
        FieldSpec(name="worksheet", label="Worksheet Name", type="string", placeholder="Sheet1"),
        FieldSpec(name="range", label="Range (A1)", type="string", placeholder="A1:C10"),
        FieldSpec(name="values", label="Values (JSON 2D array)", type="json"),
        FieldSpec(name="formulas", label="Formulas (JSON 2D array)", type="json", mode="advanced"),
        FieldSpec(
            name="number_format",
            label="Number Format (JSON 2D array)",
            type="json",
            mode="advanced",
        ),
        FieldSpec(name="table_name", label="Table Name", type="string"),
        FieldSpec(name="row_index", label="Row Index", type="number", mode="advanced"),
        FieldSpec(name="address", label="Cell Address", type="string", mode="advanced"),
        FieldSpec(name="new_sheet_name", label="New Worksheet Name", type="string"),
    ],
    operations=[
        OpSpec(
            id="list_worksheets",
            label="List Worksheets",
            method="GET",
            path="/me/drive/items/{workbook_id}/workbook/worksheets",
            visible_fields=["workbook_id"],
        ),
        OpSpec(
            id="add_worksheet",
            label="Add Worksheet",
            method="POST",
            path="/me/drive/items/{workbook_id}/workbook/worksheets/add",
            visible_fields=["workbook_id", "new_sheet_name"],
            body_builder=lambda v: {"name": getattr(v, "new_sheet_name", None) or ""},
        ),
        OpSpec(
            id="get_range",
            label="Get Range",
            method="GET",
            path=(
                "/me/drive/items/{workbook_id}/workbook/worksheets/"
                "{worksheet}/range(address='{range}')"
            ),
            visible_fields=["workbook_id", "worksheet", "range"],
        ),
        OpSpec(
            id="update_range",
            label="Update Range",
            method="PATCH",
            path=(
                "/me/drive/items/{workbook_id}/workbook/worksheets/"
                "{worksheet}/range(address='{range}')"
            ),
            visible_fields=[
                "workbook_id",
                "worksheet",
                "range",
                "values",
                "formulas",
                "number_format",
            ],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "values": getattr(v, "values", None),
                    "formulas": getattr(v, "formulas", None),
                    "numberFormat": getattr(v, "number_format", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="list_tables",
            label="List Tables",
            method="GET",
            path="/me/drive/items/{workbook_id}/workbook/tables",
            visible_fields=["workbook_id"],
        ),
        OpSpec(
            id="add_table_row",
            label="Add Table Row",
            method="POST",
            path=("/me/drive/items/{workbook_id}/workbook/tables/{table_name}/rows/add"),
            visible_fields=["workbook_id", "table_name", "values"],
            body_builder=lambda v: {"values": getattr(v, "values", None) or []},
        ),
        OpSpec(
            id="list_table_rows",
            label="List Table Rows",
            method="GET",
            path="/me/drive/items/{workbook_id}/workbook/tables/{table_name}/rows",
            visible_fields=["workbook_id", "table_name"],
        ),
        OpSpec(
            id="delete_table_row",
            label="Delete Table Row",
            method="DELETE",
            path=(
                "/me/drive/items/{workbook_id}/workbook/tables/{table_name}/rows"
                "/itemAt(index={row_index})"
            ),
            visible_fields=["workbook_id", "table_name", "row_index"],
            success_payload_template={"deleted": True, "row_index": "{row_index}"},
        ),
        OpSpec(
            id="get_cell",
            label="Get Cell",
            method="GET",
            path=(
                "/me/drive/items/{workbook_id}/workbook/worksheets/{worksheet}"
                "/range(address='{address}')"
            ),
            visible_fields=["workbook_id", "worksheet", "address"],
        ),
    ],
    outputs_schema=[
        {"label": "values", "type": "array"},
        {"label": "address", "type": "string"},
        {"label": "rowCount", "type": "number"},
        {"label": "columnCount", "type": "number"},
        {"label": "value", "type": "array"},
        {"label": "name", "type": "string"},
    ],
    allow_error=True,
)
