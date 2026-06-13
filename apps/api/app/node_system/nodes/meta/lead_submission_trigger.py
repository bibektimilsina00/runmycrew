from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class LeadSubmissionTriggerProperties(BaseModel):
    page_id: str = ""
    form_id: str | None = Field(
        default=None,
        description="Optional — only fire for this specific Lead Ads form id.",
    )


class LeadSubmissionTriggerNode(BaseNode[LeadSubmissionTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.lead_submission",
            name="Lead Ad Submission",
            category="trigger",
            description=(
                "Fires when a user submits a Facebook/Instagram Lead Ad form "
                "for the connected Page. Webhook payload only carries the "
                "leadgen_id — pair with `action.meta.lead_fetch` to pull "
                "the full lead details."
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
                    "name": "form_id",
                    "label": "Form ID (optional)",
                    "type": "string",
                    "placeholder": "98765432101234",
                    "description": (
                        "Restrict the trigger to one form. The Page admin must "
                        "grant Lead Access to your Meta app via Page Settings — "
                        "this step is NOT automated by OAuth."
                    ),
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "leadgen_id", "type": "string"},
                {"label": "form_id", "type": "string"},
                {"label": "ad_id", "type": "string"},
                {"label": "adgroup_id", "type": "string"},
                {"label": "page_id", "type": "string"},
                {"label": "created_time", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[LeadSubmissionTriggerProperties]:
        return LeadSubmissionTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        value = input_data.get("value") or {}
        form_actual = str(value.get("form_id") or "")

        wanted_form = (self.props.form_id or "").strip()
        if wanted_form and wanted_form != form_actual:
            return NodeResult(success=True, output_data={"skipped": "form_id mismatch"})

        return NodeResult(
            success=True,
            output_data={
                "leadgen_id": str(value.get("leadgen_id") or ""),
                "form_id": form_actual,
                "ad_id": str(value.get("ad_id") or ""),
                "adgroup_id": str(value.get("adgroup_id") or ""),
                "page_id": str(value.get("page_id") or ""),
                "created_time": str(value.get("created_time") or ""),
                "payload": value,
            },
        )
