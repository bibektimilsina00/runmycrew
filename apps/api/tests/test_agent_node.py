import json
from typing import Any

import httpx
import pytest

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.nodes.ai.agent.agent import AgentNode


def test_agent_model_field_uses_generic_dynamic_options_contract():
    metadata = AgentNode.get_metadata()
    model_property = next(prop for prop in metadata.properties if prop["name"] == "model")

    assert model_property["type"] == "string"
    assert model_property["loadOptions"] == "/ai/models"
    assert model_property["loadOptionsDependsOn"] == [
        "provider",
        "openaiCredential",
        "anthropicCredential",
        "googleCredential",
        "groqCredential",
    ]
    assert not any(prop["name"].endswith("Model") for prop in metadata.properties)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def make_context(
    client: httpx.AsyncClient,
    credentials: list[dict[str, Any]] | None = None,
    variables: dict[str, Any] | None = None,
) -> NodeContext:
    return NodeContext(
        execution_id="execution-1",
        workflow_id="workflow-1",
        node_id="agent-1",
        variables=variables or {},
        credentials=credentials or [],
        http_client=client,
        db=None,
    )


@pytest.mark.anyio
async def test_agent_node_sends_openai_request_and_returns_output():
    captured_request: dict[str, Any] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_request["headers"] = dict(request.headers)
        captured_request["json"] = request.read()
        return httpx.Response(
            200,
            json={
                "id": "chatcmpl-1",
                "model": "gpt-4o-mini",
                "choices": [
                    {
                        "message": {
                            "role": "assistant",
                            "content": "{\"answer\":\"done\"}",
                        }
                    }
                ],
                "usage": {"prompt_tokens": 10, "completion_tokens": 5, "total_tokens": 15},
            },
        )

    credentials = [
        {"id": "cred-1", "type": "openai_api_key", "data": {"api_key": "sk-test"}},
    ]

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        node = AgentNode(
            node_id="agent-1",
            properties={
                "provider": "openai",
                "openaiCredential": "cred-1",
                "model": "gpt-4o-mini",
                "messages": [{"role": "user", "content": "Summarize this"}],
                "temperature": 0.2,
                "maxTokens": 512,
            },
        )

        result = await node.execute({"input": "hello"}, make_context(client, credentials))

    request_body = json.loads(captured_request["json"])

    assert result.success is True
    assert captured_request["headers"]["authorization"] == "Bearer sk-test"
    assert request_body["model"] == "gpt-4o-mini"
    assert request_body["messages"] == [{"role": "user", "content": "Summarize this"}]
    assert request_body["temperature"] == 0.2
    assert request_body["max_tokens"] == 512
    assert result.output_data["provider"] == "openai"
    assert result.output_data["content"] == "{\"answer\":\"done\"}"
    assert result.output_data["answer"] == "done"
    assert result.output_data["tokens"]["total_tokens"] == 15


@pytest.mark.anyio
async def test_agent_node_requires_selected_provider_credential():
    async with httpx.AsyncClient(transport=httpx.MockTransport(lambda request: httpx.Response(200))) as client:
        node = AgentNode(
            node_id="agent-1",
            properties={"provider": "anthropic", "messages": "Hello"},
        )

        result = await node.execute({}, make_context(client))

    assert result.success is False
    assert result.error == "Anthropic API key credential is required."


