"""Unit tests for core, functional workflow nodes.

Covers the most-used primitives — set-variable, JSON transform, and HTTP
request — in the suite's infra-free style (NodeContext + httpx MockTransport).
"""

from typing import Any

import httpx
import pytest

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.nodes.common.json_transform.json_transform import JsonTransformNode
from apps.api.app.node_system.nodes.common.set_variable.set_variable import SetVariableNode
from apps.api.app.node_system.nodes.http.request.request import HttpRequestNode


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def make_context(
    client: httpx.AsyncClient | None = None,
    variables: dict[str, Any] | None = None,
) -> NodeContext:
    return NodeContext(
        execution_id="exec-1",
        workflow_id="wf-1",
        node_id="node-1",
        variables=variables if variables is not None else {},
        credentials=[],
        http_client=client,
        db=None,
    )


@pytest.mark.anyio
async def test_set_variable_writes_to_shared_variables():
    variables: dict[str, Any] = {}
    node = SetVariableNode(node_id="sv-1", properties={"key": "greeting", "value": "hi"})

    result = await node.execute({"carry": 1}, make_context(variables=variables))

    assert result.success is True
    assert variables["greeting"] == "hi"  # mutated shared execution variables
    assert result.output_data["key"] == "greeting"
    assert result.output_data["value"] == "hi"
    assert result.output_data["carry"] == 1  # input is spread through


@pytest.mark.anyio
async def test_set_variable_requires_key():
    node = SetVariableNode(node_id="sv-1", properties={"key": "", "value": "x"})
    result = await node.execute({}, make_context())
    assert result.success is False
    assert "key" in (result.error or "").lower()


@pytest.mark.anyio
async def test_json_transform_renders_jinja_template():
    node = JsonTransformNode(
        node_id="jt-1",
        properties={"template": {"greeting": "Hello {{ input.name }}", "n": "{{ input.count }}"}},
    )
    result = await node.execute({"name": "World", "count": 3}, make_context())

    assert result.success is True
    assert result.output_data["result"]["greeting"] == "Hello World"


@pytest.mark.anyio
async def test_http_request_returns_parsed_response():
    captured: dict[str, Any] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["method"] = request.method
        captured["url"] = str(request.url)
        return httpx.Response(200, json={"ok": True, "id": 42})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        node = HttpRequestNode(
            node_id="h-1",
            properties={"url": "https://api.test/users", "method": "GET"},
        )
        result = await node.execute({}, make_context(client))

    assert result.success is True
    assert captured["method"] == "GET"
    assert result.output_data["status_code"] == 200
    assert result.output_data["ok"] is True
    assert result.output_data["body"] == {"ok": True, "id": 42}


@pytest.mark.anyio
async def test_http_request_substitutes_path_params():
    captured: dict[str, Any] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured["path"] = request.url.path
        return httpx.Response(200, json={})

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        node = HttpRequestNode(
            node_id="h-2",
            properties={
                "url": "https://api.test/users/:id",
                "method": "GET",
                "pathParams": {"id": "42"},
            },
        )
        result = await node.execute({}, make_context(client))

    assert result.success is True
    assert captured["path"] == "/users/42"
