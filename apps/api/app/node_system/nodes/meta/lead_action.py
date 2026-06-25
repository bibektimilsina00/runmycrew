"""Consolidated Lead Ads action node.

Replaces `lead_fetch`. Single operation today (`fetch`); the dropdown
keeps room for future Lead Ads write ops without re-introducing a
per-task node.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.features.meta.service import MetaService
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import (
    find_credential,
    page_token_by_page_id,
)

LEAD_ACTION_OPS: tuple[str, ...] = ("fetch",)


class LeadActionProperties(BaseModel):
    credential: str | None = None
    operation: str = "fetch"
    page_id: str = ""
    leadgen_id: str = ""


class LeadActionNode(BaseNode[LeadActionProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.lead",
            name="Lead Ads",
            category="action",
            description=(
                "Resolve a Lead Ads `leadgen_id` (from the lead trigger) into "
                "the full submitted form data. Requires the Page admin to "
                "have granted Lead Access to your Meta app."
            ),
            icon="ListChecks",
            color="#1c1c1c",
            properties=[
                {
                    "name": "credential",
                    "label": "Meta Account",
                    "type": "credential",
                    "credentialType": "meta_oauth",
                    "required": True,
                },
                {
                    "name": "page_id",
                    "label": "Facebook Page",
                    "type": "meta-resource",
                    "resourceKind": "page",
                    "dependsOn": ["credential"],
                    "required": True,
                },
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "fetch",
                    "options": [
                        {"label": "Fetch Lead Details", "value": "fetch"},
                    ],
                },
                {
                    "name": "leadgen_id",
                    "label": "Leadgen ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $step.leadgen_id }}",
                    "condition": {"field": "operation", "value": "fetch"},
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "operation", "type": "string"},
                {"label": "id", "type": "string"},
                {"label": "form_id", "type": "string"},
                {"label": "field_data", "type": "array"},
                {"label": "created_time", "type": "string"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[LeadActionProperties]:
        return LeadActionProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")

        op = (self.props.operation or "").strip()
        if op not in LEAD_ACTION_OPS:
            return NodeResult(
                success=False,
                error=f"Unsupported operation '{op}'",
            )

        page_id = (self.props.page_id or "").strip()
        leadgen_id = (self.props.leadgen_id or "").strip()
        if not page_id:
            return NodeResult(success=False, error="page_id is required")
        if not leadgen_id:
            return NodeResult(success=False, error="leadgen_id is required")

        credential = find_credential(context.credentials, self.props.credential)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")
        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")

        token = page_token_by_page_id(data, page_id)
        if not token:
            return NodeResult(success=False, error="No page access token for this Page.")

        service = MetaService(context.db)
        try:
            response = await service.lead_fetch(token, leadgen_id)
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))

        return NodeResult(
            success=True,
            output_data={
                "operation": "fetch",
                "id": str(response.get("id") or leadgen_id),
                "form_id": str(response.get("form_id") or ""),
                "field_data": response.get("field_data") or [],
                "created_time": str(response.get("created_time") or ""),
                "response": response,
            },
        )
