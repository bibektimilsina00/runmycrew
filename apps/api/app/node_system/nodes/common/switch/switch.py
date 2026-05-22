from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

class SwitchProperties(BaseModel):
    field: str
    cases: list[dict[str, Any]] | None = None

class SwitchNode(BaseNode[SwitchProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.switch",
            name="Switch",
            category="logic",
            description="Route to different branches based on a field value",
            icon="Split",
            color="#f59e0b",
            inputs=1,
            outputs=2, # Static 2 for now
            properties=[
                {
                    "name": "field",
                    "label": "Field to Check",
                    "type": "string",
                    "required": True,
                    "placeholder": "status"
                },
                {
                    "name": "cases",
                    "label": "Cases",
                    "type": "json",
                    "required": False,
                    "placeholder": '[{"value":"success","label":"Success"},{"value":"error","label":"Error"}]'
                },
            ],
            allow_error=False,
        )

    @classmethod
    def get_properties_model(cls):
        return SwitchProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            field = self.props.field
            if not field:
                return NodeResult(success=False, error="Field to check is required")

            # Support dot notation for nested fields
            field_value = input_data
            for part in field.split("."):
                if isinstance(field_value, dict):
                    field_value = field_value.get(part)
                else:
                    field_value = None
                    break

            # The branch selection happens in the WorkflowRunner based on 'branch' field in output_data
            return NodeResult(
                success=True,
                output_data={
                    "matched_value": field_value,
                    "branch": str(field_value),
                    **input_data,
                },
            )
        except Exception as e:
            logger.error(f"SwitchNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
