from __future__ import annotations

import json
import time
from typing import Any, Literal

import httpx
from pydantic import BaseModel, Field

from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.api_keys import get_ai_provider, get_ai_providers
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)

MemoryType = Literal["none", "workflow"]


def _retry_from_dict(d: Any) -> Any:
    """Materialise a `ToolRetryConfig` from a saved user-override dict.

    Returns ``None`` when no override is provided (the tool's built-in
    config wins). Unknown / missing fields fall back to the
    `ToolRetryConfig` defaults so a partial override (just ``max_retries``,
    for example) does the sensible thing.
    """
    if not isinstance(d, dict) or not d.get("enabled"):
        return None
    from apps.api.app.node_system.tools.base import ToolRetryConfig

    return ToolRetryConfig(
        enabled=True,
        max_retries=int(d.get("max_retries", 3)),
        initial_delay_ms=int(d.get("initial_delay_ms", 1000)),
        max_delay_ms=int(d.get("max_delay_ms", 10000)),
    )


class AgentMessage(BaseModel):
    role: str
    content: Any


class AgentProperties(BaseModel):
    provider: str = "openai"
    credential: str | None = None
    openaiCredential: str | None = None
    anthropicCredential: str | None = None
    googleCredential: str | None = None
    groqCredential: str | None = None
    model: str | None = None
    openaiModel: str | None = None
    anthropicModel: str | None = None
    googleModel: str | None = None
    groqModel: str | None = None
    messages: list[AgentMessage] | str | None = Field(default_factory=list)
    tools: list[dict[str, Any]] | list[str] | str | None = Field(default_factory=list)
    toolChoice: str = "auto"
    memoryType: MemoryType = "none"
    memoryKey: str | None = None
    memoryLimit: int = 10
    memoryBackend: str = "workflow"  # workflow | redis | pinecone | qdrant | mem0
    memoryTTL: int = 86400
    # Vector backend config
    pineconeApiKey: str | None = None
    pineconeIndex: str | None = None
    qdrantUrl: str | None = None
    qdrantCollection: str | None = None
    mem0ApiKey: str | None = None
    temperature: float | None = 0.3
    maxTokens: int | None = 4096
    responseFormat: dict[str, Any] | str | None = None
    timeout: int = 60000
    maxIterations: int = 10
    streaming: bool = False
    mcpServers: list[dict[str, Any]] | str | None = Field(default_factory=list)
    # Skills selection — accepts either bare UUID strings (legacy shape) or
    # `{skillId, name, description, updated_at}` snapshot dicts. The snapshot
    # fields are UI-only metadata used by the inspector to detect drift; the
    # runtime always re-fetches name/description/content from the source-of-
    # truth Skill row keyed by `skillId`.
    skills: list[str | dict[str, Any]] | str | None = Field(default_factory=list)
    reasoningEffort: str = "auto"  # auto | low | medium | high


