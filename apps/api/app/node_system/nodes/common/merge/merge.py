from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class MergeProperties(BaseModel):
    mode: str = "shallow"


class MergeNode(BaseNode[MergeProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.merge",
            name="Merge",
            category="logic",
            description="Merge multiple inputs into a single output object",
            icon="Merge",
            color="#8b5cf6",
            inputs=2,
            outputs=1,
            properties=[
                {
                    "name": "mode",
                    "label": "Merge Mode",
                    "type": "options",
                    "default": "shallow",
                    "options": [
                        {"label": "Shallow merge (last wins)", "value": "shallow"},
                        {"label": "Deep merge (coming soon)", "value": "deep"},
                    ],
                },
            ],
            allow_error=False,
        )

    @classmethod
    def get_properties_model(cls):
        return MergeProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            # The execution engine currently merges data from all incoming edges into input_data
            # before calling execute(). So MergeNode is effectively a passthrough that
            # signifies a convergence point in the graph.
            return NodeResult(success=True, output_data=input_data)
        except Exception as e:
            logger.error(f"MergeNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
