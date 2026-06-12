"""Tests for runner-side paired-item propagation (PR3).

These cover the runner's behaviour of populating `_output_items` with
provenance metadata after every successful node execution. No resolver
consumes this data yet — PR4 wires that — but the data must be present
and correct.
"""

from __future__ import annotations

import pytest

from apps.api.app.execution_engine.engine.workflow_runner import WorkflowRunner


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _code_node(node_id: str, code: str) -> dict:
    return {
        "id": node_id,
        "type": "logic.code",
        "data": {"properties": {"language": "python", "code": code}},
    }


@pytest.mark.anyio
async def test_entry_node_items_have_no_paired_item():
    # A node with no upstream — there is no source to point at.
    graph = {
        "nodes": [_code_node("entry", "output = {'value': 1}")],
        "edges": [],
    }
    runner = WorkflowRunner(workflow_id="wf", execution_id="exec", graph=graph)
    await runner.run(trigger_data={})

    items = runner._output_items["entry"]
    assert len(items) == 1
    # CodeNode wraps the user's output dict alongside language/logs metadata,
    # so check the value rather than full-dict equality.
    assert items[0].data["value"] == 1
    assert items[0].paired_item is None


@pytest.mark.anyio
async def test_downstream_node_inherits_paired_item_from_immediate_upstream():
    # B is fed by A. B's output item must point back at A, not "the chain".
    graph = {
        "nodes": [
            _code_node("a", "output = {'value': 10}"),
            _code_node("b", "output = {'final': input['value'] + 5}"),
        ],
        "edges": [{"source": "a", "target": "b"}],
    }
    runner = WorkflowRunner(workflow_id="wf", execution_id="exec", graph=graph)
    await runner.run(trigger_data={})

    a_items = runner._output_items["a"]
    b_items = runner._output_items["b"]

    assert a_items[0].paired_item is None  # entry
    assert b_items[0].data["final"] == 15
    assert b_items[0].paired_item is not None
    assert b_items[0].paired_item.source_node_id == "a"
    assert b_items[0].paired_item.source_item_index == 0


@pytest.mark.anyio
async def test_three_node_chain_each_points_at_immediate_upstream():
    # C's paired_item must be B (not A) — the resolver's chain walk uses
    # one hop at a time.
    graph = {
        "nodes": [
            _code_node("a", "output = {'value': 1}"),
            _code_node("b", "output = {'value': input['value'] + 1}"),
            _code_node("c", "output = {'value': input['value'] + 1}"),
        ],
        "edges": [
            {"source": "a", "target": "b"},
            {"source": "b", "target": "c"},
        ],
    }
    runner = WorkflowRunner(workflow_id="wf", execution_id="exec", graph=graph)
    await runner.run(trigger_data={})

    assert runner._output_items["a"][0].paired_item is None
    assert runner._output_items["b"][0].paired_item is not None
    assert runner._output_items["b"][0].paired_item.source_node_id == "a"
    assert runner._output_items["c"][0].paired_item is not None
    assert runner._output_items["c"][0].paired_item.source_node_id == "b"


@pytest.mark.anyio
async def test_error_edge_dispatch_sets_paired_item_to_failed_source():
    # When an error-edge fires, the recovery node must trace back to the
    # node that failed, exactly like a normal edge.
    graph = {
        "nodes": [
            _code_node("boom", "raise RuntimeError('explode')"),
            _code_node("recover", "output = {'recovered': True}"),
        ],
        "edges": [
            {"source": "boom", "target": "recover", "sourceHandle": "error"},
        ],
    }
    runner = WorkflowRunner(workflow_id="wf", execution_id="exec", graph=graph)
    await runner.run(trigger_data={})

    recover_items = runner._output_items["recover"]
    assert len(recover_items) == 1
    assert recover_items[0].data["recovered"] is True
    assert recover_items[0].paired_item is not None
    assert recover_items[0].paired_item.source_node_id == "boom"


@pytest.mark.anyio
async def test_default_paired_item_only_stamped_when_not_set_explicitly():
    # When a node returns its own `items` list, items that already carry a
    # paired_item must not be overwritten — only `None` slots get the
    # dispatch default. PR4's fan-out nodes will rely on this.
    from apps.api.app.execution_engine.engine.workflow_runner import WorkflowRunner
    from apps.api.app.node_system.base.node_item import NodeItem, PairedItem
    from apps.api.app.node_system.base.node_result import NodeResult

    explicit_paired = PairedItem(source_node_id="custom-upstream", source_item_index=7)
    result = NodeResult(
        success=True,
        output_data={"summary": "fan-out result"},
        items=[
            NodeItem(data={"row": 0}, paired_item=explicit_paired),
            NodeItem(data={"row": 1}),  # missing paired_item → should be defaulted
        ],
    )
    items = WorkflowRunner._build_items_with_provenance(
        result, source_node_id="dispatch-source", source_item_index=3
    )
    assert items[0].paired_item == explicit_paired  # untouched
    assert items[1].paired_item is not None
    assert items[1].paired_item.source_node_id == "dispatch-source"
    assert items[1].paired_item.source_item_index == 3


@pytest.mark.anyio
async def test_legacy_output_data_still_populated_alongside_items():
    # Existing consumers of `_outputs` (e.g. TemplateResolver) keep working.
    graph = {
        "nodes": [
            _code_node("a", "output = {'value': 99}"),
            _code_node("b", "output = {'final': input['value']}"),
        ],
        "edges": [{"source": "a", "target": "b"}],
    }
    runner = WorkflowRunner(workflow_id="wf", execution_id="exec", graph=graph)
    await runner.run(trigger_data={})

    # CodeNode's output_data carries language/logs alongside the user dict,
    # so just confirm the user-visible fields survived intact in both views.
    assert runner._outputs["a"]["value"] == 99
    assert runner._outputs["b"]["final"] == 99
    # And the rich view carries the same payload (Pydantic deep-copies on
    # validation, so equality rather than identity).
    assert runner._output_items["a"][0].data == runner._outputs["a"]
    assert runner._output_items["b"][0].data == runner._outputs["b"]
