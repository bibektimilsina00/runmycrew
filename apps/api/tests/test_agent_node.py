import json
from typing import Any

import httpx
import pytest

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.nodes.ai.agent.agent import AgentNode


def test_agent_model_field_uses_generic_dynamic_options_contract():
    metadata = AgentNode.get_metadata()
    provider_property = next(prop for prop in metadata.properties if prop["name"] == "provider")
    credential_property = next(prop for prop in metadata.properties if prop["name"] == "credential")
    model_property = next(prop for prop in metadata.properties if prop["name"] == "model")

    # Provider + model use the searchable+allowCustom combobox now so the
    # inspector renders a real picker instead of a plain text input. The
    # static `options` array stays absent — choices come from `loadOptions`.
    assert provider_property["type"] == "options"
    assert provider_property["loadOptions"] == "/ai/providers"
    assert provider_property["typeOptions"] == {"searchable": True, "allowCustom": True}
    assert "options" not in provider_property
    assert credential_property["credentialTypeByField"]["field"] == "provider"
    assert (
        credential_property["credentialTypeByField"]["values"]["openrouter"] == "openrouter_api_key"
    )
    assert model_property["type"] == "options"
    assert model_property["typeOptions"] == {"searchable": True, "allowCustom": True}
    assert model_property["loadOptions"] == "/ai/models"
    assert model_property["loadOptionsDependsOn"] == ["provider", "credential"]
    assert not any(prop["name"].endswith("Model") for prop in metadata.properties)


def test_agent_messages_field_uses_messages_editor_contract():
    metadata = AgentNode.get_metadata()
    messages_property = next(prop for prop in metadata.properties if prop["name"] == "messages")

    assert messages_property["type"] == "messages"
    assert messages_property["default"] == [{"role": "user", "content": "{{$step}}"}]


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
                            "content": '{"answer":"done"}',
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
                "credential": "cred-1",
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
    assert request_body["messages"][-1] == {"role": "user", "content": "Summarize this"}
    assert request_body["temperature"] == 0.2
    assert request_body["max_tokens"] == 512
    assert result.output_data["provider"] == "openai"
    assert result.output_data["content"] == '{"answer":"done"}'
    assert result.output_data["answer"] == "done"
    assert result.output_data["tokens"]["total_tokens"] == 15


@pytest.mark.anyio
async def test_agent_node_requires_selected_provider_credential():
    async with httpx.AsyncClient(
        transport=httpx.MockTransport(lambda request: httpx.Response(200))
    ) as client:
        node = AgentNode(
            node_id="agent-1",
            properties={"provider": "anthropic", "messages": "Hello"},
        )

        result = await node.execute({}, make_context(client))

    assert result.success is False
    assert result.error == "Anthropic API key credential is required."


@pytest.mark.anyio
async def test_agent_node_sends_anthropic_request_with_tools():
    captured_payloads: list[dict[str, Any]] = []
    captured_headers: list[dict[str, str]] = []

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_headers.append(dict(request.headers))
        payload = json.loads(request.read())
        captured_payloads.append(payload)

        # On first request (which requires lookup), return tool use
        # On subsequent request (summarization), return text response so it stops looping
        if len(captured_payloads) == 1:
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
        else:
            return httpx.Response(
                200,
                json={
                    "model": "claude-3-5-sonnet-latest",
                    "content": [
                        {"type": "text", "text": "Need lookup"},
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
    assert captured_headers[0]["x-api-key"] == "sk-ant-test"
    assert captured_payloads[0]["system"] == "Be concise."
    assert captured_payloads[0]["messages"] == [{"role": "user", "content": "Find customer 123."}]
    assert captured_payloads[0]["tools"][0]["name"] == "lookup_customer"
    assert captured_payloads[0]["tool_choice"] == {"type": "any"}
    assert result.output_data["provider"] == "anthropic"
    assert result.output_data["content"] == "Need lookup"
    # Tool calls carry a per-call `duration_ms` (PR7) — the value is
    # non-deterministic so we strip it from the assertion.
    actual_calls = [
        {k: v for k, v in tc.items() if k != "duration_ms"}
        for tc in result.output_data["toolCalls"]
    ]
    assert actual_calls == [
        {
            "id": "toolu_1",
            "name": "lookup_customer",
            "arguments": {"id": "123"},
            "success": False,
            "result": {"error": "Unknown tool: lookup_customer"},
        }
    ]
    assert all("duration_ms" in tc for tc in result.output_data["toolCalls"])
    assert result.output_data["tokens"]["total_tokens"] == 13


@pytest.mark.anyio
async def test_agent_node_sends_google_request_with_response_schema_and_memory():
    captured_payloads: list[dict[str, Any]] = []
    captured_params: list[dict[str, str]] = []
    variables = {
        "agent_memory:support": [{"role": "user", "content": "Earlier question"}],
    }

    async def handler(request: httpx.Request) -> httpx.Response:
        captured_params.append(dict(request.url.params))
        payload = json.loads(request.read())
        captured_payloads.append(payload)

        # On first request, return function call and text
        # On subsequent request, return only text so it stops looping
        if len(captured_payloads) == 1:
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": '{"status":"ok"}'},
                                    {
                                        "functionCall": {
                                            "name": "search_docs",
                                            "args": {"q": "billing"},
                                        }
                                    },
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
        else:
            return httpx.Response(
                200,
                json={
                    "candidates": [
                        {
                            "content": {
                                "parts": [
                                    {"text": '{"status":"ok"}'},
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
    assert captured_params[0]["key"] == "google-test"
    assert captured_payloads[0]["systemInstruction"] == {"parts": [{"text": "Return JSON."}]}
    assert captured_payloads[0]["contents"][0] == {
        "role": "user",
        "parts": [{"text": "Earlier question"}],
    }
    assert captured_payloads[0]["generationConfig"]["responseMimeType"] == "application/json"
    assert captured_payloads[0]["tools"][0]["functionDeclarations"][0]["name"] == "search_docs"
    assert result.output_data["provider"] == "google"
    assert result.output_data["status"] == "success"
    # Strip the non-deterministic `duration_ms` added by PR7.
    google_actual = [
        {k: v for k, v in tc.items() if k != "duration_ms"}
        for tc in result.output_data["toolCalls"]
    ]
    assert google_actual == [
        {
            "id": "search_docs",
            "name": "search_docs",
            "arguments": {"q": "billing"},
            "success": False,
            "result": {"error": "Unknown tool: search_docs"},
        }
    ]
    assert variables["agent_memory:support"][-1] == {
        "role": "assistant",
        "content": '{"status":"ok"}',
    }
