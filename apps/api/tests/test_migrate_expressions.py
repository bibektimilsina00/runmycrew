"""Tests for the legacy → JSONata migration's pure rewrite functions (PR10).

DB integration is not exercised here (no fixture infra in the test suite).
The pure helpers do all the rewriting; the async driver around them just
loops over rows.
"""

from __future__ import annotations

from apps.api.scripts.migrate_expressions import (
    _rewrite_string,
    _rewrite_value,
    migrate_graph,
)

# ──────────────────────────────────────────────────────────────────────────
#  _rewrite_string
# ──────────────────────────────────────────────────────────────────────────


def test_rewrites_simple_node_reference() -> None:
    out, n = _rewrite_string("{{abc-123.body.id}}", {"abc-123": "HTTP request"})
    assert out == "=$node('HTTP request').body.id"
    assert n == 1


def test_rewrites_with_output_marker() -> None:
    out, n = _rewrite_string("{{abc-123.output.body.id}}", {"abc-123": "HTTP request"})
    assert out == "=$node('HTTP request').body.id"
    assert n == 1


def test_rewrites_bare_node_id_no_path() -> None:
    out, n = _rewrite_string("{{abc-123}}", {"abc-123": "HTTP"})
    assert out == "=$node('HTTP')"
    assert n == 1


def test_rewrites_when_inner_is_just_output() -> None:
    out, n = _rewrite_string("{{abc-123.output}}", {"abc-123": "HTTP"})
    assert out == "=$node('HTTP')"
    assert n == 1


def test_handles_node_id_containing_dots() -> None:
    # n8n-style ids like `action.http_request-1778…` would otherwise be
    # split apart by a naive `.`-split before the lookup.
    id_to_label = {"action.http_request-1778": "HTTP"}
    out, n = _rewrite_string("{{action.http_request-1778.body.id}}", id_to_label)
    assert out == "=$node('HTTP').body.id"
    assert n == 1


def test_migrates_trigger_with_output_marker() -> None:
    out, n = _rewrite_string("{{trigger.output.url}}", {"abc": "X"})
    assert out == "=$trigger.url"
    assert n == 1


def test_migrates_trigger_without_output_marker() -> None:
    # Some legacy graphs used `{{trigger.url}}` directly because the runtime
    # resolver auto-stripped `.output` after a missed lookup.
    out, n = _rewrite_string("{{trigger.url}}", {"abc": "X"})
    assert out == "=$trigger.url"
    assert n == 1


def test_migrates_bare_trigger_collapses_to_var() -> None:
    out, n = _rewrite_string("{{trigger}}", {"abc": "X"})
    assert out == "=$trigger"
    assert n == 1


def test_migrates_variables_to_vars_binding() -> None:
    out, n = _rewrite_string("{{variables.count}}", {"abc": "X"})
    assert out == "=$vars.count"
    assert n == 1


def test_migrates_env_namespace() -> None:
    out, n = _rewrite_string("{{env.API_URL}}", {"abc": "X"})
    assert out == "=$env.API_URL"
    assert n == 1


def test_migrates_secrets_namespace() -> None:
    out, n = _rewrite_string("{{secrets.DB_PASSWORD}}", {"abc": "X"})
    assert out == "=$secrets.DB_PASSWORD"
    assert n == 1


def test_migrates_loop_namespace() -> None:
    out, n = _rewrite_string("{{loop.item}}", {"abc": "X"})
    assert out == "=$loop.item"
    assert n == 1


def test_namespace_migration_is_idempotent() -> None:
    out, n = _rewrite_string("=$trigger.url", {})
    assert out == "=$trigger.url"
    assert n == 0


def test_leaves_unknown_node_id_alone() -> None:
    out, n = _rewrite_string("{{deleted-node.body}}", {"abc": "X"})
    assert out == "{{deleted-node.body}}"
    assert n == 0


def test_idempotent_on_already_migrated_string() -> None:
    out, n = _rewrite_string("=$node('HTTP').body", {"abc": "HTTP"})
    assert out == "=$node('HTTP').body"
    assert n == 0


