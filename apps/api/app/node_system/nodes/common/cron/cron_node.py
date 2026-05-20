from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class CronTriggerProperties(BaseModel):
    cron_expression: str = "0 9 * * 1-5"
    timezone: str = "UTC"


class CronTriggerNode(BaseNode[CronTriggerProperties]):
    @classmethod
    def get_properties_model(cls) -> type[CronTriggerProperties]:
        return CronTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.cron",
            name="Schedule Trigger",
            category="trigger",
            description="Run workflow on a cron schedule",
            icon="Clock",
            color="#8b5cf6",
            properties=[
                {
                    "name": "cron_expression",
                    "label": "Cron Expression",
                    "type": "string",
                    "required": True,
                    "default": "0 9 * * 1-5",
                    "placeholder": "0 9 * * 1-5",
                    "description": "Standard cron: minute hour day month weekday. Example: '0 9 * * 1-5' = 9am Mon-Fri",
                },
                {
                    "name": "timezone",
                    "label": "Timezone",
                    "type": "string",
                    "default": "UTC",
                    "placeholder": "UTC",
                    "mode": "advanced",
                    "description": "IANA timezone name (e.g. America/New_York, Europe/London)",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "fired_at", "type": "string"},
                {"label": "workflow_id", "type": "string"},
                {"label": "scheduled_time", "type": "string"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        return NodeResult(success=True, output_data=input_data)
