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

# Prefixes the resolvers can actually bind. `$json.<path>` is NOT one of
# them (bare `$json` is) — it shipped broken in our own presets once.
_TEMPLATE_RE = re.compile(r"\{\{\s*([^}]+?)\s*\}\}")
_ALLOWED = re.compile(
    r"^("
    r"\$step(\.|$)|\$trigger(\.|$)|\$node\(|\$vars(\.|$)|\$env(\.|$)|\$secrets(\.|$)|"
    r"\$json$|\$previous_node(\.|$)|loop\.|env\.|variables\.|secrets\.|trigger\.|json\."
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