@pytest.mark.anyio
async def test_agent_node_sends_anthropic_request_with_tools():
    captured_payload: dict[str, Any] = {}
    captured_headers: dict[str, str] = {}

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.update(dict(request.headers))
        captured_payload.update(json.loads(request.read()))
        return httpx.Response(
            200,
            json={
                "model": "claude-3-5-sonnet-latest",
                "content": [
                    {"type": "text", "text": "Need lookup"},
                    {
                        "type": "tool_use",
                        "id": "toolu_1",
                        "name": "lookup_customer",
                        "input": {"id": "123"},
                    },
                ],
                "usage": {"input_tokens": 9, "output_tokens": 4},
            },
        )

    credentials = [
        {"id": "cred-2", "type": "anthropic_api_key", "data": {"api_key": "sk-ant-test"}},
    ]

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        node = AgentNode(
            node_id="agent-1",
            properties={
                "provider": "anthropic",
                "anthropicCredential": "cred-2",
                "model": "claude-3-5-sonnet-latest",
                "messages": [
                    {"role": "system", "content": "Be concise."},
                    {"role": "user", "content": "Find customer 123."},
                ],
                "tools": [
                    {
                        "name": "lookup_customer",
                        "description": "Find customer details.",
                        "parameters": {
                            "type": "object",
                            "properties": {"id": {"type": "string"}},
                            "required": ["id"],
                        },
                    }
                ],
                "toolChoice": "required",
            },
        )

        result = await node.execute({}, make_context(client, credentials))

    assert result.success is True
    assert captured_headers["x-api-key"] == "sk-ant-test"
    assert captured_payload["system"] == "Be concise."
    assert captured_payload["messages"] == [{"role": "user", "content": "Find customer 123."}]
    assert captured_payload["tools"][0]["name"] == "lookup_customer"
    assert captured_payload["tool_choice"] == {"type": "any"}
    assert result.output_data["provider"] == "anthropic"
    assert result.output_data["content"] == "Need lookup"
    assert result.output_data["toolCalls"] == [
        {"id": "toolu_1", "name": "lookup_customer", "arguments": {"id": "123"}}
    ]
    assert result.output_data["tokens"]["total_tokens"] == 13


@pytest.mark.anyio
async def test_agent_node_sends_google_request_with_response_schema_and_memory():
    captured_payload: dict[str, Any] = {}
    captured_params: dict[str, str] = {}
    variables = {
        "agent_memory:support": [{"role": "user", "content": "Earlier question"}],
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_params.update(dict(request.url.params))
        captured_payload.update(json.loads(request.read()))
        return httpx.Response(
            200,
            json={
                "candidates": [
                    {
                        "content": {
                            "parts": [
                                {"text": "{\"status\":\"ok\"}"},
                                {"functionCall": {"name": "search_docs", "args": {"q": "billing"}}},
                            ]
                        }
                    }
                ],
                "usageMetadata": {
                    "promptTokenCount": 11,
                    "candidatesTokenCount": 6,
                    "totalTokenCount": 17,
                },
            },
        )

    credentials = [
        {"id": "cred-3", "type": "google_api_key", "data": {"api_key": "google-test"}},
    ]

    async with httpx.AsyncClient(transport=httpx.MockTransport(handler)) as client:
        node = AgentNode(
            node_id="agent-1",
            properties={
                "provider": "google",
                "googleCredential": "cred-3",
                "model": "gemini-1.5-flash",
                "messages": [
                    {"role": "system", "content": "Return JSON."},
                    {"role": "user", "content": "Current question"},
                ],
                "memoryType": "workflow",
                "memoryKey": "support",
                "memoryLimit": 4,
                "responseFormat": {
                    "schema": {
                        "type": "object",
                        "properties": {"status": {"type": "string"}},
                        "required": ["status"],
                    }
                },
                "tools": [{"name": "search_docs", "parameters": {"type": "object"}}],
            },
        )

        result = await node.execute({}, make_context(client, credentials, variables))

    assert result.success is True
    assert captured_params["key"] == "google-test"
    assert captured_payload["systemInstruction"] == {"parts": [{"text": "Return JSON."}]}
    assert captured_payload["contents"][0] == {
        "role": "user",
        "parts": [{"text": "Earlier question"}],
    }
    assert captured_payload["generationConfig"]["responseMimeType"] == "application/json"
    assert captured_payload["tools"][0]["functionDeclarations"][0]["name"] == "search_docs"
    assert result.output_data["provider"] == "google"
    assert result.output_data["status"] == "ok"
    assert result.output_data["toolCalls"] == [{"name": "search_docs", "arguments": {"q": "billing"}}]
    assert variables["agent_memory:support"][-1] == {"role": "assistant", "content": "{\"status\":\"ok\"}"}
