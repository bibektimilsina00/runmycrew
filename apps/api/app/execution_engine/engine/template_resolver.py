from __future__ import annotations

import json
import re
from typing import Any

from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

# Matches {{node_id.output.field}} or {{node_id.output.nested.field}}
TEMPLATE_PATTERN = re.compile(r"\{\{([^}]+)\}\}")

# Comparison pattern: {{path}} OP value  e.g. {{variables.count}} < 10
_CMP_PATTERN = re.compile(r"^\s*\{\{([^}]+)\}\}\s*(==|!=|<=|>=|<|>)\s*(.+?)\s*$")


class TemplateResolver:
    """Resolves {{node_id.output.field}} and {{env.KEY}} templates against execution context."""

    def __init__(
        self,
        node_outputs: dict[str, dict[str, Any]],
        trigger_data: dict[str, Any],
        variables: dict[str, Any],
        env: dict[str, str] | None = None,
        secrets: dict[str, str] | None = None,
        loop_data: dict[str, Any] | None = None,
    ):
        self._context = {
            "trigger": {"output": trigger_data},
            "variables": variables,
            "env": env or {},
            "secrets": secrets or {},
            "loop": loop_data
            or {},  # {{loop.item}}, {{loop.index}}, {{loop.total}}, {{loop.value}}
            **{node_id: {"output": output} for node_id, output in node_outputs.items()},
        }

    def resolve_properties(self, properties: dict[str, Any]) -> dict[str, Any]:
        """Resolve all template strings in a node's properties dict recursively."""
        return self._resolve_recursive(properties)

    def evaluate_condition(self, condition: str) -> bool:
        """Evaluate a condition expression. Supports:
        - {{path}} < / > / == / != / <= / >= value
        - {{path}} alone (truthy check)
        - Literal 'true'/'false'
        """
        condition = condition.strip()
        if condition.lower() == "true":
            return True
        if condition.lower() == "false":
            return False

        # Try comparison pattern first: {{path}} OP literal
        m = _CMP_PATTERN.match(condition)
        if m:
            path, op, raw_rhs = m.group(1).strip(), m.group(2), m.group(3).strip()
            lhs = self._resolve_path(path)
            # Parse RHS as JSON value (handles numbers, booleans, strings)
            try:
                rhs = json.loads(raw_rhs)
            except json.JSONDecodeError:
                rhs = raw_rhs.strip("\"'")  # treat as bare string
            try:
                if op == "==":
                    return lhs == rhs
                if op == "!=":
                    return lhs != rhs
                if op == "<":
                    return float(lhs) < float(rhs)  # type: ignore[arg-type]
                if op == ">":
                    return float(lhs) > float(rhs)  # type: ignore[arg-type]
                if op == "<=":
                    return float(lhs) <= float(rhs)  # type: ignore[arg-type]
                if op == ">=":
                    return float(lhs) >= float(rhs)  # type: ignore[arg-type]
            except (TypeError, ValueError):
                return False

        # Fallback: resolve as template and check truthiness
        resolved = self._resolve_string(condition)
        if isinstance(resolved, bool):
            return resolved
        if isinstance(resolved, (int, float)):
            return resolved != 0
        if isinstance(resolved, str):
            return resolved.lower() not in ("", "false", "0", "null", "none")
        return bool(resolved)

    def _resolve_recursive(self, value: Any) -> Any:
        if isinstance(value, str):
            return self._resolve_string(value)
        elif isinstance(value, dict):
            return {k: self._resolve_recursive(v) for k, v in value.items()}
        elif isinstance(value, list):
            return [self._resolve_recursive(item) for item in value]
        return value

    def _resolve_string(self, template: str) -> Any:
        matches = TEMPLATE_PATTERN.findall(template)
        if not matches:
            return template

        # If the entire string is exactly one template "{{path}}", preserve the resolved type
        # (e.g. if it resolves to a number, return a number, not a string "42")
        if len(matches) == 1 and template.strip() == f"{{{{{matches[0]}}}}}":
            return self._resolve_path(matches[0].strip())

        # If it's a mix of text and templates, always return a string
        def replace_match(match: re.Match) -> str:
            path = match.group(1).strip()
            resolved = self._resolve_path(path)
            if resolved is None:
                return ""
            if isinstance(resolved, (dict, list)):
                return json.dumps(resolved)
            return str(resolved)

        return TEMPLATE_PATTERN.sub(replace_match, template)

    def _resolve_path(self, path: str) -> Any:
        """Resolve a dot-path like 'node_1.output.body.id'."""
        path = path.strip()
        current = self._resolve_node_output_path(path)
        if current is not None:
            return current

        parts = path.split(".")
        current = self._context

        for part in parts:
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    logger.warning(f"Could not resolve index '{part}' in path '{path}'")
                    return None
            else:
                logger.warning(f"Could not resolve part '{part}' in path '{path}'")
                return None

            if current is None:
                return None

        return current

    def _resolve_node_output_path(self, path: str) -> Any:
        """Resolve paths whose node IDs may contain dots.

        Node IDs are generated from node type prefixes, for example
        ``action.http_request-1778949244013``. Splitting the whole path on
        dots treats ``action`` as the context key and loses the real node ID,
        so node output paths are split on the explicit ``.output`` marker.
        """
        output_marker = ".output"
        if output_marker not in path:
            return None

        node_id, output_path = path.split(output_marker, 1)
        node_context = self._context.get(node_id)
        if not isinstance(node_context, dict) or "output" not in node_context:
            return None

        current: Any = node_context["output"]
        if not output_path:
            return current

        output_path = output_path.removeprefix(".")
        if not output_path:
            return current

        for part in output_path.split("."):
            if isinstance(current, dict):
                current = current.get(part)
            elif isinstance(current, list):
                try:
                    current = current[int(part)]
                except (ValueError, IndexError):
                    logger.warning(f"Could not resolve index '{part}' in path '{path}'")
                    return None
            else:
                logger.warning(f"Could not resolve part '{part}' in path '{path}'")
                return None

            if current is None:
                return None

        return current
