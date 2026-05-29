from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class SetVariableProperties(BaseModel):
    key: str
    value: Any


class SetVariableNode(BaseNode[SetVariableProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.set_variable",
            name="Set Variable",
            category="logic",
            description="Store a value in workflow variables for use by downstream nodes",
            icon="Variable",
            color="#ec4899",
            inputs=1,
            outputs=1,
            properties=[
                {
                    "name": "key",
                    "label": "Variable Name",
                    "type": "string",
                    "required": True,
                    "placeholder": "myVariable",
                },
                {
                    "name": "value",
                    "label": "Value",
                    "type": "string",
                    "required": True,
                    "placeholder": "Enter value or use {{ interpolation }}",
                },
            ],
            allow_error=False,
        )

    @classmethod
    def get_properties_model(cls):
        return SetVariableProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            key = self.props.key
            value = self.props.value

            if not key:
                return NodeResult(success=False, error="Variable name (key) is required")

            # Update context variables
            # These are shared across the entire execution
            context.variables[key] = value

            return NodeResult(
                success=True,
                output_data={
                    "key": key,
                    "value": value,
                    "variables": context.variables,
                    **input_data,
                },
            )
        except Exception as e:
            logger.error(f"SetVariableNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
