"""Property-value dispatcher between JSONata (`=` prefix) and legacy ``{{...}}``.

This is the cutover point. The runner used to call
``TemplateResolver.resolve_properties(...)`` directly; PR5 wraps that with a
walker that routes each string value:

- Starts with ``=`` → JSONata expression. Strip the prefix, hand the rest to
  :class:`JsonataResolver`, return the typed result (number, string, dict,
  list — whatever the expression produced).
- Otherwise → existing :class:`TemplateResolver` interpolation, preserving
  every behaviour of the regex ``{{...}}`` engine word-for-word.

The two systems coexist throughout PR5–PR9 so we can migrate workflows
incrementally; PR10's cutover is what finally deletes the legacy resolver.

Errors are intentionally non-fatal here. A failed JSONata expression logs a
warning and resolves to ``None``, the same way a missing ``{{path}}`` does
today. A node author writing a broken expression should see a clean failure
in their output, not a 500 in the runner.
"""

from __future__ import annotations

from typing import Any

from apps.api.app.core.logger import get_logger
from apps.api.app.execution_engine.engine.expression_engine import (
    ExpressionError,
    JsonataResolver,
)
from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver

logger = get_logger(__name__)


def resolve_property_value(
    value: Any,
    jsonata_resolver: JsonataResolver,
    template_resolver: TemplateResolver,
) -> Any:
    """Resolve one property value (any shape) using the right engine per string.

    Dicts and lists are walked recursively. Non-string primitives pass
    through unchanged. Strings are dispatched by leading character: ``=``
    routes to JSONata; everything else routes to the legacy template
    resolver.
    """
    if isinstance(value, dict):
        return {
            k: resolve_property_value(v, jsonata_resolver, template_resolver)
            for k, v in value.items()
        }
    if isinstance(value, list):
        return [resolve_property_value(item, jsonata_resolver, template_resolver) for item in value]
    if isinstance(value, str):
        if value.startswith("="):
            expression = value[1:]
            try:
                return jsonata_resolver.evaluate(expression)
            except ExpressionError as exc:
                logger.warning("JSONata expression failed; resolving to None: %s", exc)
                return None
        return template_resolver.resolve(value)
    return value


def resolve_properties(
    properties: dict[str, Any],
    jsonata_resolver: JsonataResolver,
    template_resolver: TemplateResolver,
) -> dict[str, Any]:
    """Resolve every value in a node's properties dict via the dispatcher.

    Drop-in replacement for ``TemplateResolver.resolve_properties`` when the
    caller has both resolvers prepared.
    """
    return {
        k: resolve_property_value(v, jsonata_resolver, template_resolver)
        for k, v in properties.items()
    }
