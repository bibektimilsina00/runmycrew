from typing import Any

from pydantic import BaseModel, Field

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

# Type catalog exposed to the inspector — also the universe of values the
# coercer below understands. Keep in lockstep with the runtime coercion.
_INPUT_TYPE_OPTIONS: list[dict[str, str]] = [
    {"label": "String", "value": "string"},
    {"label": "Number", "value": "number"},
    {"label": "Boolean", "value": "boolean"},
    {"label": "JSON", "value": "json"},
]


class TriggerProperties(BaseModel):
    startWorkflow: str = "manual"
    # User-defined input schema. The inspector renders this as the
    # editable list of fields shown in the design mock — each row has
    # name + type + description + default value.
    inputs: list[dict[str, Any]] = Field(default_factory=list)


class TriggerNode(BaseNode[TriggerProperties]):
    """Manual "Start" trigger that lets users define a typed input schema.

    Each entry in ``inputs`` becomes a top-level field on this node's
    ``output_data``, so downstream nodes can reach the value via
    ``{{ $step.<name> }}`` or ``{{ $node('Start').<name> }}``. The
    workflow's "Run" dialog can override defaults by passing the same
    field names through ``input_data`` at execution time.
    """

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
                    "visibility": "hidden",
                },
                {
                    "name": "inputs",
                    "label": "Inputs",
                    "type": "collection",
                    "default": [],
                    "typeOptions": {
                        "multipleValues": True,
                        "addButtonText": "Add input",
                    },
                    "properties": [
                        {
                            "name": "name",
                            "label": "Name",
                            "type": "string",
                            "placeholder": "firstName",
                            "required": True,
                        },
                        {
                            "name": "type",
                            "label": "Type",
                            "type": "options",
                            "default": "string",
                            "options": _INPUT_TYPE_OPTIONS,
                        },
                        {
                            "name": "description",
                            "label": "Description",
                            "type": "string",
                            "placeholder": "Describe this field",
                        },
                        {
                            "name": "value",
                            "label": "Value",
                            "type": "string",
                            "placeholder": "Enter default value",
                        },
                    ],
                },
            ],
            inputs=0,
            outputs=1,
            outputs_schema=[
                {"label": "input_data", "type": "object"},
            ],
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Build the output dict from the user-defined schema, coercing
        # each default to the declared type so downstream `{{ $step.x }}`
        # references get a real number/bool/object instead of a stringy
        # one. Anything that the workflow run-dialog passes in via
        # ``input_data`` wins — that's how "run with values" overrides
        # the defaults set in the editor.
        out: dict[str, Any] = {}
        for row in self.props.inputs or []:
            name = (row.get("name") or "").strip()
            if not name:
                continue
            declared_type = (row.get("type") or "string").lower()
            raw_value = row.get("value")
            out[name] = _coerce(raw_value, declared_type)
        if isinstance(input_data, dict):
            out.update(input_data)
        return NodeResult(success=True, output_data=out)


def _coerce(value: Any, declared_type: str) -> Any:
    """Best-effort cast of a user-entered default into the declared type.

    Returns the value untouched when it's already the right shape or
    when conversion fails — runtime templates can still consume the raw
    string in that case, which is friendlier than a hard failure on
    workflow start.
    """
    if value is None or value == "":
        # An unset default stays unset — the workflow run dialog can
        # still fill it in via ``input_data`` overrides.
        if declared_type == "string":
            return ""
        return None

    if declared_type == "string":
        return value if isinstance(value, str) else str(value)

    if declared_type == "number":
        if isinstance(value, int | float) and not isinstance(value, bool):
            return value
        try:
            text = str(value).strip()
            return float(text) if "." in text else int(text)
        except (TypeError, ValueError):
            return value

    if declared_type == "boolean":
        if isinstance(value, bool):
            return value
        text = str(value).strip().lower()
        if text in {"true", "1", "yes", "y", "on"}:
            return True
        if text in {"false", "0", "no", "n", "off"}:
            return False
        return value

    if declared_type == "json":
        if isinstance(value, dict | list):
            return value
        import json

        try:
            return json.loads(str(value))
        except (TypeError, ValueError, json.JSONDecodeError):
            return value

    return value
