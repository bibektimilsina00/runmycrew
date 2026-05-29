"""Coverage for the core workflow execution path.

Guards the regression that left execution silently broken: the worker task
imported pre-refactor module paths (app.repositories/services/models) after the
features/ refactor, and nothing exercised the real path. Kept infra-free
(no DB / Redis / HTTP) to match the suite's unit style.
"""

import importlib
import inspect

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
async def test_workflow_runner_executes_graph_end_to_end():
    """A real two-node graph runs through WorkflowRunner -> node_executor ->
    CodeNode, with output flowing across the edge."""
    graph = {
        "nodes": [
            _code_node("n1", "output = {'value': 10}"),
            _code_node("n2", "output = {'final': input['value'] + 5}"),
        ],
        "edges": [{"source": "n1", "target": "n2"}],
    }

    runner = WorkflowRunner(workflow_id="wf-test", execution_id="exec-test", graph=graph)
    result = await runner.run(trigger_data={})

    assert runner._outputs["n1"]["value"] == 10
    assert result["final"] == 15


@pytest.mark.anyio
async def test_workflow_runner_raises_when_a_node_fails():
    """A failing node with no error-edge must surface as a failed run."""
    graph = {
        "nodes": [_code_node("boom", "raise ValueError('kaboom')")],
        "edges": [],
    }
    runner = WorkflowRunner(workflow_id="wf", execution_id="exec", graph=graph)
    with pytest.raises(Exception, match="kaboom"):
        await runner.run(trigger_data={})


@pytest.mark.anyio
async def test_execution_budget_bounds_runaway_graphs():
    """A shared node-execution budget makes runaway/cyclic graphs fail fast
    instead of hanging the worker."""

    def _set_var(node_id: str) -> dict:
        return {
            "id": node_id,
            "type": "logic.set_variable",
            "data": {"properties": {"key": node_id, "value": 1}},
        }

    graph = {
        "nodes": [_set_var("a"), _set_var("b"), _set_var("c")],
        "edges": [{"source": "a", "target": "b"}, {"source": "b", "target": "c"}],
    }
    runner = WorkflowRunner(
        workflow_id="wf", execution_id="exec", graph=graph, _budget={"remaining": 1}
    )
    with pytest.raises(Exception, match="maximum of"):
        await runner.run(trigger_data={})


@pytest.mark.anyio
async def test_error_edge_routes_failure_to_recovery_node():
    """A node failure follows an `error` edge to a recovery node instead of
    failing the whole run."""
    graph = {
        "nodes": [
            _code_node("boom", "raise RuntimeError('explode')"),
            _code_node("recover", "output = {'recovered': True}"),
        ],
        "edges": [{"source": "boom", "target": "recover", "sourceHandle": "error"}],
    }
    runner = WorkflowRunner(workflow_id="wf", execution_id="exec", graph=graph)
    result = await runner.run(trigger_data={})

    assert runner._outputs["recover"]["recovered"] is True
    assert result["recovered"] is True


def test_worker_runtime_imports_resolve():
    """The worker imports these lazily inside _run_workflow, so a stale path only
    surfaces at execution time. Importing them here fails fast in CI instead."""
    for module in (
        "apps.api.app.core.database",
        "apps.api.app.execution_engine.engine.event_emitter",
        "apps.api.app.execution_engine.engine.workflow_runner",
        "apps.api.app.features.executions.repository",
        "apps.api.app.features.workflows.repository",
        "apps.api.app.features.credentials.service",
        "apps.api.app.features.secrets.models",
        "apps.api.app.credential_manager.encryption.aes",
        "apps.worker.app.jobs.tasks",
    ):
        importlib.import_module(module)


def test_worker_matches_workflow_runner_and_repo_contract():
    """The worker constructs WorkflowRunner with these kwargs and calls these
    repo/service methods; guard against signature drift across the refactor."""
    params = set(inspect.signature(WorkflowRunner.__init__).parameters)
    assert {
        "workflow_id",
        "execution_id",
        "graph",
        "db",
        "on_log",
        "credentials",
        "emitter",
    } <= params

    from apps.api.app.features.credentials.service import CredentialService
    from apps.api.app.features.executions.repository import ExecutionRepository
    from apps.api.app.features.workflows.repository import WorkflowRepository

    for attr in ("add_log", "update_status", "save_pause"):
        assert hasattr(ExecutionRepository, attr)
    assert hasattr(WorkflowRepository, "get_by_id")
    assert hasattr(CredentialService, "list_decrypted_for_user")


def test_celery_registers_the_live_execute_workflow_task():
    """The API enqueues execute_workflow.delay(...); the live task must be
    registered under that exact name (not the deleted consumer twin)."""
    import apps.worker.app.jobs.tasks  # noqa: F401  registers the task
    from apps.api.app.core.celery import celery_app

    assert "execute_workflow" in celery_app.tasks
