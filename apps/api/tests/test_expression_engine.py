"""Tests for the JSONata expression engine wrapper (PR1 — scaffolding only).

These tests pin the behaviour of the thin resolver wrapper, not the JSONata
language itself. We cover: path traversal, bindings (`$var`), built-in
functions, error wrapping, and empty/missing values.
"""

from __future__ import annotations

import pytest

from apps.api.app.execution_engine.engine.expression_engine import (
    ExpressionError,
    JsonataResolver,
)


def test_simple_path_lookup() -> None:
    resolver = JsonataResolver({"foo": {"bar": "hello"}})
    assert resolver.evaluate("foo.bar") == "hello"


def test_array_index_access() -> None:
    resolver = JsonataResolver({"items": [{"name": "a"}, {"name": "b"}]})
    assert resolver.evaluate("items[1].name") == "b"


def test_missing_path_returns_none() -> None:
    resolver = JsonataResolver({"foo": {}})
    assert resolver.evaluate("foo.missing.deeper") is None


def test_builtin_function_sum() -> None:
    resolver = JsonataResolver({"items": [{"v": 1}, {"v": 2}, {"v": 3}]})
    assert resolver.evaluate("$sum(items.v)") == 6


def test_arithmetic_returns_number() -> None:
    resolver = JsonataResolver({"a": 10, "b": 4})
    assert resolver.evaluate("a + b") == 14
    assert resolver.evaluate("a * b - 1") == 39


def test_string_concat_via_ampersand() -> None:
    resolver = JsonataResolver({"first": "Ada", "last": "Lovelace"})
    assert resolver.evaluate('first & " " & last') == "Ada Lovelace"


def test_filter_expression() -> None:
    resolver = JsonataResolver(
        {
            "items": [
                {"name": "a", "active": True},
                {"name": "b", "active": False},
                {"name": "c", "active": True},
            ]
        }
    )
    assert resolver.evaluate("items[active=true].name") == ["a", "c"]


def test_binding_resolves_as_variable() -> None:
    resolver = JsonataResolver({"value": 5})
    result = resolver.evaluate("$multiplier * value", bindings={"multiplier": 3})
    assert result == 15


def test_binding_with_nested_dict() -> None:
    resolver = JsonataResolver({})
    result = resolver.evaluate("$step.status_code", bindings={"step": {"status_code": 200}})
    assert result == 200


def test_compile_error_raises_expression_error() -> None:
    resolver = JsonataResolver({"x": 1})
    with pytest.raises(ExpressionError) as exc_info:
        resolver.evaluate("foo..bar")  # double-dot is a syntax error
    assert exc_info.value.expression == "foo..bar"
    assert isinstance(exc_info.value.cause, BaseException)


def test_evaluation_error_raises_expression_error() -> None:
    # Calling a function that doesn't exist surfaces as an ExpressionError too.
    resolver = JsonataResolver({})
    with pytest.raises(ExpressionError):
        resolver.evaluate("$nonExistentFunction(1, 2)")


def test_default_empty_context() -> None:
    resolver = JsonataResolver()
    assert resolver.context == {}
    # Literal expressions still evaluate against an empty document.
    assert resolver.evaluate("1 + 2") == 3
