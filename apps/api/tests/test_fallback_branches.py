"""Garbage-input tests for the engine's fallback branches, plus a lint
that keeps template syntax in seeds/presets resolvable.

The July 2026 always-true L1 bug lived in exactly this kind of branch:
"when in doubt, return something truthy/empty". Every such branch gets a
test for the doubt case.
"""

import re
from glob import glob
from pathlib import Path
from typing import Any

import pytest

from apps.api.app.execution_engine.engine.expression_engine import JsonataResolver
from apps.api.app.execution_engine.engine.template_resolver import TemplateResolver
from apps.api.app.node_system.nodes.common.trigger.form import _coerce
from apps.worker.app.jobs.tasks import _extract_reply

REPO = Path(__file__).resolve().parents[3]


def _resolver(**over: Any) -> TemplateResolver:
    kw: dict[str, Any] = dict(node_outputs={}, trigger_data={}, variables={})
    kw.update(over)
    return TemplateResolver(**kw)


# ── evaluate_condition ─────────────────────────────────────────────────


@pytest.mark.parametrize(
    ("condition", "strict", "expected"),
    [
        # Literal comparisons (the resolved-template shape).
        ("900 <= 500", False, False),
        ("120 <= 500", False, True),
        ('"a" == "a"', False, True),
        # Blank LHS from a blanked template — never a pass.
        (" == true", True, False),
        # Non-numeric operands on a numeric operator — fail, not crash.
        ("banana < 5", False, False),
        # Junk in strict mode fails closed.
        ("$$$ garbage $$$", True, False),
        ("true", False, True),
        ("false", False, False),
    ],
)
def test_evaluate_condition_garbage(condition, strict, expected):
    assert _resolver().evaluate_condition(condition, strict=strict) is expected


def test_evaluate_condition_truthy_fallback_still_works_non_strict():
    r = _resolver(node_outputs={"json": {"flag": "yes"}})
    # Documented behaviour: a bare template is a truthy check.
    assert r.evaluate_condition("{{json.output.flag}}") is True


# ── $step / $trigger / $node bindings ──────────────────────────────────


def test_step_falls_back_to_node_input_without_provenance():
    """Regression: $step was None for the first node of a crew round."""
    r = JsonataResolver(context={"amount": 42}, current_node_id="n1")
    assert r.evaluate("$step.amount") == 42


def test_step_none_context_does_not_crash():
    r = JsonataResolver(context="not-a-dict", current_node_id="n1")
    assert r.evaluate("$step") is None


def test_trigger_binding_is_raw_payload():
    r = JsonataResolver(context={}, current_node_id="n1", trigger_data={"amount": 7})
    assert r.evaluate("$trigger.amount") == 7
    # `.output.` was never part of the binding — must resolve to nothing,
    # not something surprising.
    assert r.evaluate("$trigger.output") is None


def test_node_lookup_unknown_label_is_none():
    r = JsonataResolver(context={}, current_node_id="n1", label_to_id={})
    assert r.evaluate("$node('Nope')") is None


# ── worker _extract_reply ──────────────────────────────────────────────


@pytest.mark.parametrize(
    ("output", "expect_empty"),
    [
        ({}, True),
        ({"status": "stalled", "rounds": 2, "result": {"passed": False}}, True),
        ({"content": "hello"}, False),
        ({"weird": {"nested": [1, 2]}}, True),
        ({"content": ""}, True),
    ],
)
def test_extract_reply_never_crashes(output, expect_empty):
    text, artifacts = _extract_reply(output)
    assert isinstance(text, str)
    assert isinstance(artifacts, list)
    assert (text == "") is expect_empty


# ── form trigger _coerce ───────────────────────────────────────────────


@pytest.mark.parametrize(
    ("value", "declared", "expected"),
    [
        ("42", "number", 42),
        ("4.5", "number", 4.5),
        ("not-a-number", "number", "not-a-number"),  # untouched, not crash
        ("true", "boolean", True),
        ("off", "boolean", False),
        ("maybe", "boolean", "maybe"),
        ('{"a": 1}', "object", {"a": 1}),
        ("not json", "object", "not json"),
        ("", "string", ""),
        ("", "number", None),
        (None, "boolean", None),
        ("[1,2]", "array", [1, 2]),
    ],
)
def test_form_coerce_garbage(value, declared, expected):
    assert _coerce(value, declared) == expected


# ── Template-syntax lint over seeds + presets ──────────────────────────

