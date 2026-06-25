from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)
AIRTABLE_API = "https://api.airtable.com/v0"


class AirtableProperties(BaseModel):
    credential: str | None = None
    operation: str = "list_records"
    base_id: str | None = None
    table_name: str | None = None
    record_id: str | None = None
    fields: Any | None = None  # dict of field values for create/update
    filter_formula: str | None = None
    sort: Any | None = None
    max_records: int = 100
    view: str | None = None


class AirtableNode(BaseNode[AirtableProperties]):
    @classmethod
    def get_properties_model(cls):
        return AirtableProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.airtable",
            name="Airtable",
            category="integration",
            description="Read and write Airtable bases, tables, and records.",
            icon="airtable",
            color="#1c1c1c",
            properties=[
                {
                    "name": "credential",
                    "label": "Airtable Token",
                    "type": "credential",
                    "credentialType": "airtable_api_key",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "list_records",
                    "options": [
                        {"label": "List Records", "value": "list_records"},
                        {"label": "Get Record", "value": "get_record"},
                        {"label": "Create Record", "value": "create_record"},
                        {"label": "Update Record", "value": "update_record"},
                        {"label": "Delete Record", "value": "delete_record"},
                        {"label": "Search Records (formula)", "value": "search_records"},
                    ],
                },
                {
                    "name": "base_id",
                    "label": "Base ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "appXXXXXXXX",
                },
                {
                    "name": "table_name",
                    "label": "Table Name",
                    "type": "string",
                    "required": True,
                    "placeholder": "Contacts",
                },
                {
                    "name": "record_id",
                    "label": "Record ID",
                    "type": "string",
                    "condition": {
                        "field": "operation",
                        "value": ["get_record", "update_record", "delete_record"],
                    },
                },
                {
                    "name": "fields",
                    "label": "Fields (JSON)",
                    "type": "json",
                    "condition": {
                        "field": "operation",
                        "value": ["create_record", "update_record"],
                    },
                    "placeholder": '{"Name": "John", "Email": "john@example.com"}',
                },
                {
                    "name": "filter_formula",
                    "label": "Filter Formula",
                    "type": "string",
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["list_records", "search_records"],
                    },
                    "placeholder": "{Status} = 'Active'",
                },
                {
                    "name": "view",
                    "label": "View",
                    "type": "string",
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["list_records", "search_records"],
                    },
                },
                {
                    "name": "max_records",
                    "label": "Max Records",
                    "type": "number",
                    "default": 100,
                    "mode": "advanced",
                    "condition": {
                        "field": "operation",
                        "value": ["list_records", "search_records"],
                    },
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "records", "type": "array"},
                {"label": "record", "type": "object"},
                {"label": "id", "type": "string"},
                {"label": "count", "type": "number"},
            ],
            allow_error=True,
            credential_type="airtable_api_key",
        )

    def _api_key(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("api_key")

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self._api_key()}", "Content-Type": "application/json"}

    def _table_url(self) -> str:
        return f"{AIRTABLE_API}/{self.props.base_id}/{self.props.table_name}"

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self._api_key():
            return NodeResult(success=False, error="Airtable token required.")
        if not self.props.base_id:
            return NodeResult(success=False, error="Base ID required.")
        if not self.props.table_name:
            return NodeResult(success=False, error="Table name required.")
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                if op == "list_records":
                    params: dict[str, Any] = {"maxRecords": min(self.props.max_records, 100)}
                    if self.props.filter_formula:
                        params["filterByFormula"] = self.props.filter_formula
                    if self.props.view:
                        params["view"] = self.props.view
                    r = await client.get(self._table_url(), headers=self._headers(), params=params)
                    r.raise_for_status()
                    data = r.json()
                    records = data.get("records", [])
                    return NodeResult(
                        success=True, output_data={"records": records, "count": len(records)}
                    )

                elif op == "get_record":
                    if not self.props.record_id:
                        return NodeResult(success=False, error="Record ID required.")
                    r = await client.get(
                        f"{self._table_url()}/{self.props.record_id}", headers=self._headers()
                    )
                    r.raise_for_status()
                    return NodeResult(success=True, output_data=r.json())

                elif op == "create_record":
                    body = {"fields": self.props.fields or {}}
                    r = await client.post(self._table_url(), headers=self._headers(), json=body)
                    r.raise_for_status()
                    rec = r.json()
                    return NodeResult(
                        success=True, output_data={"id": rec.get("id"), "record": rec}
                    )

                elif op == "update_record":
                    if not self.props.record_id:
                        return NodeResult(success=False, error="Record ID required.")
                    body = {"fields": self.props.fields or {}}
                    r = await client.patch(
                        f"{self._table_url()}/{self.props.record_id}",
                        headers=self._headers(),
                        json=body,
                    )
                    r.raise_for_status()
                    return NodeResult(success=True, output_data=r.json())

                elif op == "delete_record":
                    if not self.props.record_id:
                        return NodeResult(success=False, error="Record ID required.")
                    r = await client.delete(
                        f"{self._table_url()}/{self.props.record_id}", headers=self._headers()
                    )
                    r.raise_for_status()
                    return NodeResult(
                        success=True, output_data={"deleted": True, "id": self.props.record_id}
                    )

                elif op == "search_records":
                    params = {"maxRecords": min(self.props.max_records, 100)}
                    if self.props.filter_formula:
                        params["filterByFormula"] = self.props.filter_formula
                    r = await client.get(self._table_url(), headers=self._headers(), params=params)
                    r.raise_for_status()
                    records = r.json().get("records", [])
                    return NodeResult(
                        success=True, output_data={"records": records, "count": len(records)}
                    )

                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False,
                error=f"Airtable API {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.error(f"AirtableNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