class AgentNode(BaseNode[AgentProperties]):
    @classmethod
    def get_properties_model(cls) -> type[AgentProperties]:
        return AgentProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
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
                    "required": True,
                    "placeholder": "Type or select an AI provider",
                    "loadOptions": "/ai/providers",
                    "typeOptions": {"searchable": True, "allowCustom": True},
                },
                *cls._provider_credential_properties(),
                {
                    "name": "credential",
                    "label": "Provider Credential",
                    "type": "credential",
                    "required": True,
                    "dependsOn": ["provider"],
                    "credentialTypeByField": {
                        "field": "provider",
                        "values": cls._credential_type_by_provider(),
                    },
                },
                {
                    "name": "model",
                    "label": "Model",
                    "type": "options",
                    "required": True,
                    "placeholder": "Type or select a model ID",
                    "loadOptions": "/ai/models",
                    "loadOptionsDependsOn": [
                        "provider",
                        "credential",
                        "openaiCredential",
                        "anthropicCredential",
                        "googleCredential",
                        "groqCredential",
                    ],
                    "typeOptions": {"searchable": True, "allowCustom": True},
                },
                {
                    "name": "messages",
                    "label": "Messages",
                    "type": "messages",
                    "required": True,
                    "default": [
                        {"role": "user", "content": "{{trigger.output}}"},
                    ],
                    "description": "Prompt messages with role and content.",
                },
                {
                    "name": "tools",
                    "label": "Tools",
                    "type": "tool-selector",
                    "default": [],
                    "description": "Tools the agent can use. Select from built-in nodes or integration tools.",
                },
                {
                    "name": "toolChoice",
                    "label": "Tool Choice",
                    "type": "options",
                    "default": "auto",
                    "mode": "advanced",
                    "options": [
                        {"label": "Auto", "value": "auto"},
                        {"label": "Required", "value": "required"},
                        {"label": "None", "value": "none"},
                    ],
                },
                {
                    "name": "maxIterations",
                    "label": "Max Iterations",
                    "type": "number",
                    "default": 10,
                    "mode": "advanced",
                    "description": "Maximum number of agentic loop iterations.",
                },
                {
                    "name": "memoryType",
                    "label": "Memory",
                    "type": "options",
                    "default": "none",
                    "mode": "advanced",
                    "options": [
                        {"label": "None", "value": "none"},
                        {"label": "Workflow (in-execution only)", "value": "workflow"},
                        {"label": "Redis (persists across runs)", "value": "redis"},
                    ],
                },
                {
                    "name": "memoryKey",
                    "label": "Memory Key",
                    "type": "string",
                    "placeholder": "user-{{trigger.user_id}}",
                    "mode": "advanced",
                    "condition": {"field": "memoryType", "value": ["workflow", "redis"]},
                    "description": "Unique key scoping this memory. Use interpolation to make it per-user.",
                },
                {
                    "name": "memoryLimit",
                    "label": "Message History Limit",
                    "type": "number",
                    "default": 10,
                    "mode": "advanced",
                    "condition": {"field": "memoryType", "value": ["workflow", "redis"]},
                },
                {
                    "name": "memoryTTL",
                    "label": "Memory TTL (seconds)",
                    "type": "number",
                    "default": 86400,
                    "mode": "advanced",
                    "condition": {"field": "memoryType", "value": "redis"},
                    "description": "How long to keep memory in Redis. Default 86400 = 24 hours.",
                },
                {
                    "name": "temperature",
                    "label": "Temperature",
                    "type": "number",
                    "default": 0.3,
                    "mode": "advanced",
                },
                {
                    "name": "maxTokens",
                    "label": "Max Output Tokens",
                    "type": "number",
                    "default": 4096,
                    "mode": "advanced",
                },
                {
                    "name": "responseFormat",
                    "label": "Response Format",
                    "type": "json",
                    "required": False,
                    "mode": "advanced",
                    "description": "Optional JSON Schema or provider response-format object.",
                },
                {
                    "name": "timeout",
                    "label": "Timeout (ms)",
                    "type": "number",
                    "default": 60000,
                    "mode": "advanced",
                },
                {
                    "name": "reasoningEffort",
                    "label": "Reasoning Effort",
                    "type": "options",
                    "default": "auto",
                    "mode": "advanced",
                    "options": [
                        {"label": "Auto", "value": "auto"},
                        {"label": "Low", "value": "low"},
                        {"label": "Medium", "value": "medium"},
                        {"label": "High", "value": "high"},
                    ],
                    "description": "For o1/o3 (OpenAI) and extended thinking (Anthropic).",
                },
                {
                    "name": "streaming",
                    "label": "Stream Response",
                    "type": "boolean",
                    "default": False,
                    "mode": "advanced",
                    "description": "Stream LLM tokens in real-time via WebSocket.",
                },
                {
                    "name": "skills",
                    "label": "Skills",
                    "type": "skill-selector",
                    "required": False,
                    "default": [],
                    "description": "Markdown skill files the agent can load on demand.",
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
        credential_properties = [
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
        catalog_by_provider = {provider.ai_provider_id: provider for provider in get_ai_providers()}
        for prop in credential_properties:
            provider_id = prop["condition"]["value"]
            catalog_provider = catalog_by_provider.get(provider_id)
            if catalog_provider:
                prop["label"] = f"{catalog_provider.name} API Key"
                prop["credentialType"] = catalog_provider.id
            prop["visibility"] = "hidden"
        return credential_properties

    @classmethod
    def _credential_type_by_provider(cls) -> dict[str, str]:
        return {
            provider.ai_provider_id: provider.id
            for provider in get_ai_providers()
            if provider.ai_provider_id
        }

    # ------------------------------------------------------------------
    # execute — full agentic loop
    # ------------------------------------------------------------------

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        try:
            # Ensure tool modules are registered
            import apps.api.app.node_system.tools.loader  # noqa: F401
            from apps.api.app.node_system.tools.registry import tool_registry

            api_key = self._get_api_key(context)
            if not api_key:
                provider_name = self._provider_name()
                return NodeResult(
                    success=False, error=f"{provider_name} API key credential is required."
                )

            messages = self._normalize_messages(input_data)
            messages = await self._apply_memory_async(messages, context)
            if not messages:
                return NodeResult(success=False, error="At least one agent message is required.")
            messages = self._ensure_agent_system_prompt(messages)

            # Resolve skills — fetch metadata + pre-load content map
            skill_map: dict[str, str] = {}
            skill_meta: list[dict[str, str]] = []
            if context.db:
                skill_meta, skill_map = await self._resolve_skills(context)

            # Inject skills into system prompt
            if skill_meta:
                messages = self._inject_skills_system_prompt(messages, skill_meta)

            # Resolve tools — includes MCP tools fetched asynchronously
            (
                tool_specs,
                tool_user_params,
                forced_tool_ids,
                mcp_clients,
                tool_user_overrides,
                name_to_tool_id,
            ) = await self._resolve_tools_async()

            # Inject load_skill tool if skills are available
            if skill_meta:
                tool_specs = [*tool_specs, self._build_load_skill_tool(skill_meta)]

            model = self._selected_model()
            timeout_seconds = self.props.timeout / 1000.0
            client = context.http_client or httpx.AsyncClient(timeout=timeout_seconds)

            ai_provider = get_ai_provider(self.props.provider)
            if not ai_provider:
                return NodeResult(
                    success=False, error=f"Unsupported AI provider: {self.props.provider}"
                )

            all_tool_calls: list[dict[str, Any]] = []
            final_content: str = ""
            final_raw: dict[str, Any] = {}
            final_tokens: dict[str, Any] = {}

            # Track forced-tool state across iterations
            remaining_forced = list(forced_tool_ids)
            used_forced: set[str] = set()
            seen_tool_calls: set[tuple[str, str]] = set()
            max_iterations_reached = False
            consecutive_blocked = 0

            try:
                for _iteration in range(max(self.props.maxIterations, 1)):
                    # Determine tool_choice for this iteration
                    if remaining_forced:
                        next_forced = next(
                            (t for t in remaining_forced if t not in used_forced), None
                        )
                        if next_forced:
                            tool_choice_override: Any = {
                                "type": "function",
                                "function": {"name": next_forced},
                            }
                        else:
                            tool_choice_override = "auto"
                    else:
                        tool_choice_override = None  # use global setting

                    # Call LLM — streaming or full response
                    emitter = context.emitter
                    if self.props.streaming and emitter:
                        if ai_provider.ai_api_type == "openai_compatible":
                            content, tool_calls, tokens = await self._stream_llm_openai_compatible(
                                client=client,
                                url=ai_provider.chat_completions_url or "",
                                api_key=api_key,
                                model=model,
                                messages=messages,
                                tool_specs=tool_specs,
                                tool_choice_override=tool_choice_override,
                                emitter=emitter,
                                node_id=context.node_id,
                                iteration=_iteration,
                            )
                            raw_data = {}
                        elif ai_provider.ai_api_type == "anthropic":
                            content, tool_calls, tokens = await self._stream_llm_anthropic(
                                client=client,
                                url=ai_provider.chat_completions_url or "",
                                api_key=api_key,
                                model=model,
                                messages=messages,
                                tool_specs=tool_specs,
                                tool_choice_override=tool_choice_override,
                                emitter=emitter,
                                node_id=context.node_id,
                                iteration=_iteration,
                            )
                            raw_data = {}
                        elif ai_provider.ai_api_type == "google":
                            content, tool_calls, tokens = await self._stream_llm_google(
                                client=client,
                                url_template=ai_provider.chat_completions_url or "",
                                api_key=api_key,
                                model=model,
                                messages=messages,
                                tool_specs=tool_specs,
                                tool_choice_override=tool_choice_override,
                                emitter=emitter,
                                node_id=context.node_id,
                                iteration=_iteration,
                            )
                            raw_data = {}
                        else:
                            return NodeResult(
                                success=False,
                                error=f"Unsupported AI provider: {self.props.provider}",
                            )
                    elif ai_provider.ai_api_type == "openai_compatible":
                        raw_data = await self._call_llm_openai_compatible(
                            client=client,
                            url=ai_provider.chat_completions_url or "",
                            api_key=api_key,
                            model=model,
                            messages=messages,
                            tool_specs=tool_specs,
                            tool_choice_override=tool_choice_override,
                        )
                        content, tool_calls = self._extract_openai_content_and_tools(raw_data)
                        tokens = raw_data.get("usage") or {}
                    elif ai_provider.ai_api_type == "anthropic":
                        raw_data = await self._call_llm_anthropic(
                            client=client,
                            url=ai_provider.chat_completions_url or "",
                            api_key=api_key,
                            model=model,
                            messages=messages,
                            tool_specs=tool_specs,
                            tool_choice_override=tool_choice_override,
                        )
                        content, tool_calls = self._extract_anthropic_content_and_tools(raw_data)
                        usage = raw_data.get("usage") or {}
                        tokens = {
                            "prompt_tokens": usage.get("input_tokens"),
                            "completion_tokens": usage.get("output_tokens"),
                            "total_tokens": (usage.get("input_tokens") or 0)
                            + (usage.get("output_tokens") or 0),
                        }
                    elif ai_provider.ai_api_type == "google":
                        raw_data = await self._call_llm_google(
                            client=client,
                            url_template=ai_provider.chat_completions_url or "",
                            api_key=api_key,
                            model=model,
                            messages=messages,
                            tool_specs=tool_specs,
                            tool_choice_override=tool_choice_override,
                        )
                        content, tool_calls = self._extract_google_content_and_tools(raw_data)
                        usage = raw_data.get("usageMetadata") or {}
                        tokens = {
                            "prompt_tokens": usage.get("promptTokenCount"),
                            "completion_tokens": usage.get("candidatesTokenCount"),
                            "total_tokens": usage.get("totalTokenCount"),
                        }
                    else:
                        return NodeResult(
                            success=False, error=f"Unsupported AI provider: {self.props.provider}"
                        )

                    final_content = content
                    final_raw = raw_data
                    final_tokens = tokens

                    if not tool_calls:
                        break

                    # Track which forced tools were used this iteration.
                    # LLM-facing names get translated back to the saved
                    # tool_id so `workflow:<uuid>` forced entries match.
                    for tc in tool_calls:
                        tc_name = name_to_tool_id.get(tc["name"], tc["name"])
                        if tc_name in forced_tool_ids:
                            used_forced.add(tc_name)
                            if tc_name in remaining_forced:
                                remaining_forced.remove(tc_name)

                    # Append assistant message with tool calls (provider-specific)
                    messages.append(
                        self._build_assistant_message(content, tool_calls, ai_provider.ai_api_type)
                    )

                    # Execute each tool call and append results
                    from apps.api.app.node_system.tools.base import ToolResult as _TR

                    blocked_this_iteration = 0
                    for tc in tool_calls:
                        tool_id = name_to_tool_id.get(tc["name"], tc["name"])
                        llm_args = tc.get("arguments") or {}
                        user_params = tool_user_params.get(tool_id, {})

                        # Merge: LLM fills blanks, but user-configured values are locked (can't be overridden)
                        merged_params = {**llm_args, **user_params}

                        # Real-time event so the run log can render the call
                        # before it finishes — matters for long tool runs.
                        if emitter:
                            await emitter.emit(
                                "tool_call_started",
                                {
                                    "node_id": context.node_id,
                                    "iteration": _iteration,
                                    "tool_id": tool_id,
                                    "arguments": llm_args,
                                },
                            )

                        call_start = time.time()
                        # Duplicate call detection — block same (tool, args) from re-executing
                        call_sig = (tool_id, json.dumps(llm_args, sort_keys=True, default=str))
                        if call_sig in seen_tool_calls:
                            blocked_this_iteration += 1
                            result = _TR(
                                success=False,
                                error=(
                                    f"Duplicate call blocked: '{tool_id}' was already called with "
                                    "these exact arguments and the result was provided. "
                                    "Do not repeat this call — proceed with your remaining tasks."
                                ),
                            )
                        # Handle load_skill — return full skill markdown content to LLM
                        elif tool_id == "load_skill":
                            seen_tool_calls.add(call_sig)
                            skill_name = llm_args.get("skill_name", "")
                            skill_content = skill_map.get(skill_name)
                            if skill_content:
                                result = _TR(success=True, output={"content": skill_content})
                            else:
                                result = _TR(success=False, error=f"Skill '{skill_name}' not found")
                        # Route MCP tools to the appropriate MCP client
                        elif tool_id.startswith("mcp:") and mcp_clients:
                            seen_tool_calls.add(call_sig)
                            parts = tool_id.split(":", 2)
                            server_name = parts[1] if len(parts) > 1 else ""
                            mcp_tool_name = parts[2] if len(parts) > 2 else ""
                            mcp_client = mcp_clients.get(server_name)
                            if mcp_client:
                                result = await mcp_client.call_tool(mcp_tool_name, llm_args)
                            else:
                                result = _TR(
                                    success=False, error=f"MCP server '{server_name}' not found"
                                )
                        else:
                            seen_tool_calls.add(call_sig)
                            overrides = tool_user_overrides.get(tool_id, {})
                            result = await tool_registry.execute(
                                tool_id,
                                merged_params,
                                context,
                                credential_id=overrides.get("credential_id"),
                                retry_override=_retry_from_dict(overrides.get("retry")),
                            )

                        duration_ms = int((time.time() - call_start) * 1000)
                        tool_call_entry: dict[str, Any] = {
                            "name": tool_id,
                            "arguments": llm_args,
                            "result": result.output if result.success else {"error": result.error},
                            "success": result.success,
                            "duration_ms": duration_ms,
                        }
                        if "id" in tc:
                            tool_call_entry["id"] = tc["id"]
                        all_tool_calls.append(tool_call_entry)

                        # Real-time completion event mirrors the started one
                        # so the UI can swap "running" for the final status
                        # without waiting for the agent loop to finish.
                        if emitter:
                            await emitter.emit(
                                "tool_call_completed",
                                {
                                    "node_id": context.node_id,
                                    "iteration": _iteration,
                                    "tool_id": tool_id,
                                    "success": result.success,
                                    "duration_ms": duration_ms,
                                    "result": tool_call_entry["result"],
                                },
                            )

                        messages.append(
                            self._build_tool_result_message(tc, result, ai_provider.ai_api_type)
                        )

                    # All calls blocked: model is looping on already-fetched data.
                    # Inject one redirect hint — don't break, let the model try remaining tasks.
                    # (Sim doesn't deduplicate at all; we keep dedup but allow one recovery turn.)
                    if blocked_this_iteration == len(tool_calls):
                        consecutive_blocked += 1
                        if consecutive_blocked >= 2:
                            break
                        messages.append(
                            {
                                "role": "user",
                                "content": (
                                    "All your tool calls were duplicates — those results are already above. "
                                    "Do not repeat them. Use the data you already have and complete "
                                    "your remaining tasks now."
                                ),
                            }
                        )
                    else:
                        consecutive_blocked = 0
                else:
                    max_iterations_reached = True

                # Final summarization — if loop produced tool calls but no text response,
                # make one more LLM call (no tools) so the agent always returns content.
                # Must run inside try so the HTTP client is still open.
                if not final_content and all_tool_calls:
                    # Explicitly recap successful tool results so weak models don't ask for input
                    successful_results = [
                        tc
                        for tc in all_tool_calls
                        if tc["success"] and not str(tc.get("result", "")).startswith("Duplicate")
                    ]
                    recap_lines = ["Here are the tool results from this run:"]
                    for tc in successful_results:
                        recap_lines.append(
                            f"- {tc['name']}({json.dumps(tc['arguments'])})"
                            f" → {json.dumps(tc['result'])}"
                        )
                    failed_results = [tc for tc in all_tool_calls if not tc["success"]]
                    for tc in failed_results:
                        error = (tc.get("result") or {}).get("error", "")
                        if "Duplicate call blocked" not in error:
                            recap_lines.append(f"- {tc['name']} failed: {error}")
                    if max_iterations_reached:
                        recap_lines.append("(Maximum iterations reached.)")
                    recap_lines.append(
                        "Complete any remaining tasks now using your available tools. "
                        "Do not ask for more input — use what was returned above."
                    )
                    messages.append({"role": "user", "content": "\n".join(recap_lines)})
                    try:
                        # Pass tools so model can still call them (e.g. send Slack after HTTP fetch).
                        # Without tools, Gemini falls back to Python pseudo-code output.
                        if ai_provider.ai_api_type == "openai_compatible":
                            summary_raw = await self._call_llm_openai_compatible(
                                client=client,
                                url=ai_provider.chat_completions_url or "",
                                api_key=api_key,
                                model=model,
                                messages=messages,
                                tool_specs=tool_specs,
                            )
                            final_content, summary_tool_calls = (
                                self._extract_openai_content_and_tools(summary_raw)
                            )
                        elif ai_provider.ai_api_type == "anthropic":
                            summary_raw = await self._call_llm_anthropic(
                                client=client,
                                url=ai_provider.chat_completions_url or "",
                                api_key=api_key,
                                model=model,
                                messages=messages,
                                tool_specs=tool_specs,
                            )
                            final_content, summary_tool_calls = (
                                self._extract_anthropic_content_and_tools(summary_raw)
                            )
                        elif ai_provider.ai_api_type == "google":
                            summary_raw = await self._call_llm_google(
                                client=client,
                                url_template=ai_provider.chat_completions_url or "",
                                api_key=api_key,
                                model=model,
                                messages=messages,
                                tool_specs=tool_specs,
                            )
                            final_content, summary_tool_calls = (
                                self._extract_google_content_and_tools(summary_raw)
                            )

                        # If the summarization response itself has tool calls, execute them.
                        # This is the common case: model wants to call Slack after seeing HTTP data.
                        if summary_tool_calls:
                            messages.append(
                                self._build_assistant_message(
                                    final_content, summary_tool_calls, ai_provider.ai_api_type
                                )
                            )
                            for tc in summary_tool_calls:
                                tool_id = name_to_tool_id.get(tc["name"], tc["name"])
                                llm_args = tc.get("arguments") or {}
                                user_params = tool_user_params.get(tool_id, {})
                                merged = {**llm_args, **user_params}
                                overrides = tool_user_overrides.get(tool_id, {})
                                if emitter:
                                    await emitter.emit(
                                        "tool_call_started",
                                        {
                                            "node_id": context.node_id,
                                            "iteration": _iteration,
                                            "tool_id": tool_id,
                                            "arguments": llm_args,
                                            "phase": "summary",
                                        },
                                    )
                                call_start = time.time()
                                result = await tool_registry.execute(
                                    tool_id,
                                    merged,
                                    context,
                                    credential_id=overrides.get("credential_id"),
                                    retry_override=_retry_from_dict(overrides.get("retry")),
                                )
                                duration_ms = int((time.time() - call_start) * 1000)
                                summary_entry: dict[str, Any] = {
                                    "name": tool_id,
                                    "arguments": llm_args,
                                    "result": result.output
                                    if result.success
                                    else {"error": result.error},
                                    "success": result.success,
                                    "duration_ms": duration_ms,
                                }
                                all_tool_calls.append(summary_entry)
                                if emitter:
                                    await emitter.emit(
                                        "tool_call_completed",
                                        {
                                            "node_id": context.node_id,
                                            "iteration": _iteration,
                                            "tool_id": tool_id,
                                            "success": result.success,
                                            "duration_ms": duration_ms,
                                            "result": summary_entry["result"],
                                            "phase": "summary",
                                        },
                                    )
                            # If only tool calls and no text, set a brief summary
                            if not final_content:
                                final_content = f"Completed: {', '.join(tc['name'] for tc in summary_tool_calls)}"
                    except Exception as _e:
                        logger.warning(f"Final summarization call failed: {_e}")

                    # Hard fallback — API returned success but empty text
                    if not final_content:
                        successful = [tc for tc in all_tool_calls if tc["success"]]
                        failed = [
                            tc
                            for tc in all_tool_calls
                            if not tc["success"]
                            and "Duplicate call blocked" not in str(tc.get("result", ""))
                        ]
                        parts = [f"Agent completed {len(all_tool_calls)} tool call(s)."]
                        if successful:
                            parts.append(f"{len(successful)} succeeded.")
                        if failed:
                            parts.append(
                                f"{len(failed)} failed: " + "; ".join(tc["name"] for tc in failed)
                            )
                        final_content = " ".join(parts)

            finally:
                if not context.http_client:
                    await client.aclose()

            output = self._build_output(
                final_content, model, final_tokens, all_tool_calls, final_raw
            )
            output["provider"] = self.props.provider
            output["memory"] = await self._persist_memory_async(messages, final_content, context)
            return NodeResult(success=True, output_data=output)

        except httpx.HTTPStatusError as e:
            return NodeResult(success=False, error=self._extract_provider_error(e.response))
        except httpx.TimeoutException:
            return NodeResult(
                success=False, error=f"Agent request timed out after {self.props.timeout}ms"
            )
        except Exception as e:
            logger.error(f"AgentNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))

    # ------------------------------------------------------------------
    # _resolve_tools — new format + legacy fallback
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Skill helpers
    # ------------------------------------------------------------------

    async def _resolve_skills(self, context: Any) -> tuple[list[dict[str, str]], dict[str, str]]:
        """Fetch skill metadata + content for selected skill IDs.

        Returns:
        - skill_meta: [{name, description}, ...] — for system prompt injection
        - skill_map: {name: content} — for load_skill tool execution
        """
        import uuid as _uuid

        from apps.api.app.features.skills.repository import SkillRepository

        raw_skills = self.props.skills
        if not raw_skills:
            return [], {}

        if isinstance(raw_skills, str):
            try:
                raw_skills = json.loads(raw_skills)
            except json.JSONDecodeError:
                return [], {}

        if not isinstance(raw_skills, list):
            return [], {}

        # Accept both plain UUID strings and {skillId: "..."} dicts
        skill_ids: list[_uuid.UUID] = []
        for item in raw_skills:
            try:
                if isinstance(item, str):
                    skill_ids.append(_uuid.UUID(item))
                elif isinstance(item, dict) and item.get("skillId"):
                    skill_ids.append(_uuid.UUID(item["skillId"]))
            except (ValueError, AttributeError):
                continue

        if not skill_ids:
            return [], {}

        repo = SkillRepository(context.db)

        # Fetch user_id from credentials context — skills are owned by the workflow user
        # We use workflow_id to look up the user via WorkflowRepository
        from apps.api.app.features.workflows.repository import WorkflowRepository

        wf_repo = WorkflowRepository(context.db)
        workflow = await wf_repo.get_by_id(_uuid.UUID(context.workflow_id))
        if not workflow:
            return [], {}

        skills = await repo.get_by_ids_and_user(skill_ids, workflow.user_id)

        skill_meta = [{"name": s.name, "description": s.description} for s in skills]
        skill_map = {s.name: s.content for s in skills}
        return skill_meta, skill_map

    def _inject_skills_system_prompt(
        self, messages: list[dict[str, Any]], skill_meta: list[dict[str, str]]
    ) -> list[dict[str, Any]]:
        from xml.sax.saxutils import escape as _xml_escape
        from xml.sax.saxutils import quoteattr as _xml_quoteattr

        skills_xml_parts = [
            "You have access to the following skills. Use the load_skill tool to activate a skill when relevant.\n\n<available_skills>"
        ]
        for s in skill_meta:
            # `quoteattr` returns the value already wrapped in quotes and
            # escapes any embedded quotes/ampersands/angle brackets — so a
            # free-form name like `Bob "the" builder` round-trips cleanly.
            name_attr = _xml_quoteattr(s["name"])
            desc = _xml_escape(s["description"])
            skills_xml_parts.append(
                f"  <skill name={name_attr}>\n    <description>{desc}</description>\n  </skill>"
            )
        skills_xml_parts.append("</available_skills>")
        skills_section = "\n".join(skills_xml_parts)

        messages = list(messages)
        for i, msg in enumerate(messages):
            if msg.get("role") == "system":
                messages[i] = {**msg, "content": msg["content"] + "\n\n" + skills_section}
                return messages

        # No system message — prepend one
        return [{"role": "system", "content": skills_section}, *messages]

    def _ensure_agent_system_prompt(self, messages: list[dict[str, Any]]) -> list[dict[str, Any]]:
        """Prepend a default system prompt if the user provided none.

        Guides the LLM on failure handling and dedup — critical for weaker models.
        """
        if any(m.get("role") == "system" for m in messages):
            return messages
        system_content = (
            "You are a helpful AI agent with access to tools.\n\n"
            "Guidelines:\n"
            "- Use tools to gather information and complete tasks step by step.\n"
            "- If a tool returns an error or a non-success status (e.g. HTTP 4xx/5xx), "
            "acknowledge the result and continue with remaining tasks — do not retry the same call.\n"
            "- Never call the same tool with the same arguments more than once.\n"
            "- After gathering information, produce a clear, concise final response.\n"
            "- If a task cannot be completed, explain what you attempted and what failed."
        )
        return [{"role": "system", "content": system_content}, *messages]

    def _build_load_skill_tool(self, skill_meta: list[dict[str, str]]) -> dict[str, Any]:
        skill_names = [s["name"] for s in skill_meta]
        return {
            "type": "function",
            "function": {
                "name": "load_skill",
                "description": f"Load a skill to get specialized instructions. Available skills: {', '.join(skill_names)}",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "skill_name": {
                            "type": "string",
                            "description": "Name of the skill to load.",
                            "enum": skill_names,
                        }
                    },
                    "required": ["skill_name"],
                },
            },
        }

    def _parse_mcp_servers(self) -> list[dict[str, Any]]:
        """Collect MCP server configs from two sources (in priority order):
        1. kind='mcp' entries in the unified `tools` array (new UI format)
        2. The standalone `mcpServers` JSON prop (legacy / raw JSON editing)
        """
        servers: list[dict[str, Any]] = []
        seen_names: set[str] = set()

        # 1. Read from unified tools array
        raw_tools = self.props.tools
        if isinstance(raw_tools, str):
            try:
                raw_tools = json.loads(raw_tools)
            except json.JSONDecodeError:
                raw_tools = []
        if isinstance(raw_tools, list):
            for item in raw_tools:
                if not isinstance(item, dict):
                    continue
                if item.get("kind") == "mcp":
                    name = item.get("mcpName") or item.get("title", "")
                    url = item.get("mcpUrl", "")
                    if name and url and name not in seen_names:
                        servers.append(
                            {"name": str(name), "url": str(url), "apiKey": item.get("mcpApiKey")}
                        )
                        seen_names.add(name)

        # 2. Fallback: legacy mcpServers prop
        raw = self.props.mcpServers
        if raw:
            if isinstance(raw, str):
                try:
                    raw = json.loads(raw)
                except json.JSONDecodeError:
                    raw = []
            if isinstance(raw, list):
                for item in raw:
                    if not isinstance(item, dict):
                        continue
                    name = item.get("name")
                    url = item.get("url")
                    if name and url and name not in seen_names:
                        servers.append(
                            {"name": str(name), "url": str(url), "apiKey": item.get("apiKey")}
                        )
                        seen_names.add(name)

        return servers

    @staticmethod
    def _workflow_tool_safe_name(tool_id: str) -> str:
        """Map a ``workflow:<uuid>`` saved id to an LLM-safe function name.

        OpenAI's function-name grammar is ``[a-zA-Z0-9_-]{1,64}`` — colons
        are rejected. UUID hyphens stay because hyphens are allowed.
        """
        return tool_id.replace(":", "_")

    @classmethod
    def _build_workflow_tool_schema(cls, tool_id: str, entry: dict[str, Any]) -> dict[str, Any]:
        """Build the OpenAI function schema for a `workflow:<uuid>` entry.

        Reads the frontend's snapshot of the referenced workflow's
        ``input_schema`` from ``entry["paramsSchema"]`` so the agent doesn't
        need to round-trip the DB while the LLM is calling. Missing snapshot
        degrades to an empty-object schema; the workflow still runs with
        whatever the user pinned in the inspector via ``tool_user_params``.
        """
        params_schema = entry.get("paramsSchema")
        properties: dict[str, Any] = {}
        required: list[str] = []
        if isinstance(params_schema, dict):
            for name, meta in params_schema.items():
                if not isinstance(name, str) or not name:
                    continue
                if not isinstance(meta, dict):
                    continue
                p_type = str(meta.get("type") or "string")
                properties[name] = {
                    "type": p_type if p_type != "json" else "object",
                    "description": str(meta.get("description") or ""),
                }
                if meta.get("required"):
                    required.append(name)
        display_name = str(entry.get("name") or tool_id)
        description = str(entry.get("description") or f"Run the workflow {display_name!r}.")
        return {
            "type": "function",
            "function": {
                "name": cls._workflow_tool_safe_name(tool_id),
                "description": description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    "required": required,
                },
            },
        }

    def _resolve_tools(
        self,
    ) -> tuple[
        list[dict[str, Any]],
        dict[str, dict[str, Any]],
        list[str],
        dict[str, dict[str, Any]],
        dict[str, str],
    ]:
        """Parse tools props and return:
        - tool_specs: list of OpenAI function-call schema objects for the LLM
          (tools with usageControl='none' are excluded)
        - tool_user_params: mapping of tool_id → user-provided params dict
        - forced_tool_ids: tool IDs where usageControl='force'
        - tool_user_overrides: mapping of tool_id → {credential_id?, retry?}
          for per-tool credential and retry-config overrides set in the
          inspector. Passed into ``tool_registry.execute`` at call time.
        - name_to_tool_id: LLM-facing function name → saved tool_id. Identity
          for everything except ``workflow:`` entries, whose colons are
          stripped to satisfy OpenAI's function-name grammar. Tool-call
          dispatch translates ``tc["name"]`` through this map before any
          state lookup.

        Handles three formats:
        1. New format: [{"toolId": "slack_send_message", "params": {...}, "usageControl": "auto"}, ...]
        2. Old schema format: [{"type": "node"|"custom", "schema": {...}, ...}]
        3. Legacy format: [{"name": "...", ...}] or [{"type": "function", "function": {...}}]
        """
        from apps.api.app.node_system.tools.registry import tool_registry

        raw_tools = self.props.tools
        if raw_tools in (None, ""):
            return [], {}, [], {}, {}

        if isinstance(raw_tools, str):
            try:
                raw_tools = json.loads(raw_tools)
            except json.JSONDecodeError as e:
                raise ValueError(f"Tools must be valid JSON: {e.msg}") from e

        if not isinstance(raw_tools, list) or not raw_tools:
            return [], {}, [], {}, {}

        first = raw_tools[0]
        if not isinstance(first, dict):
            return [], {}, [], {}, {}

        # ----- New format: items have a "toolId" key OR kind='mcp' (skip mcp here) -----
        if "toolId" in first or first.get("kind") in ("tool", "mcp"):
            tool_specs: list[dict[str, Any]] = []
            tool_user_params: dict[str, dict[str, Any]] = {}
            tool_user_overrides: dict[str, dict[str, Any]] = {}
            forced_tool_ids: list[str] = []
            name_to_tool_id: dict[str, str] = {}

            for item in raw_tools:
                if not isinstance(item, dict):
                    continue
                # MCP entries are handled by _parse_mcp_servers, not here
                if item.get("kind") == "mcp":
                    continue
                tool_id = item.get("toolId")
                if not isinstance(tool_id, str) or not tool_id:
                    continue

                # Resolve versioned tool IDs (skip for `workflow:` prefix —
                # registry doesn't own them).
                if not tool_id.startswith("workflow:"):
                    tool_id = tool_registry.resolve_tool_id(tool_id)

                usage_control = item.get("usageControl") or "auto"

                # Skip tools the user explicitly disabled
                if usage_control == "none":
                    continue

                if tool_id.startswith("workflow:"):
                    schema = self._build_workflow_tool_schema(tool_id, item)
                    name_to_tool_id[self._workflow_tool_safe_name(tool_id)] = tool_id
                else:
                    schema = tool_registry.to_openai_schema(tool_id)
                if schema is None:
                    logger.warning(f"Tool '{tool_id}' not found in registry, skipping")
                    continue
                tool_specs.append(schema)
                params = item.get("params")
                tool_user_params[tool_id] = params if isinstance(params, dict) else {}

                # Per-tool overrides from the inspector: credential pinning
                # and retry-config override. Stored alongside `params` so the
                # caller can hand them straight to `tool_registry.execute`.
                overrides: dict[str, Any] = {}
                credential_id = item.get("credentialId")
                if isinstance(credential_id, str) and credential_id:
                    overrides["credential_id"] = credential_id
                retry_cfg = item.get("retry")
                if isinstance(retry_cfg, dict) and retry_cfg.get("enabled"):
                    overrides["retry"] = retry_cfg
                if overrides:
                    tool_user_overrides[tool_id] = overrides

                if usage_control == "force":
                    forced_tool_ids.append(tool_id)

            return (
                tool_specs,
                tool_user_params,
                forced_tool_ids,
                tool_user_overrides,
                name_to_tool_id,
            )

        # ----- Old schema format: items have a "schema" key -----
        if "schema" in first:
            tool_specs = []
            for item in raw_tools:
                if not isinstance(item, dict):
                    continue
                schema = item.get("schema")
                if isinstance(schema, dict):
                    tool_specs.append({"type": "function", "function": schema})
            return tool_specs, {}, [], {}, {}

        # ----- Legacy format: raw function spec objects -----
        tool_specs = []
        for tool in raw_tools:
            if not isinstance(tool, dict):
                continue
            name = tool.get("name") or (tool.get("function") or {}).get("name")
            if not isinstance(name, str) or not name:
                continue
            tool_specs.append(self._to_openai_tool(tool))
        return tool_specs, {}, [], {}, {}

    async def _resolve_tools_async(
        self,
    ) -> tuple[
        list[dict[str, Any]],
        dict[str, dict[str, Any]],
        list[str],
        dict[str, Any],
        dict[str, dict[str, Any]],
        dict[str, str],
    ]:
        """Extend _resolve_tools() with async MCP tool fetching.

        Returns:
            (tool_specs, tool_user_params, forced_tool_ids, mcp_clients,
             tool_user_overrides, name_to_tool_id)
        """
        from apps.api.app.node_system.tools.mcp.client import MCPClient

        (
            tool_specs,
            tool_user_params,
            forced_tool_ids,
            tool_user_overrides,
            name_to_tool_id,
        ) = self._resolve_tools()
        mcp_clients: dict[str, Any] = {}

        mcp_server_configs = self._parse_mcp_servers()
        for server in mcp_server_configs:
            name = server["name"]
            url = server["url"]
            api_key = server.get("apiKey")
            try:
                mcp_client = MCPClient(name, url, api_key)
                mcp_tools = await mcp_client.list_tools()
                for tool_def in mcp_tools:
                    # Build OpenAI-compatible function schema from ToolDefinition
                    params_schema: dict[str, Any] = {
                        "type": "object",
                        "properties": {},
                        "required": [],
                    }
                    for p_name, p in tool_def.params.items():
                        if p.visibility in ("hidden", "user-only"):
                            continue
                        params_schema["properties"][p_name] = {
                            "type": p.type if p.type != "json" else "object",
                            "description": p.description,
                        }
                        if p.required:
                            params_schema["required"].append(p_name)
                    tool_specs.append(
                        {
                            "type": "function",
                            "function": {
                                "name": tool_def.id,
                                "description": tool_def.description,
                                "parameters": params_schema,
                            },
                        }
                    )
                mcp_clients[name] = mcp_client
            except Exception as e:
                logger.warning(f"Failed to fetch tools from MCP server '{name}' ({url}): {e}")

        return (
            tool_specs,
            tool_user_params,
            forced_tool_ids,
            mcp_clients,
            tool_user_overrides,
            name_to_tool_id,
        )

    # ------------------------------------------------------------------
    # LLM call helpers (return raw response data)
    # ------------------------------------------------------------------

    async def _call_llm_openai_compatible(
        self,
        client: httpx.AsyncClient,
        url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, Any]],
        tool_specs: list[dict[str, Any]],
        tool_choice_override: Any = None,
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

        if tool_specs:
            payload["tools"] = tool_specs
            if tool_choice_override is not None:
                payload["tool_choice"] = tool_choice_override
            elif self.props.toolChoice == "required":
                payload["tool_choice"] = "required"
            elif self.props.toolChoice == "none":
                payload["tool_choice"] = "none"
            else:
                payload["tool_choice"] = "auto"

        # Reasoning effort for o1/o3 models
        if self.props.reasoningEffort and self.props.reasoningEffort != "auto":
            payload["reasoning_effort"] = self.props.reasoningEffort

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

    async def _call_llm_anthropic(
        self,
        client: httpx.AsyncClient,
        url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, Any]],
        tool_specs: list[dict[str, Any]],
        tool_choice_override: Any = None,
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

        if tool_specs:
            payload["tools"] = [self._to_anthropic_tool(spec) for spec in tool_specs]
            if tool_choice_override is not None:
                if (
                    isinstance(tool_choice_override, dict)
                    and tool_choice_override.get("type") == "function"
                ):
                    fn_name = (tool_choice_override.get("function") or {}).get("name", "")
                    payload["tool_choice"] = {"type": "tool", "name": fn_name}
                else:
                    payload["tool_choice"] = {"type": "auto"}
            elif self.props.toolChoice == "required":
                payload["tool_choice"] = {"type": "any"}
            elif self.props.toolChoice == "auto":
                payload["tool_choice"] = {"type": "auto"}

        # Extended thinking for Anthropic
        _THINKING_BUDGETS = {"low": 1024, "medium": 8192, "high": 32768}
        if self.props.reasoningEffort and self.props.reasoningEffort in _THINKING_BUDGETS:
            payload["thinking"] = {
                "type": "enabled",
                "budget_tokens": _THINKING_BUDGETS[self.props.reasoningEffort],
            }
            payload["temperature"] = 1  # required when thinking enabled

        response = await client.post(
            url,
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

    async def _call_llm_google(
        self,
        client: httpx.AsyncClient,
        url_template: str,
        api_key: str,
        model: str,
        messages: list[dict[str, Any]],
        tool_specs: list[dict[str, Any]],
        tool_choice_override: Any = None,
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

        payload: dict[str, Any] = {"contents": contents}
        if generation_config:
            payload["generationConfig"] = generation_config
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if tool_specs:
            payload["tools"] = [
                {"functionDeclarations": [self._to_google_tool(spec) for spec in tool_specs]}
            ]
            # Google tool_config for forced tool call
            if tool_choice_override is not None and isinstance(tool_choice_override, dict):
                fn_name = (tool_choice_override.get("function") or {}).get("name", "")
                if fn_name:
                    payload["toolConfig"] = {
                        "functionCallingConfig": {
                            "mode": "ANY",
                            "allowedFunctionNames": [fn_name],
                        }
                    }

        response = await client.post(
            url_template.format(model=self._google_model_path(model)),
            params={"key": api_key},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=None,
        )
        response.raise_for_status()
        return response.json()

    # ------------------------------------------------------------------
    # Streaming LLM callers — emit agent_chunk events, return (content, tool_calls, tokens)
    # ------------------------------------------------------------------

    async def _stream_llm_openai_compatible(
        self,
        client: httpx.AsyncClient,
        url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, Any]],
        tool_specs: list[dict[str, Any]],
        tool_choice_override: Any,
        emitter: Any,
        node_id: str,
        iteration: int,
    ) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
        payload: dict[str, Any] = {"model": model, "messages": messages, "stream": True}
        if self.props.temperature is not None:
            payload["temperature"] = self.props.temperature
        if self.props.maxTokens is not None:
            payload["max_tokens"] = self.props.maxTokens
        response_format = self._normalize_response_format("openai")
        if response_format is not None:
            payload["response_format"] = response_format
        if tool_specs:
            payload["tools"] = tool_specs
            if tool_choice_override is not None:
                payload["tool_choice"] = tool_choice_override
            elif self.props.toolChoice == "required":
                payload["tool_choice"] = "required"
            elif self.props.toolChoice == "none":
                payload["tool_choice"] = "none"
            else:
                payload["tool_choice"] = "auto"

        accumulated_content = ""
        tool_calls_buffer: dict[int, dict[str, Any]] = {}
        tokens: dict[str, Any] = {}

        async with client.stream(
            "POST",
            url,
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json=payload,
            timeout=None,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                raw = line[6:]
                if raw == "[DONE]":
                    break
                try:
                    chunk = json.loads(raw)
                except json.JSONDecodeError:
                    continue
                if chunk.get("usage"):
                    tokens = chunk["usage"]
                choice = (chunk.get("choices") or [{}])[0]
                delta = choice.get("delta") or {}
                text = delta.get("content") or ""
                if text:
                    accumulated_content += text
                    await emitter.emit(
                        "agent_chunk", {"node_id": node_id, "delta": text, "iteration": iteration}
                    )
                for tc in delta.get("tool_calls") or []:
                    idx = tc.get("index", 0)
                    if idx not in tool_calls_buffer:
                        tool_calls_buffer[idx] = {"id": "", "name": "", "arguments": ""}
                    tool_calls_buffer[idx]["id"] += tc.get("id") or ""
                    fn = tc.get("function") or {}
                    tool_calls_buffer[idx]["name"] += fn.get("name") or ""
                    tool_calls_buffer[idx]["arguments"] += fn.get("arguments") or ""

        tool_calls: list[dict[str, Any]] = []
        for tc in tool_calls_buffer.values():
            try:
                args = json.loads(tc["arguments"]) if tc["arguments"] else {}
            except json.JSONDecodeError:
                args = {}
            tool_calls.append({"id": tc["id"], "name": tc["name"], "arguments": args})
        return accumulated_content, tool_calls, tokens

    async def _stream_llm_anthropic(
        self,
        client: httpx.AsyncClient,
        url: str,
        api_key: str,
        model: str,
        messages: list[dict[str, Any]],
        tool_specs: list[dict[str, Any]],
        tool_choice_override: Any,
        emitter: Any,
        node_id: str,
        iteration: int,
    ) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
        system_prompt, anthropic_messages = self._to_anthropic_messages(messages)
        payload: dict[str, Any] = {
            "model": model,
            "max_tokens": self.props.maxTokens or 4096,
            "messages": anthropic_messages,
            "stream": True,
        }
        if system_prompt:
            payload["system"] = system_prompt
        if self.props.temperature is not None:
            payload["temperature"] = self.props.temperature
        if tool_specs:
            payload["tools"] = [self._to_anthropic_tool(spec) for spec in tool_specs]
            if tool_choice_override is not None:
                if (
                    isinstance(tool_choice_override, dict)
                    and tool_choice_override.get("type") == "function"
                ):
                    fn_name = (tool_choice_override.get("function") or {}).get("name", "")
                    payload["tool_choice"] = {"type": "tool", "name": fn_name}
                else:
                    payload["tool_choice"] = {"type": "auto"}
            elif self.props.toolChoice == "required":
                payload["tool_choice"] = {"type": "any"}
            elif self.props.toolChoice == "auto":
                payload["tool_choice"] = {"type": "auto"}

        accumulated_text = ""
        tool_use_blocks: dict[int, dict[str, Any]] = {}
        tokens: dict[str, Any] = {}

        async with client.stream(
            "POST",
            url,
            headers={
                "x-api-key": api_key,
                "anthropic-version": "2023-06-01",
                "Content-Type": "application/json",
            },
            json=payload,
            timeout=None,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                try:
                    data = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                event_type = data.get("type")
                if event_type == "message_delta":
                    usage = data.get("usage") or {}
                    tokens = {
                        "prompt_tokens": None,
                        "completion_tokens": usage.get("output_tokens"),
                        "total_tokens": usage.get("output_tokens"),
                    }
                elif event_type == "message_start":
                    usage = (data.get("message") or {}).get("usage") or {}
                    tokens["prompt_tokens"] = usage.get("input_tokens")
                    if tokens.get("total_tokens") and tokens.get("prompt_tokens"):
                        tokens["total_tokens"] = (tokens.get("prompt_tokens") or 0) + (
                            tokens.get("completion_tokens") or 0
                        )
                elif event_type == "content_block_start":
                    block = data.get("content_block") or {}
                    if block.get("type") == "tool_use":
                        idx = data.get("index", 0)
                        tool_use_blocks[idx] = {
                            "id": block.get("id", ""),
                            "name": block.get("name", ""),
                            "partial_json": "",
                        }
                elif event_type == "content_block_delta":
                    delta = data.get("delta") or {}
                    idx = data.get("index", 0)
                    if delta.get("type") == "text_delta":
                        text = delta.get("text") or ""
                        accumulated_text += text
                        await emitter.emit(
                            "agent_chunk",
                            {"node_id": node_id, "delta": text, "iteration": iteration},
                        )
                    elif delta.get("type") == "input_json_delta" and idx in tool_use_blocks:
                        tool_use_blocks[idx]["partial_json"] += delta.get("partial_json") or ""

        tool_calls: list[dict[str, Any]] = []
        for block in tool_use_blocks.values():
            try:
                args = json.loads(block["partial_json"]) if block["partial_json"] else {}
            except json.JSONDecodeError:
                args = {}
            tool_calls.append({"id": block["id"], "name": block["name"], "arguments": args})
        return accumulated_text, tool_calls, tokens

    async def _stream_llm_google(
        self,
        client: httpx.AsyncClient,
        url_template: str,
        api_key: str,
        model: str,
        messages: list[dict[str, Any]],
        tool_specs: list[dict[str, Any]],
        tool_choice_override: Any,
        emitter: Any,
        node_id: str,
        iteration: int,
    ) -> tuple[str, list[dict[str, Any]], dict[str, Any]]:
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

        payload: dict[str, Any] = {"contents": contents}
        if generation_config:
            payload["generationConfig"] = generation_config
        if system_prompt:
            payload["systemInstruction"] = {"parts": [{"text": system_prompt}]}
        if tool_specs:
            payload["tools"] = [
                {"functionDeclarations": [self._to_google_tool(spec) for spec in tool_specs]}
            ]
            if tool_choice_override is not None and isinstance(tool_choice_override, dict):
                fn_name = (tool_choice_override.get("function") or {}).get("name", "")
                if fn_name:
                    payload["toolConfig"] = {
                        "functionCallingConfig": {"mode": "ANY", "allowedFunctionNames": [fn_name]}
                    }

        stream_url = url_template.format(model=self._google_model_path(model)).replace(
            ":generateContent", ":streamGenerateContent"
        )

        accumulated_text = ""
        tool_calls: list[dict[str, Any]] = []
        tokens: dict[str, Any] = {}

        async with client.stream(
            "POST",
            stream_url,
            params={"key": api_key, "alt": "sse"},
            headers={"Content-Type": "application/json"},
            json=payload,
            timeout=None,
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if not line.startswith("data: "):
                    continue
                try:
                    chunk = json.loads(line[6:])
                except json.JSONDecodeError:
                    continue
                usage = chunk.get("usageMetadata") or {}
                if usage:
                    tokens = {
                        "prompt_tokens": usage.get("promptTokenCount"),
                        "completion_tokens": usage.get("candidatesTokenCount"),
                        "total_tokens": usage.get("totalTokenCount"),
                    }
                candidates = chunk.get("candidates") or []
                for candidate in candidates:
                    parts = candidate.get("content", {}).get("parts") or []
                    for part in parts:
                        if "text" in part:
                            text = part["text"]
                            accumulated_text += text
                            await emitter.emit(
                                "agent_chunk",
                                {"node_id": node_id, "delta": text, "iteration": iteration},
                            )
                        if "functionCall" in part:
                            call = part["functionCall"]
                            tool_calls.append(
                                {
                                    "id": call.get("name", ""),
                                    "name": call.get("name", ""),
                                    "arguments": call.get("args") or {},
                                }
                            )

        return accumulated_text, tool_calls, tokens

    # ------------------------------------------------------------------
    # Content + tool call extraction (per provider → unified format)
    # ------------------------------------------------------------------

    def _extract_openai_content_and_tools(
        self, data: dict[str, Any]
    ) -> tuple[str, list[dict[str, Any]]]:
        choices = data.get("choices") or []
        first_choice = choices[0] if choices else {}
        message = first_choice.get("message") or {}
        content = message.get("content") or ""
        raw_tool_calls = message.get("tool_calls") or []

        tool_calls: list[dict[str, Any]] = []
        for tc in raw_tool_calls:
            if not isinstance(tc, dict):
                continue
            fn = tc.get("function") or {}
            args = fn.get("arguments", "{}")
            try:
                parsed_args = json.loads(args) if isinstance(args, str) else args
            except json.JSONDecodeError:
                parsed_args = {}
            tool_calls.append(
                {
                    "id": tc.get("id", ""),
                    "name": fn.get("name", ""),
                    "arguments": parsed_args,
                }
            )
        return str(content), tool_calls

    def _extract_anthropic_content_and_tools(
        self, data: dict[str, Any]
    ) -> tuple[str, list[dict[str, Any]]]:
        content_blocks = data.get("content") or []
        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        for block in content_blocks:
            if not isinstance(block, dict):
                continue
            if block.get("type") == "text":
                text_parts.append(block.get("text", ""))
            elif block.get("type") == "tool_use":
                tool_calls.append(
                    {
                        "id": block.get("id", ""),
                        "name": block.get("name", ""),
                        "arguments": block.get("input") or {},
                    }
                )
        return "".join(text_parts), tool_calls

    def _extract_google_content_and_tools(
        self, data: dict[str, Any]
    ) -> tuple[str, list[dict[str, Any]]]:
        candidates = data.get("candidates") or []
        first_candidate = candidates[0] if candidates else {}
        parts = first_candidate.get("content", {}).get("parts", [])
        text_parts: list[str] = []
        tool_calls: list[dict[str, Any]] = []
        for part in parts:
            if not isinstance(part, dict):
                continue
            if "text" in part:
                text_parts.append(part["text"])
            if "functionCall" in part:
                call = part["functionCall"]
                tool_calls.append(
                    {
                        "id": call.get("name", ""),  # Google uses name as ID
                        "name": call.get("name", ""),
                        "arguments": call.get("args") or {},
                    }
                )
        return "".join(text_parts), tool_calls

    # ------------------------------------------------------------------
    # Message builders (per provider)
    # ------------------------------------------------------------------

    def _build_assistant_message(
        self,
        content: str,
        tool_calls: list[dict[str, Any]],
        api_type: str,
    ) -> dict[str, Any]:
        if api_type == "anthropic":
            content_blocks: list[dict[str, Any]] = []
            if content:
                content_blocks.append({"type": "text", "text": content})
            for tc in tool_calls:
                content_blocks.append(
                    {
                        "type": "tool_use",
                        "id": tc["id"],
                        "name": tc["name"],
                        "input": tc.get("arguments") or {},
                    }
                )
            return {"role": "assistant", "content": content_blocks}

        if api_type == "google":
            parts: list[dict[str, Any]] = []
            if content:
                parts.append({"text": content})
            for tc in tool_calls:
                parts.append(
                    {
                        "functionCall": {
                            "name": tc["name"],
                            "args": tc.get("arguments") or {},
                        }
                    }
                )
            return {"role": "model", "parts": parts}

        # OpenAI-compatible
        openai_tool_calls = [
            {
                "id": tc["id"],
                "type": "function",
                "function": {
                    "name": tc["name"],
                    "arguments": json.dumps(tc.get("arguments") or {}),
                },
            }
            for tc in tool_calls
        ]
        return {
            "role": "assistant",
            "content": content or None,
            "tool_calls": openai_tool_calls,
        }

    def _build_tool_result_message(
        self,
        tc: dict[str, Any],
        result: Any,  # ToolResult
        api_type: str,
    ) -> dict[str, Any]:
        result_text = (
            json.dumps(result.output) if result.success else json.dumps({"error": result.error})
        )

        if api_type == "anthropic":
            return {
                "role": "user",
                "content": [
                    {
                        "type": "tool_result",
                        "tool_use_id": tc["id"],
                        "content": result_text,
                    }
                ],
            }

        if api_type == "google":
            return {
                "role": "user",
                "parts": [
                    {
                        "functionResponse": {
                            "name": tc["name"],
                            "response": result.output
                            if result.success
                            else {"error": result.error},
                        }
                    }
                ],
            }

        # OpenAI-compatible
        return {
            "role": "tool",
            "tool_call_id": tc["id"],
            "content": result_text,
        }

    # ------------------------------------------------------------------
    # Credentials + model helpers (unchanged from original)
    # ------------------------------------------------------------------

    def _get_api_key(self, context: NodeContext) -> str | None:
        ai_provider = get_ai_provider(self.props.provider)
        if not ai_provider:
            return None

        credential_type = ai_provider.id
        selected_credential_id = self.props.credential or self._legacy_selected_credential()
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
            credential = next(
                (item for item in credentials if item.get("type") == credential_type), None
            )

        data = credential.get("data") if credential else None
        if not isinstance(data, dict):
            return None
        api_key = data.get("api_key")
        return api_key if isinstance(api_key, str) and api_key.strip() else None

    def _legacy_selected_credential(self) -> str | None:
        return {
            "openai": self.props.openaiCredential,
            "anthropic": self.props.anthropicCredential,
            "google": self.props.googleCredential,
            "groq": self.props.groqCredential,
        }.get(self.props.provider)

    def _selected_model(self) -> str:
        if self.props.model:
            return self.props.model
        field_name = f"{self.props.provider}Model"
        model = getattr(self.props, field_name, None)
        if model:
            return model
        ai_provider = get_ai_provider(self.props.provider)
        return ai_provider.default_model if ai_provider and ai_provider.default_model else ""

    def _provider_name(self) -> str:
        ai_provider = get_ai_provider(self.props.provider)
        return ai_provider.name if ai_provider else self.props.provider

    def _google_model_path(self, model: str) -> str:
        return model.removeprefix("models/")

    # ------------------------------------------------------------------
    # Message normalization
    # ------------------------------------------------------------------

    def _normalize_messages(self, input_data: dict[str, Any]) -> list[dict[str, Any]]:
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

        messages: list[dict[str, Any]] = []
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

            messages.append(
                {"role": self._normalize_role(role), "content": self._stringify_content(content)}
            )

        return messages

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
            schema = (
                raw_format.get("schema")
                if isinstance(raw_format.get("schema"), dict)
                else raw_format
            )
            return schema

        if isinstance(raw_format.get("type"), str):
            return raw_format

        schema = (
            raw_format.get("schema") if isinstance(raw_format.get("schema"), dict) else raw_format
        )
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

    def _memory_key(self) -> str:
        return self.props.memoryKey or self.node_id

    def _get_provider(self, context: NodeContext) -> Any:
        from apps.api.app.node_system.nodes.ai.agent.memory.providers import get_memory_provider

        # memoryType drives backend selection (workflow → workflow, redis → redis)
        backend = self.props.memoryBackend
        if self.props.memoryType == "redis":
            backend = "redis"
        elif self.props.memoryType == "workflow":
            backend = "workflow"
        # Extract OpenAI API key for embedding (used by Pinecone/Qdrant)
        openai_key = ""
        for cred in context.credentials or []:
            if cred.get("type") == "openai_api_key":
                openai_key = (cred.get("data") or {}).get("api_key", "")
                break
        return get_memory_provider(
            backend,
            context,
            ttl_seconds=self.props.memoryTTL,
            pinecone_api_key=self.props.pineconeApiKey or "",
            pinecone_index=self.props.pineconeIndex or "",
            qdrant_url=self.props.qdrantUrl or "",
            qdrant_collection=self.props.qdrantCollection or "",
            openai_api_key=openai_key,
            mem0_api_key=self.props.mem0ApiKey or "",
        )

    def _apply_memory(
        self, messages: list[dict[str, Any]], context: NodeContext
    ) -> list[dict[str, Any]]:
        if self.props.memoryType == "none":
            return messages
        # Sync wrapper — memory providers are async; run in event loop
        import asyncio

        provider = self._get_provider(context)
        try:
            loop = asyncio.get_event_loop()
            memory = loop.run_until_complete(
                provider.get(self._memory_key(), self.props.memoryLimit)
            )
        except RuntimeError:
            # Already inside event loop (normal case)
            memory = []
        return [*self._normalize_memory(memory), *messages]

    def _persist_memory(
        self, messages: list[dict[str, Any]], assistant_content: str, context: NodeContext
    ) -> list[dict[str, Any]]:
        if self.props.memoryType == "none":
            return []
        # Caller is async — schedule provider.append as a task (called from async context)
        # Return the new messages list for the output
        new_items = [
            message
            for message in messages
            if isinstance(message, dict) and message.get("role") in {"user", "assistant"}
        ]
        if assistant_content:
            new_items.append({"role": "assistant", "content": assistant_content})
        return new_items

    async def _apply_memory_async(
        self, messages: list[dict[str, Any]], context: NodeContext
    ) -> list[dict[str, Any]]:
        if self.props.memoryType == "none":
            return messages
        provider = self._get_provider(context)
        # Use latest user message as semantic query for vector backends
        query = next(
            (str(m.get("content", "")) for m in reversed(messages) if m.get("role") == "user"),
            None,
        )
        raw_memory = await provider.get(self._memory_key(), self.props.memoryLimit, query=query)
        return [*self._normalize_memory(raw_memory), *messages]

    async def _persist_memory_async(
        self, messages: list[dict[str, Any]], assistant_content: str, context: NodeContext
    ) -> list[dict[str, Any]]:
        if self.props.memoryType == "none":
            return []
        new_items = [
            m for m in messages if isinstance(m, dict) and m.get("role") in {"user", "assistant"}
        ]
        if assistant_content:
            new_items.append({"role": "assistant", "content": assistant_content})
        provider = self._get_provider(context)
        await provider.append(self._memory_key(), new_items, self.props.memoryLimit)
        return new_items

    def _normalize_memory(self, memory: list[dict[str, Any]]) -> list[dict[str, Any]]:
        result = []
        for message in memory:
            if isinstance(message, dict) and {"role", "content"} <= set(message):
                result.append(
                    {
                        "role": self._normalize_role(message["role"]),
                        "content": self._stringify_content(message["content"]),
                    }
                )
        return result[-max(self.props.memoryLimit, 1) :]

    # ------------------------------------------------------------------
    # Tool format converters (for legacy format + provider-specific)
    # ------------------------------------------------------------------

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

    def _to_anthropic_tool(self, openai_spec: dict[str, Any]) -> dict[str, Any]:
        """Convert an OpenAI-format tool spec to Anthropic format."""
        fn = (
            openai_spec.get("function")
            if isinstance(openai_spec.get("function"), dict)
            else openai_spec
        )
        return {
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "input_schema": fn.get("parameters") or {"type": "object", "properties": {}},
        }

    def _to_google_tool(self, openai_spec: dict[str, Any]) -> dict[str, Any]:
        """Convert an OpenAI-format tool spec to Google format."""
        fn = (
            openai_spec.get("function")
            if isinstance(openai_spec.get("function"), dict)
            else openai_spec
        )
        return {
            "name": fn.get("name", ""),
            "description": fn.get("description", ""),
            "parameters": fn.get("parameters") or {"type": "object", "properties": {}},
        }

    def _to_anthropic_messages(
        self, messages: list[dict[str, Any]]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        system_messages = [
            message["content"] for message in messages if message.get("role") == "system"
        ]
        chat_messages = [
            {
                "role": "assistant" if message.get("role") == "assistant" else "user",
                "content": message.get("content", ""),
            }
            for message in messages
            if message.get("role") != "system"
        ]
        return ("\n\n".join(system_messages) or None, chat_messages)

    def _to_google_contents(
        self, messages: list[dict[str, Any]]
    ) -> tuple[str | None, list[dict[str, Any]]]:
        system_messages = [
            message["content"] for message in messages if message.get("role") == "system"
        ]
        contents: list[dict[str, Any]] = []
        for message in messages:
            if message.get("role") == "system":
                continue
            role = "model" if message.get("role") == "assistant" else "user"
            contents.append({"role": role, "parts": [{"text": message.get("content", "")}]})
        return ("\n\n".join(system_messages) or None, contents)

    # ------------------------------------------------------------------
    # Output builders
    # ------------------------------------------------------------------

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
        provider_name = self._provider_name()
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