# The user-facing convention (what the expression autocomplete offers):
# `$step.<field>` and `$node('Label').<field>`, plus the workflow-scope
# namespaces. `$trigger` is an engine-internal binding, `$previous_node`
# never existed, and `$json.<path>` never resolves — all three shipped
# broken in our own presets/defaults once; ban them here.
_TEMPLATE_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
_ALLOWED = re.compile(
    r"^("
    r"\$step(\.|$)|\$node\(|\$vars(\.|$)|\$env(\.|$)|\$secrets(\.|$)|\$loop(\.|$)|"
    r"loop\.|env\.|variables\.|secrets\."
    r")"
)


def _lint_templates(text: str, source: str) -> list[str]:
    bad = []
    for m in _TEMPLATE_RE.finditer(text):
        expr = m.group(1).strip()
        # Strip a leading `=` (expression-mode marker in some fields).
        expr = expr.lstrip("=").strip()
        if expr.startswith("$json."):
            bad.append(
                f"{source}: '{{{{{expr}}}}}' — $json.<path> never resolves; use $step.<path>"
            )
        elif expr.startswith("$") and not _ALLOWED.match(expr):
            bad.append(f"{source}: '{{{{{expr}}}}}' — unknown binding prefix")
    return bad


def test_seed_templates_use_resolvable_bindings():
    problems: list[str] = []
    for f in glob(str(REPO / "apps/api/app/features/templates/seeds/**/*.json"), recursive=True):
        problems += _lint_templates(Path(f).read_text(), Path(f).name)
    assert not problems, "\n".join(problems)


def test_crew_presets_use_resolvable_bindings():
    presets = (REPO / "apps/web/src/features/loops/utils/crewPresets.ts").read_text()
    problems = _lint_templates(presets, "crewPresets.ts")
    assert not problems, "\n".join(problems)


def test_node_metadata_uses_resolvable_bindings():
    """Every placeholder/default/description in node source files teaches
    only the canonical forms. $previous_node shipped as ai.parallel's REAL
    default and $trigger.output as llm/agent's default message — both
    resolved to nothing for every fresh node."""
    problems: list[str] = []
    for f in glob(str(REPO / "apps/api/app/node_system/**/*.py"), recursive=True):
        path = Path(f)
        problems += _lint_templates(path.read_text(), str(path.relative_to(REPO)))
    assert not problems, "\n".join(problems)


# ── Loop-condition resolution ($step / $vars inside iterations) ────────


def test_for_iteration_resolver_binds_step_and_vars():
    r = TemplateResolver.for_iteration({"hasMore": True, "count": 3}, variables={"limit": 5})
    assert r.evaluate_condition("{{$step.hasMore}}") is True
    assert r.evaluate_condition("{{$step.count}} < 5") is True
    assert r.evaluate_condition("{{$step.count}} >= 5") is False
    assert r.evaluate_condition("{{$vars.limit}} == 5") is True
    # Legacy non-$ forms keep working through the same resolver.
    assert r.evaluate_condition("{{variables.limit}} == 5") is True
    assert r.evaluate_condition("{{iteration.output.count}} == 3") is True


def test_for_iteration_resolver_fails_closed_on_missing_field():
    r = TemplateResolver.for_iteration({"done": False})
    assert r.evaluate_condition("{{$step.hasMore}}") is False
    assert r.evaluate_condition("{{$step.missing}} == 1") is False


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_while_condition_re_evaluates_per_iteration():
    """Regression: the runner pre-resolved the while condition ONCE against
    the loop node's input, so the node re-evaluated a baked-in constant
    forever — every template-driven while loop ran to maxIterations.
    `deferred_properties` hands the raw template to the node instead."""
    from apps.api.app.execution_engine.engine.workflow_runner import WorkflowRunner

    def _n(nid, ntype, label, props):
        return {
            "id": nid,
            "type": ntype,
            "position": {"x": 0, "y": 0},
            "data": {"label": label, "properties": props},
        }

    g = {
        "nodes": [
            _n(
                "form",
                "trigger.form",
                "Form",
                {"inputs": [{"name": "stop", "type": "string", "value": ""}]},
            ),
            _n(
                "w",
                "logic.while",
                "While",
                {"condition": "{{$step.stop}} != done", "maxIterations": 5},
            ),
            _n(
                "c",
                "logic.code",
                "Code",
                {"language": "python", "code": "output = {'stop': 'done'}"},
            ),
        ],
        "edges": [
            {"id": "a", "source": "form", "target": "w"},
            {"id": "b", "source": "w", "target": "c"},
        ],
    }
    runner = WorkflowRunner(workflow_id="t-wf", execution_id="t-exec", graph=g)
    out = await runner.run({"stop": ""})
    # Body sets stop='done'; the SECOND check must see it and break.
    assert out["iterations"] == 1
