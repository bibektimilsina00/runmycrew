from __future__ import annotations

import json
from contextlib import suppress
from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class InputField(BaseModel):
    name: str
    label: str = ""
    type: str = "string"  # string | number | boolean | text
    required: bool = False


class HumanInputProperties(BaseModel):
    title: str = "Human Approval Required"
    description: str = ""
    fields: list[InputField] | str = Field(default_factory=list)
    timeoutHours: int = 72


class HumanInputNode(BaseNode[HumanInputProperties]):
    @classmethod
    def get_properties_model(cls) -> type[HumanInputProperties]:
        return HumanInputProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="logic.human_input",
            name="Human Input",
            category="logic",
            description="Pause workflow and wait for a human to provide input or approval.",
            icon="UserCheck",
            color="#f59e0b",
            properties=[
                {
                    "name": "title",
                    "label": "Title",
                    "type": "string",
                    "default": "Human Approval Required",
                },
                {
                    "name": "description",
                    "label": "Instructions",
                    "type": "string",
                    "placeholder": "Please review and approve...",
                },
                {
                    "name": "fields",
                    "label": "Input Fields",
                    "type": "json",
                    "default": [{"name": "approved", "label": "Approved?", "type": "boolean", "required": True}],
                    "description": "Fields the human must fill. Each: {name, label, type, required}.",
                },
                {
                    "name": "timeoutHours",
                    "label": "Timeout (hours)",
                    "type": "number",
                    "default": 72,
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "input", "type": "object"},
                {"label": "approved", "type": "boolean"},
            ],
            allow_error=True,
        )

    def _parse_fields(self) -> list[InputField]:
        raw = self.props.fields
        if isinstance(raw, str):
            try:
                raw = json.loads(raw)
            except json.JSONDecodeError:
                return []
        if not isinstance(raw, list):
            return []
        fields = []
        for item in raw:
            if isinstance(item, InputField):
                fields.append(item)
            elif isinstance(item, dict):
                with suppress(Exception):
                    fields.append(InputField(**item))
        return fields

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if context.pause is None:
            return NodeResult(
                success=False,
                error="Human Input node requires pause/resume support — not available in this context",
            )

        fields = self._parse_fields()
        resume_schema = {
            "title": self.props.title,
            "description": self.props.description,
            "fields": [f.model_dump() for f in fields],
            "timeoutHours": self.props.timeoutHours,
            "context": input_data,
        }

        # This raises PauseSignal — execution stops here until resumed
        await context.pause(resume_schema)

        # Never reached; resume_input becomes this node's output via _resume_from()
        return NodeResult(success=True, output_data={})
