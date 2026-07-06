from __future__ import annotations

import json
import re
from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

# Verification ladder: mode -> level (L1 deterministic / L2 rule / L3 field-truth).
MODE_LEVEL = {"expression": 1, "rule": 2, "http": 3, "code": 3}


class VerifyProperties(BaseModel):
    mode: str = "expression"  # expression | rule | http | code
    # Subject for rule mode (engine pre-resolves templates in props).
    content: str = ""
    # L1 template boolean expression.
    expression: str = ""
    # Rule mode.
    ruleType: str = "contains"  # contains | not_contains | regex | required_keys
    pattern: str = ""
    requiredKeys: str = ""  # comma-separated
    # HTTP mode.
    url: str = ""
    method: str = "GET"
    expectedStatus: str = "2xx"  # "2xx" | "200" | "200-299"
    bodyContains: str = ""
    # Code mode (L3) — python assertion body.
    code: str = ""


class VerifyNode(BaseNode[VerifyProperties]):
    @classmethod
    def get_properties_model(cls) -> type[VerifyProperties]:
        return VerifyProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="ai.verify",
            name="Verify",
            category="ai",
            description=(
                "Objective verification checker for a crew loop. Runs a deterministic "
                "L1-L3 check (expression / rule / http / code) and emits a "
                "{passed, feedback} verdict the Agent Crew orchestrator reads."
            ),
            icon="CheckCheck",
            color="#3fb98b",
            properties=[
                {
                    "name": "mode",
                    "label": "Mode",
                    "type": "options",
                    "default": "expression",
                    "options": [
                        {"label": "Expression (L1)", "value": "expression"},
                        {"label": "Rule (L2)", "value": "rule"},
                        {"label": "HTTP (L3)", "value": "http"},
                        {"label": "Code (L3)", "value": "code"},
                    ],
                    "description": "Verification ladder level. Deterministic to field-truth.",
                },
                {
                    "name": "expression",
                    "label": "Expression",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{$json.status}} == success",
                    "condition": {"field": "mode", "value": "expression"},
                    "description": "Template boolean. Passes when it resolves truthy.",
                },
                {
                    "name": "content",
                    "label": "Subject",
                    "type": "string",
                    "required": True,
                    "placeholder": "{{$previous_node.output.text}}",
                    "condition": {"field": "mode", "value": "rule"},
                    "description": "Text (or JSON) the rule is applied to.",
                },
                {
                    "name": "ruleType",
                    "label": "Rule Type",
                    "type": "options",
                    "default": "contains",
                    "options": [
                        {"label": "Contains", "value": "contains"},
                        {"label": "Does Not Contain", "value": "not_contains"},
                        {"label": "Regex", "value": "regex"},
                        {"label": "Required Keys", "value": "required_keys"},
                    ],
                    "condition": {"field": "mode", "value": "rule"},
                },
                {
                    "name": "pattern",
                    "label": "Pattern",
                    "type": "string",
                    "placeholder": "expected substring or regex",
                    "condition": {"field": "mode", "value": "rule"},
                },
                {
                    "name": "requiredKeys",
                    "label": "Required Keys",
                    "type": "string",
                    "placeholder": "id, name, email",
                    "condition": {"field": "mode", "value": "rule"},
                    "description": "Comma-separated keys that must exist in the JSON subject.",
                },
                {
                    "name": "url",
                    "label": "URL",
                    "type": "string",
                    "required": True,
                    "condition": {"field": "mode", "value": "http"},
                },
                {
                    "name": "method",
                    "label": "Method",
                    "type": "options",
                    "default": "GET",
                    "options": [
                        {"label": "GET", "value": "GET"},
                        {"label": "POST", "value": "POST"},
                        {"label": "PUT", "value": "PUT"},
                        {"label": "DELETE", "value": "DELETE"},
                        {"label": "PATCH", "value": "PATCH"},
                        {"label": "HEAD", "value": "HEAD"},
                    ],
                    "condition": {"field": "mode", "value": "http"},
                },
                {
                    "name": "expectedStatus",
                    "label": "Expected Status",
                    "type": "string",
                    "default": "2xx",
                    "placeholder": "2xx | 200 | 200-299",
                    "condition": {"field": "mode", "value": "http"},
                },
                {
                    "name": "bodyContains",
                    "label": "Body Contains",
                    "type": "string",
                    "required": False,
                    "condition": {"field": "mode", "value": "http"},
                    "description": "Optional substring the response body must contain.",
                },
                {
                    "name": "code",
                    "label": "Code",
                    "type": "string",
                    "required": True,
                    "placeholder": "output = {'passed': input['count'] > 0}",
                    "condition": {"field": "mode", "value": "code"},
                    "description": (
                        "Python run in the sandbox with `input`. Passes when `output` "
                        "is truthy (or `output['passed']` is truthy)."
                    ),
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "passed", "type": "boolean"},
                {"label": "feedback", "type": "string"},
                {"label": "level", "type": "number"},
                {"label": "mode", "type": "string"},
                {"label": "average", "type": "number"},
                {"label": "details", "type": "object"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        mode = (self.props.mode or "expression").strip()
        level = MODE_LEVEL.get(mode, 1)
        details: dict[str, Any] = {}

        try:
            if mode == "expression":
                passed, feedback, details = self._verify_expression(input_data, context)
            elif mode == "rule":
                passed, feedback, details = self._verify_rule()
            elif mode == "http":
                passed, feedback, details = await self._verify_http()
            elif mode == "code":
                passed, feedback, details = await self._verify_code(input_data)
            else:
                passed = False
                feedback = f"Unknown verify mode `{mode}`."
        except Exception as e:
            # Check-infra failure (bad url, sandbox error, etc). Don't hard-fail —
            # the crew loop needs a verdict it can iterate on.
            logger.warning(f"VerifyNode ({mode}) check failed: {e}")
            passed = False
            feedback = str(e)
            details = {"error": str(e)}

        average = 100.0 if passed else 0.0
        return NodeResult(
            success=True,
            output_data={
                "passed": passed,
                "feedback": feedback,
                "level": level,
                "mode": mode,
                "average": average,
                "details": details,
            },
        )

    # --- L1: deterministic expression ---------------------------------------
    def _verify_expression(
        self, input_data: dict[str, Any], context: NodeContext
    ) -> tuple[bool, str, dict[str, Any]]:
        from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver

        expr = self.props.expression
        resolver = TemplateResolver(
            node_outputs={"json": input_data},
            trigger_data=input_data,
            variables=context.variables,
            env=getattr(context, "env", {}),
        )
        passed = bool(resolver.evaluate_condition(expr))
        feedback = f"L1 assertion `{expr}` -> {passed}"
        return passed, feedback, {"expression": expr}

    # --- L2: rule -----------------------------------------------------------
    def _verify_rule(self) -> tuple[bool, str, dict[str, Any]]:
        subject = self.props.content or ""
        rule_type = (self.props.ruleType or "contains").strip()
        pattern = self.props.pattern or ""
        details: dict[str, Any] = {"ruleType": rule_type}

        if rule_type == "contains":
            passed = pattern in subject
            feedback = f"L2 rule `contains '{pattern}'` -> {passed}"
        elif rule_type == "not_contains":
            passed = pattern not in subject
            feedback = f"L2 rule `not_contains '{pattern}'` -> {passed}"
        elif rule_type == "regex":
            passed = bool(re.search(pattern, subject))
            feedback = f"L2 rule `regex /{pattern}/` -> {passed}"
        elif rule_type == "required_keys":
            keys = [k.strip() for k in (self.props.requiredKeys or "").split(",") if k.strip()]
            parsed: Any = None
            try:
                parsed = json.loads(subject)
            except (json.JSONDecodeError, TypeError):
                parsed = None
            if isinstance(parsed, dict):
                missing = [k for k in keys if k not in parsed]
            else:
                missing = list(keys)
            passed = not missing
            details["missing_keys"] = missing
            feedback = f"L2 rule `required_keys {keys}` -> {passed}" + (
                f" (missing: {missing})" if missing else ""
            )
        else:
            passed = False
            feedback = f"Unknown rule type `{rule_type}`."

        details["pattern"] = pattern
        return passed, feedback, details

    # --- L3: http field-truth ----------------------------------------------
    async def _verify_http(self) -> tuple[bool, str, dict[str, Any]]:
        url = self.props.url
        method = (self.props.method or "GET").upper()
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.request(method, url)
        status = response.status_code
        status_ok = _status_matches(status, self.props.expectedStatus or "2xx")

        body_ok = True
        if self.props.bodyContains:
            body_ok = self.props.bodyContains in response.text

        passed = status_ok and body_ok
        feedback = (
            f"L3 http {method} {url} -> {status} "
            f"(expected {self.props.expectedStatus}); status_ok={status_ok}, body_ok={body_ok}"
        )
        return passed, feedback, {"status_code": status, "status_ok": status_ok, "body_ok": body_ok}

    # --- L3: code field-truth (sandbox) -------------------------------------
    async def _verify_code(self, input_data: dict[str, Any]) -> tuple[bool, str, dict[str, Any]]:
        from apps.api.app.node_system.nodes.logic.code.sandbox import execute_code

        output, logs = await execute_code("python", self.props.code, input_data, 30)
        # `output` is always a dict (sandbox wraps non-dicts as {"result": ...}).
        if "passed" in output:
            passed = bool(output["passed"])
        elif "result" in output:
            passed = bool(output["result"])
        else:
            passed = bool(output)
        feedback = f"L3 code assertion -> {passed}"
        return passed, feedback, {"output": output, "logs": logs}


def _status_matches(status: int, expected: str) -> bool:
    """Accept '2xx'/'4xx' ranges, an explicit code ('200'), or a 'lo-hi' band."""
    expected = (expected or "").strip().lower()
    if not expected:
        return 200 <= status < 300
    if len(expected) == 3 and expected.endswith("xx") and expected[0].isdigit():
        base = int(expected[0]) * 100
        return base <= status < base + 100
    if "-" in expected:
        lo_s, hi_s = expected.split("-", 1)
        try:
            return int(lo_s) <= status <= int(hi_s)
        except ValueError:
            return False
    try:
        return status == int(expected)
    except ValueError:
        return False
