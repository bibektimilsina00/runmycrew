"""Contract tests for the verification ladder (L1–L4).

The ladder is the product's core promise — a crew only finishes when a
check passes. In July 2026 every L1 assertion silently evaluated True
(resolved comparisons fell into a truthy fallback), which nothing
caught because none of this had tests. These lock the contract:

- A check NEVER crashes the loop: infra failures become a
  ``passed=False`` verdict with feedback (success=True on NodeResult).
- Garbage in ⇒ ``passed=False``, never a truthy default.
"""

import json
from typing import Any
from unittest.mock import AsyncMock, patch

import pytest

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.nodes.ai.evaluator.evaluator import EvaluatorNode
from apps.api.app.node_system.nodes.ai.verify.verify import VerifyNode


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _ctx(**over: Any) -> NodeContext:
    kw: dict[str, Any] = dict(
        execution_id="t-exec",
        workflow_id="t-wf",
        node_id="t-node",
        variables={},
        credentials=[],
        http_client=None,
    )
    kw.update(over)
    return NodeContext(**kw)


def _verify(props: dict[str, Any]) -> VerifyNode:
    node = VerifyNode.__new__(VerifyNode)
    node.props = VerifyNode.get_properties_model()(**props)
    return node


# ── L1: expression ─────────────────────────────────────────────────────


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("expression", "input_data", "expected"),
    [
        # Literal comparisons — the resolved-template shape (runner
        # substitutes {{$step.x}} before the node sees the string).
        ("120 <= 500", {}, True),
        ("900 <= 500", {}, False),
        ("true == true", {}, True),
        ("false == true", {}, False),
        ("10 > 5", {}, True),
        ("5 != 5", {}, False),
        # Unresolved/blank LHS (template that resolved to nothing) must
        # NOT pass — this exact shape was the always-true bug.
        (" == true", {}, False),
        # Braced path form evaluated inside the node (input is exposed
        # as `json.output.*` in the node-level resolver).
        ("{{json.output.passed}} == true", {"passed": True}, True),
        ("{{json.output.passed}} == true", {"passed": False}, False),
        # Unresolved template reaching the node must fail closed.
        ("{{$step.passed}} == true", {"passed": True}, False),
    ],
)
async def test_l1_expression_verdicts(expression, input_data, expected):
    node = _verify({"mode": "expression", "expression": expression, "level": 1})
    result = await node.execute(input_data, _ctx())
    assert result.success is True  # a verdict, never a crash
    assert result.output_data["passed"] is expected, result.output_data["feedback"]


@pytest.mark.anyio
async def test_l1_malformed_expression_fails_closed():
    node = _verify({"mode": "expression", "expression": "$$$ not an expression $$$", "level": 1})
    result = await node.execute({}, _ctx())
    assert result.success is True
    # Fail-closed: junk must never count as a pass.
    assert result.output_data["passed"] is False


# ── L2: rule ───────────────────────────────────────────────────────────


@pytest.mark.anyio
@pytest.mark.parametrize(
    ("props", "expected"),
    [
        ({"ruleType": "contains", "content": "hello world", "pattern": "world"}, True),
        ({"ruleType": "contains", "content": "hello world", "pattern": "mars"}, False),
        ({"ruleType": "not_contains", "content": "clean output", "pattern": "error"}, True),
        ({"ruleType": "not_contains", "content": "an error happened", "pattern": "error"}, False),
        ({"ruleType": "regex", "content": "order-12345", "pattern": r"order-\d+"}, True),
        ({"ruleType": "regex", "content": "no digits here", "pattern": r"order-\d+"}, False),
        (
            {"ruleType": "required_keys", "content": '{"a": 1, "b": 2}', "requiredKeys": "a,b"},
            True,
        ),
        (
            {"ruleType": "required_keys", "content": '{"a": 1}', "requiredKeys": "a,b"},
            False,
        ),
        # Garbage subject for required_keys: not JSON ⇒ fail, not crash.
        ({"ruleType": "required_keys", "content": "not json", "requiredKeys": "a"}, False),
        # Empty subject: contains nothing.
        ({"ruleType": "contains", "content": "", "pattern": "x"}, False),
    ],
)
async def test_l2_rule_verdicts(props, expected):
    node = _verify({"mode": "rule", "level": 2, **props})
    result = await node.execute({}, _ctx())
    assert result.success is True
    assert result.output_data["passed"] is expected, result.output_data["feedback"]


