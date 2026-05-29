"""Tests for CodeNode sandbox hardening (phase A: process isolation + limits).

Proves user code runs in a separate process that (a) cannot see the worker's
environment/secrets, (b) is killed on timeout, and (c) surfaces errors cleanly —
while normal code still produces output.
"""

import os

import pytest

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.nodes.logic.code.code_node import CodeNode


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def _ctx() -> NodeContext:
    return NodeContext(
        execution_id="e",
        workflow_id="w",
        node_id="code-1",
        variables={},
        credentials=[],
        http_client=None,
        db=None,
    )


def _node(code: str, timeout: int = 30) -> CodeNode:
    return CodeNode(
        node_id="code-1", properties={"language": "python", "code": code, "timeout": timeout}
    )


@pytest.mark.anyio
async def test_python_code_executes_in_subprocess():
    result = await _node("output = {'sum': 2 + 3}").execute({}, _ctx())
    assert result.success is True
    assert result.output_data["sum"] == 5


@pytest.mark.anyio
async def test_worker_env_secrets_are_not_visible_to_user_code():
    """The defining security property of phase A: a worker env var (e.g. a
    secret) must NOT be readable from sandboxed user code."""
    os.environ["FUSE_SANDBOX_CANARY"] = "leaked-secret"
    try:
        result = await _node(
            "import os\noutput = {'seen': os.environ.get('FUSE_SANDBOX_CANARY')}"
        ).execute({}, _ctx())
    finally:
        os.environ.pop("FUSE_SANDBOX_CANARY", None)

    assert result.success is True
    assert result.output_data["seen"] is None  # clean env — secret not propagated


@pytest.mark.anyio
async def test_runaway_code_is_killed_on_timeout():
    result = await _node("import time\ntime.sleep(10)", timeout=1).execute({}, _ctx())
    assert result.success is False
    assert "timed out" in (result.error or "").lower()


@pytest.mark.anyio
async def test_user_exception_surfaces_as_failure():
    result = await _node("raise ValueError('boom')").execute({}, _ctx())
    assert result.success is False
    assert "boom" in (result.error or "")
