"""Consolidated Lead Ads trigger.

Replaces `lead_submission_trigger`. Currently only the `submission`
event is supported (Meta only delivers `leadgen` events for Lead Ads);
the dropdown leaves room to add future Lead-Ads events (form changes,
column updates, etc.) without re-introducing a per-event node.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.meta._helpers import require_webhook_payload

LEAD_EVENT_TYPES: tuple[str, ...] = ("submission",)


class LeadTriggerProperties(BaseModel):
    event_type: str = "submission"
    page_id: str = ""
    credential: str | None = None
    form_id: str | None = Field(
        default=None,
        description="Optional — only fire for this specific Lead Ads form id.",
    )


class LeadTriggerNode(BaseNode[LeadTriggerProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.meta.lead",
            name="Lead Ads",
            category="trigger",
            description=(
                "Fires when a user submits a Facebook/Instagram Lead Ad form "
                "for the connected Page. The webhook payload only carries the "
                "leadgen_id — pair with the Lead Ads action node (fetch) to "
                "pull the full form data."
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
                    "name": "event_type",
                    "label": "Event",
                    "type": "options",
                    "default": "submission",
                    "options": [
                        {"label": "Form Submission", "value": "submission"},
                    ],
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
                    "condition": {"field": "event_type", "value": "submission"},
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "event_type", "type": "string"},
                {"label": "leadgen_id", "type": "string"},
                {"label": "form_id", "type": "string"},
                {"label": "ad_id", "type": "string"},
                {"label": "adgroup_id", "type": "string"},
                {"label": "page_id", "type": "string"},
                {"label": "created_time", "type": "string"},
                {"label": "received_at", "type": "string"},
                {"label": "payload", "type": "object"},
            ],
            credential_type="meta_oauth",
        )

    @classmethod
    def get_properties_model(cls) -> type[LeadTriggerProperties]:
        return LeadTriggerProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        guard = require_webhook_payload(input_data, trigger_label="Lead Ads")
        if guard is not None:
            return guard

        event_type = (self.props.event_type or "").strip()
        if event_type not in LEAD_EVENT_TYPES:
            return NodeResult(
                success=False,
                error=f"Unsupported event_type '{event_type}'",
            )

        value = input_data.get("value") or {}
        received_at = str(input_data.get("received_at") or "")
        form_actual = str(value.get("form_id") or "")

        wanted_form = (self.props.form_id or "").strip()
        if wanted_form and wanted_form != form_actual:
            return NodeResult(success=True, output_data={"skipped": "form_id mismatch"})

        return NodeResult(
            success=True,
            output_data={
                "event_type": "submission",
                "leadgen_id": str(value.get("leadgen_id") or ""),
                "form_id": form_actual,
                "ad_id": str(value.get("ad_id") or ""),
                "adgroup_id": str(value.get("adgroup_id") or ""),
                "page_id": str(value.get("page_id") or ""),
                "created_time": str(value.get("created_time") or ""),
                "received_at": received_at,
                "payload": value,
            },
        )
