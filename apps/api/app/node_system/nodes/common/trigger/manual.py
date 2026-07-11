from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class TriggerProperties(BaseModel):
    """No config — the Manual trigger only starts the workflow."""


class TriggerNode(BaseNode[TriggerProperties]):
    """Bare manual trigger: fires the workflow, nothing else.

    Workflows that need typed user inputs at run time use the Form
    trigger (``trigger.form``) instead — this node deliberately has no
    configuration.
    """

    @classmethod
    def get_properties_model(cls) -> type[TriggerProperties]:
        return TriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.manual",
            name="Manual",
            category="trigger",
            description="Start the workflow manually. No configuration, no inputs.",
            icon="MousePointerClick",
            color="#10b981",
            properties=[],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "input_data", "type": "object"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Pass through whatever the run carried (usually {}), so callers
        # that inject data programmatically still reach downstream nodes.
        return NodeResult(
            success=True, output_data=input_data if isinstance(input_data, dict) else {}
        )
