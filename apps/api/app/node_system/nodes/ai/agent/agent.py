import json
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

OPENAI_CHAT_COMPLETIONS_URL = "https://api.openai.com/v1/chat/completions"
GROQ_CHAT_COMPLETIONS_URL = "https://api.groq.com/openai/v1/chat/completions"
ANTHROPIC_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
GOOGLE_GENERATE_CONTENT_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"

ProviderId = Literal["openai", "anthropic", "google", "groq"]
MemoryType = Literal["none", "workflow"]

PROVIDER_CREDENTIALS: dict[str, tuple[str, str, str]] = {
    "openai": ("openaiCredential", "openai_api_key", "OpenAI"),
    "anthropic": ("anthropicCredential", "anthropic_api_key", "Anthropic"),
    "google": ("googleCredential", "google_api_key", "Google Gemini"),
    "groq": ("groqCredential", "groq_api_key", "Groq"),
}

DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-3-5-sonnet-latest",
    "google": "gemini-1.5-flash",
    "groq": "llama-3.1-8b-instant",
}


class AgentMessage(BaseModel):
    role: str
    content: Any


class AgentProperties(BaseModel):
    provider: ProviderId = "openai"
    openaiCredential: str | None = None
    anthropicCredential: str | None = None
    googleCredential: str | None = None
    groqCredential: str | None = None
    model: str | None = None
    openaiModel: str = DEFAULT_MODELS["openai"]
    anthropicModel: str = DEFAULT_MODELS["anthropic"]
    googleModel: str = DEFAULT_MODELS["google"]
    groqModel: str = DEFAULT_MODELS["groq"]
    messages: list[AgentMessage] | str | None = Field(default_factory=list)
    tools: list[dict[str, Any]] | str | None = Field(default_factory=list)
    toolChoice: str = "auto"
    memoryType: MemoryType = "none"
    memoryKey: str | None = None
    memoryLimit: int = 10
    temperature: float | None = 0.3
    maxTokens: int | None = 4096
    responseFormat: dict[str, Any] | str | None = None
    timeout: int = 60000


