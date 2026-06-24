"""Smoke tests for the template registry + loop templates."""

from __future__ import annotations

import pytest

from apps.api.app.features.templates import get_template, list_templates


def test_loop_templates_present():
    loops = list_templates(category="loops")
    ids = {t["id"] for t in loops}
    assert {"loop_linear_triage", "loop_dependabot_automerge"} <= ids


@pytest.mark.parametrize(
    "tid",
    ["loop_linear_triage", "loop_dependabot_automerge"],
)
def test_loop_template_well_formed(tid):
    t = get_template(tid)
    assert t is not None
    assert "name" in t
    assert "summary" in t
    assert "credentials_required" in t
    wf = t.get("workflow", {})
    graph = wf.get("graph", {})
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    # Trigger + agent at minimum
    assert any(n["type"].startswith("trigger.") for n in nodes)
    assert any(n["type"] == "action.agent" for n in nodes)
    # Every edge references real nodes
    node_ids = {n["id"] for n in nodes}
    for e in edges:
        assert e["source"] in node_ids
        assert e["target"] in node_ids


def test_agent_node_has_loop_hardening_fields():
    """All three templates must use the new Phase 1 budget fields."""
    for tid in (
        "loop_linear_triage",
        "loop_dependabot_automerge",
    ):
        t = get_template(tid)
        agent = next(n for n in t["workflow"]["graph"]["nodes"] if n["type"] == "action.agent")
        props = agent["data"]["properties"]
        assert "maxSeconds" in props
        assert "maxCostUsd" in props
        assert "successWhen" in props
        assert "failurePolicy" in props
        assert props["maxCostUsd"] <= 0.50


def test_unknown_template_returns_none():
    assert get_template("does_not_exist") is None
