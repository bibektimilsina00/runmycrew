from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class TriggerProperties(BaseModel):
    startWorkflow: str = "manual"
    input_schema: list[dict[str, Any]] = []


class TriggerNode(BaseNode[TriggerProperties]):
    @classmethod
    def get_properties_model(cls) -> type[TriggerProperties]:
        return TriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.manual",
            name="Start",
            category="trigger",
            description="Initiate workflow execution manually",
            icon="Play",
            color="#10b981",
            properties=[
                {
                    "name": "startWorkflow",
                    "label": "Start Workflow",
                    "type": "string",
                    "default": "manual",
                },
                {
                    "name": "input_schema",
                    "label": "Input Schema",
                    "type": "schema",
                    "default": [],
                    "mode": "advanced",
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "input_data", "type": "object"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Starter nodes receive the initial workflow input (from context or input_data)
        return NodeResult(
            success=True,
            output_data=input_data,
        )
