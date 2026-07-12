"""Contract tests for the Crew (ai.agent_crew) maker/checker loop.

All graphs are deterministic (form trigger + verify checks — no LLM), so
every terminal state is reproducible. Locks the July 2026 regressions:
`_trigger_data` missing on sub-runners, round failures swallowed into a
successful no_op, `$step` unresolvable inside rounds.
"""

from typing import Any

import pytest

from apps.api.app.execution_engine.engine.workflow_runner import WorkflowRunner


@pytest.fixture
def anyio_backend():
    return "asyncio"


def _node(nid: str, ntype: str, label: str, props: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": nid,
        "type": ntype,
        "position": {"x": 0, "y": 0},
        "data": {"label": label, "properties": props},
    }


def _edge(a: str, b: str) -> dict[str, Any]:
    return {"id": f"{a}-{b}", "source": a, "target": b}


def _gate_graph(crew_props: dict[str, Any], check_props: dict[str, Any]) -> dict[str, Any]:
    """form → crew → verify — the minimal verified loop."""
    return {
        "nodes": [
            _node(
                "form",
                "trigger.form",
                "Form",
                {"inputs": [{"name": "amount", "type": "number", "value": ""}]},
            ),
            _node("crew", "ai.agent_crew", "Crew", {"goal": "gate", **crew_props}),
            _node("check", "ai.verify", "Check", {"mode": "expression", "level": 1, **check_props}),
        ],
        "edges": [_edge("form", "crew"), _edge("crew", "check")],
    }


async def _run(graph: dict[str, Any], trigger: dict[str, Any]) -> dict[str, Any]:
    runner = WorkflowRunner(workflow_id="t-wf", execution_id="t-exec", graph=graph)
    return await runner.run(trigger) or {}


# ── Terminal states ────────────────────────────────────────────────────


@pytest.mark.anyio
async def test_success_on_first_passing_round():
    g = _gate_graph(
        {"maxRounds": 3, "minRounds": 1},
        {"expression": "{{$step.amount}} <= 500"},
    )
    out = await _run(g, {"amount": 120})
    assert out["status"] == "success"
    assert out["rounds"] == 1
    assert out["result"]["passed"] is True


@pytest.mark.anyio
async def test_stalled_when_deterministic_check_cannot_improve():
    g = _gate_graph(
        {"maxRounds": 4, "minRounds": 1, "stagnationRounds": 1},
        {"expression": "{{$step.amount}} <= 500"},
    )
    out = await _run(g, {"amount": 900})
    assert out["status"] == "stalled"
    assert out["rounds"] == 2  # round 1 fails, round 2 stagnates
    assert out["result"]["passed"] is False


@pytest.mark.anyio
async def test_exhausted_at_max_rounds():
    g = _gate_graph(
        # High stagnation threshold so exhaustion is what terminates.
        {"maxRounds": 3, "minRounds": 1, "stagnationRounds": 99},
        {"expression": "{{$step.amount}} <= 500"},
    )
    out = await _run(g, {"amount": 900})
    assert out["status"] == "exhausted"
    assert out["rounds"] == 3


@pytest.mark.anyio
async def test_min_rounds_forces_extra_iterations():
    g = _gate_graph(
        {"maxRounds": 5, "minRounds": 3, "stagnationRounds": 99},
        {"expression": "{{$step.amount}} <= 500"},
    )
    out = await _run(g, {"amount": 120})
    assert out["status"] == "success"
    assert out["rounds"] == 3  # success verdict may not terminate before minRounds


@pytest.mark.anyio
async def test_blocked_round_failure_fails_the_crew_with_reason():
    """A crew member crashing (not a verdict — a crash) must surface the
    real reason. July 2026: this ended as a silent successful no_op."""
    g = {
        "nodes": [
            _node(
                "form",
                "trigger.form",
                "Form",
                {"inputs": [{"name": "x", "type": "string", "value": ""}]},
            ),
            _node("crew", "ai.agent_crew", "Crew", {"goal": "g", "maxRounds": 2, "minRounds": 1}),
            # Agent with no credential in a bare context ⇒ hard node failure.
            _node(
                "agent",
                "action.agent",
                "Agent",
                {"provider": "openai", "messages": [{"role": "user", "content": "hi"}]},
            ),
        ],
        "edges": [_edge("form", "crew"), _edge("crew", "agent")],
    }
    runner = WorkflowRunner(workflow_id="t-wf", execution_id="t-exec", graph=g)
    with pytest.raises(Exception, match="Crew round 1 failed"):
        await runner.run({"x": "1"})
    assert runner._failed.is_set()
    assert "Crew round 1 failed" in (runner._error_message or "")


# ── Round payload contract ─────────────────────────────────────────────


@pytest.mark.anyio
async def test_round_input_carries_goal_round_feedback_and_trigger_fields():
    """The check sees {goal, round, feedback} + the trigger's fields via
    $step — the exact resolution that broke inside sub-runners in July."""
    g = _gate_graph(
        {"maxRounds": 1, "minRounds": 1},
        # Passes only if BOTH a trigger field and the injected round
        # counter resolve inside the sub-graph.
        {"expression": "{{$step.round}} == 0"},
    )
    out = await _run(g, {"amount": 1})
    assert out["result"]["passed"] is True, out["result"]["feedback"]

    g2 = _gate_graph({"maxRounds": 1, "minRounds": 1}, {"expression": "{{$step.amount}} == 42"})
    out2 = await _run(g2, {"amount": 42})
    assert out2["result"]["passed"] is True, out2["result"]["feedback"]


@pytest.mark.anyio
async def test_trigger_binding_resolves_inside_rounds():
    """Regression: sub-runners crashed on missing _trigger_data, then
    resolved {{$trigger.*}} against an empty dict. NB the jsonata binding
    is the RAW trigger payload — `$trigger.amount`, not `$trigger.output.…`."""
    g = _gate_graph(
        {"maxRounds": 1, "minRounds": 1},
        {"expression": "{{$trigger.amount}} == 7"},
    )
    out = await _run(g, {"amount": 7})
    assert out["result"]["passed"] is True, out["result"]["feedback"]


# ── run_downstream failure propagation ────────────────────────────────


@pytest.mark.anyio
async def test_failed_subrun_returns_status_and_error_not_empty_dict():
    """run_downstream used to discard sub-runner failures as {} — the crew
    could never know WHY a round died."""
    g = {
        "nodes": [
            _node(
                "form",
                "trigger.form",
                "Form",
                {"inputs": [{"name": "x", "type": "string", "value": ""}]},
            ),
            _node("crew", "ai.agent_crew", "Crew", {"goal": "g", "maxRounds": 1, "minRounds": 1}),
            _node(
                "agent",
                "action.agent",
                "Agent",
                {"provider": "openai", "messages": [{"role": "user", "content": "hi"}]},
            ),
        ],
        "edges": [_edge("form", "crew"), _edge("crew", "agent")],
    }
    runner = WorkflowRunner(workflow_id="t-wf", execution_id="t-exec", graph=g)
    with pytest.raises(Exception, match="credential"):
        await runner.run({"x": "1"})
    # The crew's terminal error embeds the inner node's real failure.
    assert "credential" in (runner._error_message or "").lower()