# ── L3: http / code — infra failure is a verdict, not a crash ─────────


@pytest.mark.anyio
async def test_l3_http_unreachable_fails_closed():
    node = _verify({"mode": "http", "url": "http://127.0.0.1:1/nope", "method": "GET", "level": 3})
    result = await node.execute({}, _ctx())
    assert result.success is True
    assert result.output_data["passed"] is False
    assert result.output_data["feedback"]  # says why


@pytest.mark.anyio
async def test_l3_unknown_mode_fails_closed():
    node = _verify({"mode": "definitely-not-a-mode", "level": 3})
    result = await node.execute({}, _ctx())
    assert result.success is True
    assert result.output_data["passed"] is False


# ── L4: evaluator — model output parsing ───────────────────────────────


def _evaluator(**props: Any) -> EvaluatorNode:
    node = EvaluatorNode.__new__(EvaluatorNode)
    defaults: dict[str, Any] = {
        "provider": "openai",
        "model": "gpt-test",
        "content": "the content under judgment",
        "metrics": [
            {"name": "quality", "description": "q", "min": 0, "max": 10},
            {"name": "clarity", "description": "c", "min": 0, "max": 10},
        ],
    }
    defaults.update(props)
    node.props = EvaluatorNode.get_properties_model()(**defaults)
    return node


def _openai_cred() -> list[dict[str, Any]]:
    return [{"id": "c1", "type": "openai_api_key", "data": {"api_key": "sk-test"}}]


class _FakeResponse:
    def __init__(self, content: str, status: int = 200):
        self._content = content
        self.status_code = status
        self.text = content

    def raise_for_status(self):
        pass

    def json(self):
        return {"choices": [{"message": {"content": self._content}}]}


def _mock_llm(content: str):
    return patch(
        "httpx.AsyncClient.post",
        new=AsyncMock(return_value=_FakeResponse(content)),
    )


@pytest.mark.anyio
async def test_l4_well_formed_verdict():
    node = _evaluator()
    body = json.dumps({"quality": 9, "clarity": 8, "passed": True, "feedback": "good"})
    with _mock_llm(body):
        result = await node.execute({}, _ctx(credentials=_openai_cred()))
    assert result.success is True
    assert result.output_data["passed"] is True
    assert result.output_data["average"] == 8.5


@pytest.mark.anyio
async def test_l4_missing_passed_falls_back_to_60_percent_rule():
    node = _evaluator()
    # 9+8 avg 8.5 >= 6.0 threshold ⇒ passed via fallback
    with _mock_llm(json.dumps({"quality": 9, "clarity": 8, "feedback": "no passed key"})):
        result = await node.execute({}, _ctx(credentials=_openai_cred()))
    assert result.output_data["passed"] is True

    # 2+3 avg 2.5 < 6.0 ⇒ fail via fallback
    with _mock_llm(json.dumps({"quality": 2, "clarity": 3, "feedback": "low"})):
        result = await node.execute({}, _ctx(credentials=_openai_cred()))
    assert result.output_data["passed"] is False


@pytest.mark.anyio
async def test_l4_unparseable_model_output_is_an_error_not_a_pass():
    node = _evaluator()
    with _mock_llm("I am not JSON at all"):
        result = await node.execute({}, _ctx(credentials=_openai_cred()))
    assert result.success is False  # crew treats this as a failed round
    assert result.error


@pytest.mark.anyio
async def test_l4_missing_metric_scores_default_to_min():
    node = _evaluator()
    with _mock_llm(json.dumps({"quality": 10, "passed": True, "feedback": ""})):
        result = await node.execute({}, _ctx(credentials=_openai_cred()))
    assert result.output_data["scores"]["clarity"] == 0  # metric min


@pytest.mark.anyio
async def test_l4_missing_credential_is_a_clear_error():
    node = _evaluator()
    result = await node.execute({}, _ctx(credentials=[]))
    assert result.success is False
    assert "credential" in (result.error or "").lower()
