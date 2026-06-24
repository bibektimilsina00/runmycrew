from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.logic.code.sandbox import execute_code


class CodeProperties(BaseModel):
    language: str = "python"
    code: str = ""
    timeout: int = 30


class CodeNode(BaseNode[CodeProperties]):
    @classmethod
    def get_properties_model(cls) -> type[CodeProperties]:
        return CodeProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.code",
            name="Code",
            category="logic",
            description="Run Python or JavaScript code. Access input data via `input`, set `output` to return data.",
            icon="Code2",
            color="#f59e0b",
            properties=[
                {
                    "name": "language",
                    "label": "Language",
                    "type": "options",
                    "default": "python",
                    "options": [
                        {"label": "Python", "value": "python"},
                        {"label": "JavaScript", "value": "javascript"},
                    ],
                },
                {
                    "name": "code",
                    "label": "Code",
                    "type": "code",
                    "required": True,
                    "default": "# Access previous node data via `input`\n# Set `output` to pass data to the next node\noutput = {'result': input}",
                    "description": "Python: set `output` dict. Use `{{$node.output.field}}` to reference previous nodes.",
                    "condition": {"field": "language", "value": "python"},
                },
                {
                    "name": "code",
                    "label": "Code",
                    "type": "code",
                    "required": True,
                    "default": "// Access previous node data via `input`\n// Set `output` to pass data to the next node\noutput = { result: input };",
                    "description": "JavaScript: set `output` object. Use {{$node.output.field}} to reference previous nodes.",
                    "condition": {"field": "language", "value": "javascript"},
                },
                {
                    "name": "timeout",
                    "label": "Timeout (seconds)",
                    "type": "number",
                    "default": 30,
                    "mode": "advanced",
                    "description": "Maximum execution time. Default 30s.",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "output", "type": "object"},
                {"label": "logs", "type": "array"},
                {"label": "language", "type": "string"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.code.strip():
            return NodeResult(success=False, error="Code is required.")
        if self.props.language not in ("python", "javascript"):
            return NodeResult(success=False, error=f"Unsupported language: {self.props.language}")

        timeout = max(1, min(self.props.timeout, 120))
        try:
            output, logs = await execute_code(
                self.props.language, self.props.code, input_data, timeout
            )
        except TimeoutError as e:
            return NodeResult(success=False, error=str(e))
        except Exception as e:
            return NodeResult(success=False, error=str(e))

        return NodeResult(
            success=True,
            output_data={
                "output": output,
                "logs": logs,
                "language": self.props.language,
                **output,  # spread output fields so downstream can reference them directly
            },
        )