def test_skips_mixed_text_strings() -> None:
    # Mixed-text strings need JSONata string concat (`& "suffix"`); out of
    # scope for the one-shot migration. Left to the legacy resolver.
    out, n = _rewrite_string("Hello {{abc.body.name}}", {"abc": "X"})
    assert out == "Hello {{abc.body.name}}"
    assert n == 0


def test_skips_multi_template_strings() -> None:
    out, n = _rewrite_string("{{a.x}}{{b.y}}", {"a": "A", "b": "B"})
    assert out == "{{a.x}}{{b.y}}"
    assert n == 0


def test_escapes_quote_in_label() -> None:
    out, n = _rewrite_string("{{abc.body}}", {"abc": "It's hot"})
    assert out == "=$node('It\\'s hot').body"
    assert n == 1


def test_returns_unchanged_for_empty_string() -> None:
    out, n = _rewrite_string("", {"abc": "X"})
    assert out == ""
    assert n == 0


# ──────────────────────────────────────────────────────────────────────────
#  _rewrite_value (recursion)
# ──────────────────────────────────────────────────────────────────────────


def test_recursive_walk_dict_and_list() -> None:
    id_to_label = {"a": "Alpha"}
    value = {
        "headers": {"name": "{{a.body.name}}"},
        "params": ["{{a.body.value}}", "static"],
        "nested": {"x": {"y": "{{a.body.deep}}"}},
        "literal": 42,
        "bool": True,
        "none": None,
    }
    rewritten, n = _rewrite_value(value, id_to_label)
    assert n == 3
    assert rewritten == {
        "headers": {"name": "=$node('Alpha').body.name"},
        "params": ["=$node('Alpha').body.value", "static"],
        "nested": {"x": {"y": "=$node('Alpha').body.deep"}},
        "literal": 42,
        "bool": True,
        "none": None,
    }


def test_recursive_walk_returns_zero_when_nothing_matched() -> None:
    # Pure-literal values + an unknown namespace head (`vars` isn't a real
    # legacy namespace — `variables` is). Nothing matches → no rewrite.
    rewritten, n = _rewrite_value(
        {"x": "static", "y": "{{vars.k}}"},
        {"abc": "X"},
    )
    assert n == 0
    assert rewritten == {"x": "static", "y": "{{vars.k}}"}


# ──────────────────────────────────────────────────────────────────────────
#  migrate_graph (top-level)
# ──────────────────────────────────────────────────────────────────────────


def test_migrate_graph_uses_node_labels_from_graph() -> None:
    graph = {
        "nodes": [
            {"id": "a", "data": {"label": "HTTP fetch", "properties": {}}},
            {
                "id": "b",
                "data": {
                    "label": "Code",
                    "properties": {
                        "input": "{{a.output.body.id}}",
                        "header": "{{a.body.token}}",
                    },
                },
            },
        ],
        "edges": [{"source": "a", "target": "b"}],
    }
    new_graph, n = migrate_graph(graph)
    assert n == 2
    b_props = new_graph["nodes"][1]["data"]["properties"]
    assert b_props["input"] == "=$node('HTTP fetch').body.id"
    assert b_props["header"] == "=$node('HTTP fetch').body.token"
    # Node `a` had no expressions — left as the same dict object.
    assert new_graph["nodes"][0] is graph["nodes"][0]


def test_migrate_graph_falls_back_to_id_when_label_missing() -> None:
    graph = {
        "nodes": [
            {"id": "a", "data": {"properties": {}}},  # no label
            {"id": "b", "data": {"properties": {"x": "{{a.body}}"}}},
        ],
        "edges": [],
    }
    new_graph, n = migrate_graph(graph)
    assert n == 1
    assert new_graph["nodes"][1]["data"]["properties"]["x"] == "=$node('a').body"


def test_migrate_graph_no_op_returns_identity() -> None:
    graph = {
        "nodes": [
            {"id": "a", "data": {"label": "A", "properties": {"x": "static"}}},
        ],
        "edges": [],
    }
    new_graph, n = migrate_graph(graph)
    assert n == 0
    assert new_graph is graph  # identity — caller can skip persisting
