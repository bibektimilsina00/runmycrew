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
    {"label": "Object", "value": "object"},
    {"label": "Array", "value": "array"},
    {"label": "Files", "value": "files"},
]

_DEFAULT_INPUTS: list[dict[str, Any]] = [
    {"name": "input1", "type": "string", "value": ""},
]


class FormTriggerProperties(BaseModel):
    # User-defined input schema. The inspector renders this as the
    # editable list of fields — each row has name + type + default value.
    inputs: list[dict[str, Any]] = Field(
        # Ships with one ready-to-edit row so a fresh node doesn't open
        # a totally blank inputs panel.
        default_factory=lambda: [dict(row) for row in _DEFAULT_INPUTS]
    )


class FormTriggerNode(BaseNode[FormTriggerProperties]):
    """Form trigger: a typed input schema the user fills at run time.

    Each entry in ``inputs`` becomes a top-level field on this node's
    ``output_data``, so downstream nodes can reach the value via
    ``{{ $step.<name> }}`` or ``{{ $node('Form').<name> }}``. Run in
    the editor opens a form built from this schema; submitted values
    arrive through ``input_data`` and override the defaults.
    """

    @classmethod
    def get_properties_model(cls) -> type[FormTriggerProperties]:
        return FormTriggerProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="trigger.form",
            name="Form",
            category="trigger",
            description="Start the workflow from a form — define fields, fill them at run time.",
            icon="ClipboardList",
            color="#10b981",
            properties=[
                {
                    # Virtual, read-only public link (same renderer the
                    # Chat App trigger uses) — the hosted form page URL.
                    "name": "app_url",
                    "label": "Public link",
                    "type": "app-link",
                    "visibility": "user-only",
                },
                {
                    "name": "inputs",
                    "label": "Fields",
                    "type": "collection",
                    "default": [dict(row) for row in _DEFAULT_INPUTS],
                    "typeOptions": {
                        "multipleValues": True,
                        "addButtonText": "Add field",
                        # CollectionRenderer reads these to auto-fill the
                        # `name` sub-field with `input1`, `input2`, …
                        # each time the user adds a row.
                        "autoIncrementField": "name",
                        "autoIncrementPrefix": "input",
                    },
                    "properties": [
                        {
                            "name": "name",
                            "label": "Name",
                            "type": "string",
                            "placeholder": "input1",
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
                # Fallback when the user hasn't added any fields yet;
                # once `inputs` is populated, `dynamic_outputs_from`
                # exposes the user-defined names instead.
                {"label": "input_data", "type": "object"},
            ],
            dynamic_outputs_from="inputs",
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        # Build the output dict from the user-defined schema, coercing
        # each default to the declared type so downstream `{{ $step.x }}`
        # references get a real number/bool/object instead of a stringy
        # one. Anything the run form passes in via ``input_data`` wins.
        #
        # Defensive: rows with an empty or whitespace-only `name` (user
        # added the row but never typed) and rows whose name collides
        # with one already used are auto-recovered to `inputN` instead
        # of being silently dropped.
        out: dict[str, Any] = {}
        used: set[str] = set()
        for idx, row in enumerate(self.props.inputs or [], start=1):
            raw_name = row.get("name")
            name = (raw_name if isinstance(raw_name, str) else "").strip()
            if not name or name in used:
                candidate = f"input{idx}"
                bump = idx
                while candidate in used:
                    bump += 1
                    candidate = f"input{bump}"
                name = candidate
            used.add(name)
            declared_type = (row.get("type") or "string").lower()
            raw_value = row.get("value")
            out[name] = _coerce(raw_value, declared_type)
        if isinstance(input_data, dict):
            # Hosted form submissions arrive wrapped as trigger_data
            # {message, session_id, form_data, …}; the field values live
            # in form_data. Editor runs pass the values directly.
            form_data = input_data.get("form_data")
            if isinstance(form_data, dict) and form_data:
                out.update(form_data)
            else:
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
        # An unset default stays unset — the run form can still fill it
        # in via ``input_data`` overrides.
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

    # "json" is the legacy alias used before the type catalog gained the
    # object / array / files split — coerce identically.
    if declared_type in {"object", "array", "files", "json"}:
        if isinstance(value, dict | list):
            return value
        import json

        try:
            return json.loads(str(value))
        except (TypeError, ValueError, json.JSONDecodeError):
            return value

    return value
