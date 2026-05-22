import json
from typing import Any

from jinja2 import BaseLoader, Environment
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

class JsonTransformProperties(BaseModel):
    template: Any

class JsonTransformNode(BaseNode[JsonTransformProperties]):
    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.json_transform",
            name="JSON Transform",
            category="logic",
            description="Reshape or extract fields from input data using a JSON template (supports Jinja2)",
            icon="FileJson",
            color="#3b82f6",
            inputs=1,
            outputs=1,
            properties=[
                {
                    "name": "template",
                    "label": "Output Template (JSON)",
                    "type": "json",
                    "required": True,
                    "placeholder": '{"name": "{{ input.name }}", "email": "{{ input.email }}"}'
                },
            ],
            allow_error=False,
        )

    @classmethod
    def get_properties_model(cls):
        return JsonTransformProperties

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            template_data = self.props.template
            if not template_data:
                return NodeResult(success=False, error="Template is required")

            if isinstance(template_data, (dict, list)):
                template_str = json.dumps(template_data)
            else:
                template_str = str(template_data)

            # Render jinja2 template with input_data as context
            env = Environment(loader=BaseLoader())
            tmpl = env.from_string(template_str)
            
            # Provide 'input' for convenience, and also spread input_data for direct access
            render_context = {
                "input": input_data,
                **input_data,
                "variables": context.variables,
            }
            
            rendered = tmpl.render(**render_context)

            try:
                result = json.loads(rendered)
            except json.JSONDecodeError:
                result = rendered  # Return as string if not valid JSON

            return NodeResult(success=True, output_data={"result": result})
        except Exception as e:
            logger.error(f"JsonTransformNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
