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
SF_API_VERSION = "v59.0"


class SalesforceProperties(BaseModel):
    credential: str | None = None
    operation: str = "query"
    object_type: str | None = None
    record_id: str | None = None
    fields: str | None = None  # comma-separated for get_record
    record_data: Any | None = None  # JSON dict for create/update
    soql_query: str | None = None
    limit: int = 10


class SalesforceNode(BaseNode[SalesforceProperties]):
    @classmethod
    def get_properties_model(cls):
        return SalesforceProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.salesforce",
            name="Salesforce",
            category="integration",
            description="Create and query Salesforce records (Contacts, Leads, Accounts, Opportunities).",
            icon="si:SiSalesforce",
            color="#00a1e0",
            properties=[
                {
                    "name": "credential",
                    "label": "Salesforce Credential",
                    "type": "credential",
                    "credentialType": "salesforce_api_key",
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "query",
                    "options": [
                        {"label": "SOQL Query", "value": "query"},
                        {"label": "Create Record", "value": "create_record"},
                        {"label": "Get Record", "value": "get_record"},
                        {"label": "Update Record", "value": "update_record"},
                        {"label": "Delete Record", "value": "delete_record"},
                        {"label": "List Object Types", "value": "list_objects"},
                    ],
                },
                {
                    "name": "object_type",
                    "label": "Object Type",
                    "type": "string",
                    "placeholder": "Contact, Lead, Account, Opportunity…",
                    "condition": {
                        "field": "operation",
                        "value": ["create_record", "get_record", "update_record", "delete_record"],
                    },
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
                    "name": "record_data",
                    "label": "Fields (JSON)",
                    "type": "json",
                    "placeholder": '{"FirstName":"John","Email":"john@example.com"}',
                    "condition": {
                        "field": "operation",
                        "value": ["create_record", "update_record"],
                    },
                },
                {
                    "name": "fields",
                    "label": "Fields to Return",
                    "type": "string",
                    "placeholder": "Id,Name,Email",
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "get_record"},
                },
                {
                    "name": "soql_query",
                    "label": "SOQL Query",
                    "type": "string",
                    "placeholder": "SELECT Id, Name FROM Contact LIMIT 10",
                    "condition": {"field": "operation", "value": "query"},
                },
                {
                    "name": "limit",
                    "label": "Limit",
                    "type": "number",
                    "default": 10,
                    "mode": "advanced",
                    "condition": {"field": "operation", "value": "query"},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "records", "type": "array"},
                {"label": "totalSize", "type": "number"},
                {"label": "record", "type": "object"},
            ],
            allow_error=True,
            credential_type="salesforce_api_key",
        )

    def _access_token(self) -> str | None:
        if not self.credential:
            return None
        return self.credential.get("api_key") or self.credential.get("access_token")

    def _instance_url(self) -> str:
        if not self.credential:
            return ""
        return self.credential.get("instance_url", "").rstrip("/")

    def _base(self) -> str:
        return f"{self._instance_url()}/services/data/{SF_API_VERSION}"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self._access_token()}",
            "Content-Type": "application/json",
        }

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self._access_token():
            return NodeResult(
                success=False,
                error="Salesforce credential required (api_key/access_token + instance_url).",
            )
        if not self._instance_url():
            return NodeResult(
                success=False, error="instance_url missing from Salesforce credential."
            )
        op = self.props.operation
        try:
            async with httpx.AsyncClient(timeout=30) as c:
                if op == "query":
                    q = (
                        self.props.soql_query
                        or f"SELECT Id, Name FROM Contact LIMIT {self.props.limit}"
                    )
                    r = await c.get(
                        f"{self._base()}/query/", headers=self._headers(), params={"q": q}
                    )
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={
                            "records": d.get("records", []),
                            "totalSize": d.get("totalSize", 0),
                            "done": d.get("done", True),
                        },
                    )

                elif op == "create_record":
                    if not self.props.object_type:
                        return NodeResult(success=False, error="object_type required")
                    r = await c.post(
                        f"{self._base()}/sobjects/{self.props.object_type}/",
                        headers=self._headers(),
                        json=self.props.record_data or {},
                    )
                    r.raise_for_status()
                    d = r.json()
                    return NodeResult(
                        success=True,
                        output_data={"id": d.get("id"), "success": d.get("success", True)},
                    )

                elif op == "get_record":
                    if not self.props.object_type or not self.props.record_id:
                        return NodeResult(success=False, error="object_type and record_id required")
                    url = f"{self._base()}/sobjects/{self.props.object_type}/{self.props.record_id}"
                    params = {"fields": self.props.fields} if self.props.fields else {}
                    r = await c.get(url, headers=self._headers(), params=params)
                    r.raise_for_status()
                    return NodeResult(success=True, output_data={"record": r.json()})

                elif op == "update_record":
                    if not self.props.object_type or not self.props.record_id:
                        return NodeResult(success=False, error="object_type and record_id required")
                    r = await c.patch(
                        f"{self._base()}/sobjects/{self.props.object_type}/{self.props.record_id}",
                        headers=self._headers(),
                        json=self.props.record_data or {},
                    )
                    r.raise_for_status()  # 204 No Content on success
                    return NodeResult(
                        success=True, output_data={"id": self.props.record_id, "updated": True}
                    )

                elif op == "delete_record":
                    if not self.props.object_type or not self.props.record_id:
                        return NodeResult(success=False, error="object_type and record_id required")
                    r = await c.delete(
                        f"{self._base()}/sobjects/{self.props.object_type}/{self.props.record_id}",
                        headers=self._headers(),
                    )
                    r.raise_for_status()
                    return NodeResult(
                        success=True, output_data={"id": self.props.record_id, "deleted": True}
                    )

                elif op == "list_objects":
                    r = await c.get(f"{self._base()}/sobjects/", headers=self._headers())
                    r.raise_for_status()
                    d = r.json()
                    objects = [
                        {"name": o["name"], "label": o["label"], "queryable": o.get("queryable")}
                        for o in d.get("sobjects", [])
                    ]
                    return NodeResult(
                        success=True, output_data={"objects": objects, "count": len(objects)}
                    )

                else:
                    return NodeResult(success=False, error=f"Unknown operation: {op}")

        except httpx.HTTPStatusError as e:
            return NodeResult(
                success=False,
                error=f"Salesforce API {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            logger.error(f"SalesforceNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
