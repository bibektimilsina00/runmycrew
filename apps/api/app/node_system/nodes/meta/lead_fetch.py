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


class LeadFetchProperties(BaseModel):
    credential: str | None = None
    page_id: str = ""  # Page that owns the form (used to look up the right page token)
    leadgen_id: str = ""


class LeadFetchNode(BaseNode[LeadFetchProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.meta.lead_fetch",
            name="Fetch Lead Ad Details",
            category="action",
            description=(
                "Resolve a Lead Ads `leadgen_id` (from the lead-submission "
                "trigger) into the full submitted form data. Requires the "
                "Page admin to have granted Lead Access to your Meta app."
            ),
            icon="ListChecks",
            color="#1877F2",
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
                    "name": "leadgen_id",
                    "label": "Leadgen ID",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{ $node('Lead Ad Submission').leadgen_id }}",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "id", "type": "string"},
                {"label": "created_time", "type": "string"},
                {"label": "ad_id", "type": "string"},
                {"label": "form_id", "type": "string"},
                {"label": "field_data", "type": "array"},
                {"label": "partner_name", "type": "string"},
                {"label": "response", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[LeadFetchProperties]:
        return LeadFetchProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.db is None:
            return NodeResult(success=False, error="Database session unavailable")
        if not self.props.leadgen_id:
            return NodeResult(success=False, error="leadgen_id is required")

        credential = find_credential(context.credentials, self.props.credential)
        if credential is None:
            return NodeResult(success=False, error="No Meta credential available")
        data = credential.get("data") if isinstance(credential, dict) else None
        if not isinstance(data, dict):
            return NodeResult(success=False, error="Meta credential is missing data")

        token = page_token_by_page_id(data, self.props.page_id)
        if not token:
            return NodeResult(success=False, error="No page access token for this Page.")

        service = MetaService(context.db)
        try:
            resp = await service.lead_fetch(token, self.props.leadgen_id)
        except Exception as exc:  # noqa: BLE001
            return NodeResult(success=False, error=str(exc))
        return NodeResult(
            success=True,
            output_data={
                "id": str(resp.get("id") or ""),
                "created_time": str(resp.get("created_time") or ""),
                "ad_id": str(resp.get("ad_id") or ""),
                "form_id": str(resp.get("form_id") or ""),
                "field_data": resp.get("field_data") or [],
                "partner_name": str(resp.get("partner_name") or ""),
                "response": resp,
            },
        )
