"""Tests for str-field coercion in BaseNode.validate_properties.

JSONata expressions resolve to typed values — `=2` becomes the int `2`,
`=true` becomes the bool `True`. Node properties declared as `str`
should accept those without making the user think about types.
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult


class _StrProps(BaseModel):
    name: str = "default"
    age: int = 0
    label: str | None = None
    description: str | int = ""


class _StrNode(BaseNode[_StrProps]):
    @classmethod
    def get_properties_model(cls) -> type[_StrProps]:
        return _StrProps

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="test.str",
            name="Str",
            category="action",
            description="",
            icon="x",
            properties=[],
            inputs=0,
            outputs=0,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        return NodeResult(success=True)


def test_int_value_for_str_field_is_coerced() -> None:
    node = _StrNode(node_id="n1", properties={"name": 2})
    assert node.props.name == "2"


def test_float_value_for_str_field_is_coerced() -> None:
    node = _StrNode(node_id="n1", properties={"name": 3.14})
    assert node.props.name == "3.14"


def test_bool_value_for_str_field_is_coerced_to_lowercase() -> None:
    node = _StrNode(node_id="n1", properties={"name": True})
    assert node.props.name == "true"
    node2 = _StrNode(node_id="n2", properties={"name": False})
    assert node2.props.name == "false"


def test_optional_str_field_coerces_too() -> None:
    node = _StrNode(node_id="n1", properties={"label": 42})
    assert node.props.label == "42"


def test_none_for_optional_str_passes_through() -> None:
    node = _StrNode(node_id="n1", properties={"label": None})
    assert node.props.label is None


def test_int_field_is_not_touched() -> None:
    # Non-str fields go through Pydantic's normal validation untouched.
    node = _StrNode(node_id="n1", properties={"age": "42"})
    assert node.props.age == 42  # Pydantic coerces "42" → 42 for `int`


def test_union_with_non_str_branches_left_alone() -> None:
    # `str | int` accepts both — we don't pre-coerce because the user
    # genuinely meant either type.
    node = _StrNode(node_id="n1", properties={"description": 42})
    assert node.props.description == 42


def test_missing_property_uses_default() -> None:
    # No coercion when the key isn't there; Pydantic default kicks in.
    node = _StrNode(node_id="n1", properties={})
    assert node.props.name == "default"
