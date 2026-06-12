"""Tests for the `$step` and `$node('Label')` sugar in JsonataResolver (PR4).

These cover the resolver's paired-item chain walking. The runner doesn't
construct sugar-aware resolvers yet (PR5 wires that in), so these tests
build the resolver directly with synthetic graph state.
"""

from __future__ import annotations

from apps.api.app.execution_engine.engine.expression_engine import JsonataResolver
from apps.api.app.node_system.base.node_item import NodeItem, PairedItem


def _item(data: dict, source_node_id: str | None = None, source_item_index: int = 0) -> NodeItem:
    paired = (
        PairedItem(source_node_id=source_node_id, source_item_index=source_item_index)
        if source_node_id is not None
        else None
    )
    return NodeItem(data=data, paired_item=paired)


# ──────────────────────────────────────────────────────────────────────────
#  $step
# ──────────────────────────────────────────────────────────────────────────


def test_step_resolves_to_immediate_upstream_data() -> None:
    resolver = JsonataResolver(
        context={},
        current_node_id="downstream",
        incoming=PairedItem(source_node_id="upstream", source_item_index=0),
        node_items={
            "upstream": [_item({"status_code": 200, "body": {"id": 42}})],
        },
    )
    assert resolver.evaluate("$step.status_code") == 200
    assert resolver.evaluate("$step.body.id") == 42


def test_step_returns_none_when_no_incoming() -> None:
    resolver = JsonataResolver(context={})
    # JSONata path on `null` cleanly returns nothing.
    assert resolver.evaluate("$step.anything") is None


def test_step_returns_none_when_upstream_item_missing() -> None:
    # Provenance points at a row that doesn't exist in node_items — the
    # resolver should not crash, just yield None.
    resolver = JsonataResolver(
        context={},
        incoming=PairedItem(source_node_id="upstream", source_item_index=99),
        node_items={"upstream": [_item({"x": 1})]},
    )
    assert resolver.evaluate("$step.x") is None


def test_step_picks_correct_item_in_multi_item_upstream() -> None:
    resolver = JsonataResolver(
        context={},
        incoming=PairedItem(source_node_id="loop", source_item_index=2),
        node_items={
            "loop": [
                _item({"i": 0}),
                _item({"i": 1}),
                _item({"i": 2}),
                _item({"i": 3}),
            ],
        },
    )
    assert resolver.evaluate("$step.i") == 2


# ──────────────────────────────────────────────────────────────────────────
#  $node('Label')
# ──────────────────────────────────────────────────────────────────────────


def test_node_lookup_returns_immediate_upstream_by_label() -> None:
    resolver = JsonataResolver(
        context={},
        current_node_id="downstream",
        incoming=PairedItem(source_node_id="http-1", source_item_index=0),
        node_items={"http-1": [_item({"status_code": 201})]},
        label_to_id={"HTTP request": "http-1"},
    )
    assert resolver.evaluate("$node('HTTP request').status_code") == 201


def test_node_lookup_walks_chain_through_intermediate() -> None:
    # trigger → a → b → current
    # current's incoming = b[0], whose paired -> a[0], whose paired -> trigger[0]
    resolver = JsonataResolver(
        context={},
        current_node_id="current",
        incoming=PairedItem(source_node_id="b", source_item_index=0),
        node_items={
            "trigger": [_item({"url": "https://example.com"})],
            "a": [_item({"middle": "ok"}, source_node_id="trigger")],
            "b": [_item({"latest": "ok"}, source_node_id="a")],
        },
        label_to_id={"Trigger": "trigger", "A": "a", "B": "b"},
    )
    assert resolver.evaluate("$node('Trigger').url") == "https://example.com"
    assert resolver.evaluate("$node('A').middle") == "ok"
    assert resolver.evaluate("$node('B').latest") == "ok"


def test_node_lookup_unknown_label_returns_none() -> None:
    resolver = JsonataResolver(
        context={},
        incoming=PairedItem(source_node_id="a", source_item_index=0),
        node_items={"a": [_item({"x": 1})]},
        label_to_id={"A": "a"},
    )
    assert resolver.evaluate("$node('Unknown').x") is None


def test_node_lookup_when_chain_dead_ends() -> None:
    # Chain breaks: a's item has no paired_item, so walking past `a` to
    # "Target" fails cleanly.
    resolver = JsonataResolver(
        context={},
        incoming=PairedItem(source_node_id="a", source_item_index=0),
        node_items={
            "a": [_item({"x": 1})],  # no paired_item — dead end
        },
        label_to_id={"A": "a", "Target": "target-id"},
    )
    assert resolver.evaluate("$node('Target').x") is None
    # But the reachable one still works.
    assert resolver.evaluate("$node('A').x") == 1


def test_node_lookup_returns_correct_item_after_fan_out() -> None:
    # foreach fans out three items. The downstream node currently processes
    # item 2 of foreach. `$node('Foreach')` must return foreach.items[2],
    # not items[0] or "latest" — because that's the row this lineage came
    # from.
    resolver = JsonataResolver(
        context={},
        current_node_id="downstream",
        incoming=PairedItem(source_node_id="foreach", source_item_index=2),
        node_items={
            "foreach": [
                _item({"row": "a"}, source_node_id="trigger"),
                _item({"row": "b"}, source_node_id="trigger"),
                _item({"row": "c"}, source_node_id="trigger"),
            ],
            "trigger": [_item({"items": ["a", "b", "c"]})],
        },
        label_to_id={"Foreach": "foreach", "Trigger": "trigger"},
    )
    assert resolver.evaluate("$node('Foreach').row") == "c"
    # Trigger lookup walks foreach[2].paired_item → trigger[0]
    assert resolver.evaluate("$node('Trigger').items[0]") == "a"


def test_paired_chain_cycle_is_aborted_safely() -> None:
    # Pathological metadata: a → b → a. Walker must not loop forever.
    resolver = JsonataResolver(
        context={},
        incoming=PairedItem(source_node_id="a", source_item_index=0),
        node_items={
            "a": [_item({"x": 1}, source_node_id="b")],
            "b": [_item({"y": 2}, source_node_id="a")],
        },
        label_to_id={"Target": "target-id"},
    )
    # Should return None and not hang.
    assert resolver.evaluate("$node('Target').x") is None


# ──────────────────────────────────────────────────────────────────────────
#  Compose with regular JSONata
# ──────────────────────────────────────────────────────────────────────────


def test_step_composes_with_jsonata_arithmetic() -> None:
    resolver = JsonataResolver(
        context={"multiplier": 10},
        incoming=PairedItem(source_node_id="prev", source_item_index=0),
        node_items={"prev": [_item({"value": 5})]},
    )
    # `multiplier` comes from the context document, `$step.value` from sugar.
    assert resolver.evaluate("multiplier * $step.value") == 50


def test_explicit_bindings_override_step() -> None:
    # If the caller binds `$step` themselves, their value wins.
    resolver = JsonataResolver(
        context={},
        incoming=PairedItem(source_node_id="prev", source_item_index=0),
        node_items={"prev": [_item({"value": 1})]},
    )
    assert resolver.evaluate("$step.value", bindings={"step": {"value": 999}}) == 999