class AgentNode(BaseNode[AgentProperties]):
    @classmethod
    def get_properties_model(cls) -> type[AgentProperties]:
        return AgentProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        provider_options = [
            {"label": "OpenAI", "value": "openai"},
            {"label": "Anthropic", "value": "anthropic"},
            {"label": "Google Gemini", "value": "google"},
            {"label": "Groq", "value": "groq"},
        ]

        return NodeMetadata(
            type="action.agent",
            name="Agent",
            category="ai",
            description="Run an AI agent with provider selection, tools, memory, and structured output.",
            icon="Bot",
            color="#8b5cf6",
            properties=[
                {
                    "name": "provider",
                    "label": "Provider",
                    "type": "options",
                    "default": "openai",
                    "options": provider_options,
                    "required": True,
                },
                *cls._provider_credential_properties(),
                {
                    "name": "model",
                    "label": "Model",
                    "type": "string",
                    "default": DEFAULT_MODELS["openai"],
                    "required": True,
                    "placeholder": "Type or select a model ID",
                    "loadOptions": "/ai/models",
                    "loadOptionsDependsOn": [
                        "provider",
                        "openaiCredential",
                        "anthropicCredential",
                        "googleCredential",
                        "groqCredential",
                    ],
                },
                {
                    "name": "messages",
                    "label": "Messages",
                    "type": "json",
                    "required": True,
                    "default": [
                        {"role": "system", "content": "You are a helpful workflow agent."},
                        {"role": "user", "content": "{{trigger.output}}"},
                    ],
                    "description": "Array of messages with role and content.",
                },
                {
                    "name": "tools",
                    "label": "Tools",
                    "type": "json",
                    "default": [],
                    "description": "Function tools: [{ name, description, parameters }].",
                },
                {
                    "name": "toolChoice",
                    "label": "Tool Choice",
                    "type": "options",
                    "default": "auto",
                    "options": [
                        {"label": "Auto", "value": "auto"},
                        {"label": "Required", "value": "required"},
                        {"label": "None", "value": "none"},
                    ],
                },
                {
                    "name": "memoryType",
                    "label": "Memory",
                    "type": "options",
                    "default": "none",
                    "options": [
                        {"label": "None", "value": "none"},
                        {"label": "Workflow", "value": "workflow"},
                    ],
                },
                {
                    "name": "memoryKey",
                    "label": "Memory Key",
                    "type": "string",
                    "placeholder": "customer-123",
                    "condition": {"field": "memoryType", "value": "workflow"},
                },
                {
                    "name": "memoryLimit",
                    "label": "Memory Limit",
                    "type": "number",
                    "default": 10,
                    "condition": {"field": "memoryType", "value": "workflow"},
                },
                {
                    "name": "temperature",
                    "label": "Temperature",
                    "type": "number",
                    "default": 0.3,
                },
                {
                    "name": "maxTokens",
                    "label": "Max Output Tokens",
                    "type": "number",
                    "default": 4096,
                },
                {
                    "name": "responseFormat",
                    "label": "Response Format",
                    "type": "json",
                    "required": False,
                    "description": "Optional JSON Schema or provider response-format object.",
                },
                {
                    "name": "timeout",
                    "label": "Timeout (ms)",
                    "type": "number",
                    "default": 60000,
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "content", "type": "string"},
                {"label": "provider", "type": "string"},
                {"label": "model", "type": "string"},
                {"label": "tokens", "type": "object"},
                {"label": "toolCalls", "type": "array"},
                {"label": "structured", "type": "object"},
                {"label": "memory", "type": "array"},
                {"label": "raw", "type": "object"},
            ],
            allow_error=True,
        )

    @classmethod
    def _provider_credential_properties(cls) -> list[dict[str, Any]]:
        return [
            {
                "name": "openaiCredential",
                "label": "OpenAI API Key",
                "type": "credential",
                "credentialType": "openai_api_key",
                "required": {"field": "provider", "value": "openai"},
                "condition": {"field": "provider", "value": "openai"},
            },
            {
                "name": "anthropicCredential",
                "label": "Anthropic API Key",
                "type": "credential",
                "credentialType": "anthropic_api_key",
                "required": {"field": "provider", "value": "anthropic"},
                "condition": {"field": "provider", "value": "anthropic"},
            },
            {
                "name": "googleCredential",
                "label": "Google API Key",
                "type": "credential",
                "credentialType": "google_api_key",
                "required": {"field": "provider", "value": "google"},
                "condition": {"field": "provider", "value": "google"},
            },
            {
                "name": "groqCredential",
                "label": "Groq API Key",
                "type": "credential",
                "credentialType": "groq_api_key",
                "required": {"field": "provider", "value": "groq"},
                "condition": {"field": "provider", "value": "groq"},
            },
        ]

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            api_key = self._get_api_key(context)
            if not api_key:
                provider_name = PROVIDER_CREDENTIALS[self.props.provider][2]
                return NodeResult(success=False, error=f"{provider_name} API key credential is required.")

            messages = self._normalize_messages(input_data)
            messages = self._apply_memory(messages, context)
            if not messages:
                return NodeResult(success=False, error="At least one agent message is required.")

            tools = self._normalize_tools()
            model = self._selected_model()
            timeout_seconds = self.props.timeout / 1000.0
            client = context.http_client or httpx.AsyncClient(timeout=timeout_seconds)

            try:
                if self.props.provider == "openai":
                    data = await self._execute_openai_compatible(
                        client=client,
                        url=OPENAI_CHAT_COMPLETIONS_URL,
                        api_key=api_key,
                        model=model,
                        messages=messages,
                        tools=tools,
                    )
                    output = self._build_openai_compatible_output(data, model)
                elif self.props.provider == "groq":
                    data = await self._execute_openai_compatible(
                        client=client,
                        url=GROQ_CHAT_COMPLETIONS_URL,
                        api_key=api_key,
                        model=model,
                        messages=messages,
                        tools=tools,
                    )
                    output = self._build_openai_compatible_output(data, model)
                elif self.props.provider == "anthropic":
                    data = await self._execute_anthropic(
                        client=client,
                        api_key=api_key,
                        model=model,
                        messages=messages,
                        tools=tools,
                    )
                    output = self._build_anthropic_output(data, model)
                else:
                    data = await self._execute_google(
                        client=client,
                        api_key=api_key,
                        model=model,
                        messages=messages,
                        tools=tools,
                    )
                    output = self._build_google_output(data, model)
            finally:
                if not context.http_client:
                    await client.aclose()

            output["provider"] = self.props.provider
            output["memory"] = self._persist_memory(messages, output.get("content", ""), context)
            return NodeResult(success=True, output_data=output)
        except httpx.HTTPStatusError as e:
            return NodeResult(success=False, error=self._extract_provider_error(e.response))
        except httpx.TimeoutException:
            return NodeResult(success=False, error=f"Agent request timed out after {self.props.timeout}ms")
        except Exception as e:
            logger.error(f"AgentNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    async def _execute_openai_compatible(
        self,
        client: httpx.AsyncClient,
        url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "model": model,
            "messages": messages,
        }

        if self.props.temperature is not None:
            payload["temperature"] = self.props.temperature
        if self.props.maxTokens is not None:
            payload["max_tokens"] = self.props.maxTokens

        response_format = self._normalize_response_format("openai")
        if response_format is not None:
            payload["response_format"] = response_format

        if tools:
            payload["tools"] = [self._to_openai_tool(tool) for tool in tools]
            if self.props.toolChoice == "required":
                payload["tool_choice"] = "required"
            elif self.props.toolChoice == "none":
                payload["tool_choice"] = "none"
            else:
                payload["tool_choice"] = "auto"

        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=None,
        )
        response.raise_for_status()
        return response.json()

    async def _execute_anthropic(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        system_prompt, anthropic_messages = self._to_anthropic_messages(messages)
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": self.props.maxTokens or 4096,
            "messages": anthropic_messages,
        }

        if system_prompt:
            payload["system"] = system_prompt
        if self.props.temperature is not None:
            payload["temperature"] = self.props.temperature
        if tools:
            payload["tools"] = [self._to_anthropic_tool(tool) for tool in tools]
            if self.props.toolChoice == "required":
                payload["tool_choice"] = {"type": "any"}
            elif self.props.toolChoice == "auto":
                payload["tool_choice"] = {"type": "auto"}

        response = await client.post(
            ANTHROPIC_MESSAGES_URL,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=None,
        )
        response.raise_for_status()
        return response.json()

    async def _execute_google(
        self,
        client: httpx.AsyncClient,
        api_key: str,
        model: str,
        messages: list[dict[str, str]],
        tools: list[dict[str, Any]],
    ) -> dict[str, Any]:
        system_prompt, contents = self._to_google_contents(messages)
        generation_config: dict[str, Any] = {}

        if self.props.temperature is not None:
            generation_config["temperature"] = self.props.temperature
        if self.props.maxTokens is not None:
            generation_config["maxOutputTokens"] = self.props.maxTokens

        response_schema = self._normalize_response_format("google")
        if response_schema is not None:
            generation_config["responseMimeType"] = "application/json"
            generation_config["responseSchema"] = response_schema

        payload: dict[str, Any] = {
            "contents": contents,
        }
        if generation_config:
            payload["generationConfig"] = generation_config
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if tools:
            payload["tools"] = [{"functionDeclarations": [self._to_google_tool(tool) for tool in tools]}]

        response = await client.post(
            GOOGLE_GENERATE_CONTENT_URL.format(model=self._google_model_path(model)),
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=None,
        )
        response.raise_for_status()
        return response.json()

    def _get_api_key(self, context: NodeContext) -> str | None:
        credential_field, credential_type, _provider_name = PROVIDER_CREDENTIALS[self.props.provider]
        selected_credential_id = getattr(self.props, credential_field)
        credentials = context.credentials or []

        credential = None
        if selected_credential_id:
            credential = next(
                (
                    item
                    for item in credentials
                    if str(item.get("id")) == str(selected_credential_id)
                    and item.get("type") == credential_type
                ),
                None,
            )

        if credential is None:
            credential = next((item for item in credentials if item.get("type") == credential_type), None)

        data = credential.get("data") if credential else None
        if not isinstance(data, dict):
            return None
        api_key = data.get("api_key")
        return api_key if isinstance(api_key, str) and api_key.strip() else None

    def _selected_model(self) -> str:
        if self.props.model:
            return self.props.model
        field_name = f"{self.props.provider}Model"
        model = getattr(self.props, field_name)
        return model or DEFAULT_MODELS[self.props.provider]

    def _google_model_path(self, model: str) -> str:
        return model.removeprefix("models/")

    def _normalize_messages(self, input_data: dict[str, Any]) -> list[dict[str, str]]:
        raw_messages = self.props.messages

        if isinstance(raw_messages, str):
            raw_messages = raw_messages.strip()
            if raw_messages:
                try:
                    parsed_messages = json.loads(raw_messages)
                except json.JSONDecodeError:
                    parsed_messages = [{"role": "user", "content": raw_messages}]
            else:
                parsed_messages = []
        else:
            parsed_messages = raw_messages or []

        if not parsed_messages:
            parsed_messages = [{"role": "user", "content": self._stringify_content(input_data)}]

        messages: list[dict[str, str]] = []
        for message in parsed_messages:
            if isinstance(message, AgentMessage):
                role = message.role
                content = message.content
            elif isinstance(message, dict):
                role = message.get("role", "user")
                content = message.get("content", "")
            else:
                role = "user"
                content = message

            messages.append({"role": self._normalize_role(role), "content": self._stringify_content(content)})

        return messages

    def _normalize_tools(self) -> list[dict[str, Any]]:
        raw_tools = self.props.tools
        if raw_tools in (None, ""):
            return []

        if isinstance(raw_tools, str):
            try:
                raw_tools = json.loads(raw_tools)
            except json.JSONDecodeError as e:
                raise ValueError(f"Tools must be valid JSON: {e.msg}") from e

        if not isinstance(raw_tools, list):
            raise ValueError("Tools must be a JSON array.")

        tools = []
        for tool in raw_tools:
            if not isinstance(tool, dict):
                raise ValueError("Each tool must be an object.")
            name = tool.get("name") or tool.get("function", {}).get("name")
            if not isinstance(name, str) or not name:
                raise ValueError("Each tool must have a name.")
            tools.append(tool)
        return tools

    def _normalize_response_format(self, provider: str) -> dict[str, Any] | None:
        raw_format = self.props.responseFormat
        if raw_format in (None, ""):
            return None

        if isinstance(raw_format, str):
            try:
                raw_format = json.loads(raw_format)
            except json.JSONDecodeError as e:
                raise ValueError(f"Response Format must be valid JSON: {e.msg}") from e

        if not isinstance(raw_format, dict) or not raw_format:
            return None

        if provider == "google":
            schema = raw_format.get("schema") if isinstance(raw_format.get("schema"), dict) else raw_format
            return schema

        if isinstance(raw_format.get("type"), str):
            return raw_format

        schema = raw_format.get("schema") if isinstance(raw_format.get("schema"), dict) else raw_format
        name = raw_format.get("name", "agent_response")
        strict = raw_format.get("strict", True)

        return {
            "type": "json_schema",
            "json_schema": {
                "name": name,
                "schema": schema,
                "strict": strict,
            },
        }

    def _apply_memory(
        self, messages: list[dict[str, str]], context: NodeContext
    ) -> list[dict[str, str]]:
        if self.props.memoryType == "none":
            return messages
        memory = self._get_memory(context)
        return [*memory, *messages]

    def _persist_memory(
        self, messages: list[dict[str, str]], assistant_content: str, context: NodeContext
    ) -> list[dict[str, str]]:
        if self.props.memoryType == "none":
            return []

        memory = self._get_memory(context)
        new_items = [message for message in messages if message["role"] in {"user", "assistant"}]
        if assistant_content:
            new_items.append({"role": "assistant", "content": assistant_content})

        memory = [*memory, *new_items][-max(self.props.memoryLimit, 1) :]
        context.variables[self._memory_variable_key()] = memory
        return memory

    def _get_memory(self, context: NodeContext) -> list[dict[str, str]]:
        memory = context.variables.get(self._memory_variable_key(), [])
        if not isinstance(memory, list):
            return []

        normalized_memory = []
        for message in memory:
            if isinstance(message, dict) and {"role", "content"} <= set(message):
                normalized_memory.append(
                    {
                        "role": self._normalize_role(message["role"]),
                        "content": self._stringify_content(message["content"]),
                    }
                )
        return normalized_memory[-max(self.props.memoryLimit, 1) :]

    def _memory_variable_key(self) -> str:
        memory_key = self.props.memoryKey or self.node_id
        return f"agent_memory:{memory_key}"

    def _to_openai_tool(self, tool: dict[str, Any]) -> dict[str, Any]:
        if tool.get("type") == "function" and isinstance(tool.get("function"), dict):
            return tool
        return {
            "type": "function",
            "function": {
                "name": tool["name"],
                "description": tool.get("description", ""),
                "parameters": tool.get("parameters") or {"type": "object", "properties": {}},
            },
        }

    def _to_anthropic_tool(self, tool: dict[str, Any]) -> dict[str, Any]:
        function = tool.get("function") if isinstance(tool.get("function"), dict) else tool
        return {
            "name": function["name"],
            "description": function.get("description", ""),
            "input_schema": function.get("parameters") or {"type": "object", "properties": {}},
        }

    def _to_google_tool(self, tool: dict[str, Any]) -> dict[str, Any]:
        function = tool.get("function") if isinstance(tool.get("function"), dict) else tool
        return {
            "name": function["name"],
            "description": function.get("description", ""),
            "parameters": function.get("parameters") or {"type": "object", "properties": {}},
        }

    def _to_anthropic_messages(
        self, messages: list[dict[str, str]]
    ) -> tuple[str | None, list[dict[str, str]]]:
        system_messages = [message["content"] for message in messages if message["role"] == "system"]
        chat_messages = [
            {
                "role": "assistant" if message["role"] == "assistant" else "user",
                "content": message["content"],
            }
            for message in messages
            if message["role"] != "system"
        ]
        return ("\n\n".join(system_messages) or None, chat_messages)

    def _to_google_contents(
        self, messages: list[dict[str, str]]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        system_messages = [message["content"] for message in messages if message["role"] == "system"]
        contents = []
        for message in messages:
            if message["role"] == "system":
                continue
            role = "model" if message["role"] == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message["content"]}]})
        return ("\n\n".join(system_messages) or None, contents)

    def _build_openai_compatible_output(self, data: dict[str, Any], model: str) -> dict[str, Any]:
        choices = data.get("choices") or []
        first_choice = choices[0] if choices else {}
        message = first_choice.get("message") or {}
        content = message.get("content") or ""
        tool_calls = message.get("tool_calls") or []
        return self._build_output(content, data.get("model", model), data.get("usage") or {}, tool_calls, data)

    def _build_anthropic_output(self, data: dict[str, Any], model: str) -> dict[str, Any]:
        content_blocks = data.get("content") or []
        text_parts = []
        tool_calls = []
        for block in content_blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    {
                        "id": block.get("id"),
                        "name": block.get("name"),
                        "arguments": block.get("input") or {},
                    }
                )

        usage = data.get("usage") or {}
        tokens = {
            "prompt_tokens": usage.get("input_tokens"),
            "completion_tokens": usage.get("output_tokens"),
            "total_tokens": (usage.get("input_tokens") or 0) + (usage.get("output_tokens") or 0),
        }
        return self._build_output("".join(text_parts), data.get("model", model), tokens, tool_calls, data)

    def _build_google_output(self, data: dict[str, Any], model: str) -> dict[str, Any]:
        candidates = data.get("candidates") or []
        first_candidate = candidates[0] if candidates else {}
        parts = first_candidate.get("content", {}).get("parts", [])
        text_parts = []
        tool_calls = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            if "text" in part:
                text_parts.append(part["text"])
            if "functionCall" in part:
                call = part["functionCall"]
                tool_calls.append({"name": call.get("name"), "arguments": call.get("args") or {}})

        usage = data.get("usageMetadata") or {}
        tokens = {
            "prompt_tokens": usage.get("promptTokenCount"),
            "completion_tokens": usage.get("candidatesTokenCount"),
            "total_tokens": usage.get("totalTokenCount"),
        }
        return self._build_output("".join(text_parts), model, tokens, tool_calls, data)

    def _build_output(
        self,
        content: str,
        model: str,
        tokens: dict[str, Any],
        tool_calls: list[dict[str, Any]],
        raw: dict[str, Any],
    ) -> dict[str, Any]:
        structured = self._try_parse_json(content)

        output: dict[str, Any] = {}
        if isinstance(structured, dict):
            output.update(structured)

        output.update(
            {
                "content": content,
                "model": model,
                "tokens": tokens,
                "toolCalls": tool_calls,
                "structured": structured,
                "raw": raw,
            }
        )
        return output

    def _extract_provider_error(self, response: httpx.Response) -> str:
        provider_name = PROVIDER_CREDENTIALS[self.props.provider][2]
        try:
            body = response.json()
            if isinstance(body, dict):
                error = body.get("error")
                if isinstance(error, dict) and error.get("message"):
                    return f"{provider_name} API error: {error['message']}"
                if isinstance(error, str):
                    return f"{provider_name} API error: {error}"
        except ValueError:
            pass
        return f"{provider_name} API error: HTTP {response.status_code}"

    def _normalize_role(self, role: Any) -> str:
        role_text = str(role)
        if role_text in {"system", "user", "assistant"}:
            return role_text
        return "user"

    def _stringify_content(self, value: Any) -> str:
        if isinstance(value, str):
            return value
        return json.dumps(value, default=str)

    def _try_parse_json(self, value: str) -> Any:
        if not value:
            return None
        try:
            return json.loads(value)
        except json.JSONDecodeError:
            return None
