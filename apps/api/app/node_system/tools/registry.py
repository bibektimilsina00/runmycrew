from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from typing import Any

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.tools.base import ToolDefinition, ToolResult, ToolRetryConfig


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, ToolDefinition] = {}
        self._executors: dict[str, Callable[..., Awaitable[ToolResult]]] = {}

    def register(
        self,
        definition: ToolDefinition,
        executor: Callable[..., Awaitable[ToolResult]],
    ) -> None:
        self._tools[definition.id] = definition
        self._executors[definition.id] = executor

    def get_definition(self, tool_id: str) -> ToolDefinition | None:
        return self._tools.get(tool_id)

    def list_definitions(self) -> list[ToolDefinition]:
        return list(self._tools.values())

    # ------------------------------------------------------------------
    # Version resolution
    # ------------------------------------------------------------------

    def _strip_version_suffix(self, tool_id: str) -> str:
        return re.sub(r"_v\d+$", "", tool_id)

    def resolve_tool_id(self, name: str) -> str:
        if name in self._tools:
            return name
        base = self._strip_version_suffix(name)
        matches = [id_ for id_ in self._tools if self._strip_version_suffix(id_) == base]
        if not matches:
            return name

        def version_num(id_: str) -> int:
            m = re.search(r"_v(\d+)$", id_)
            return int(m.group(1)) if m else 1

        return max(matches, key=version_num)

    # ------------------------------------------------------------------
    # OAuth token resolution
    # ------------------------------------------------------------------

    def _resolve_oauth_token(
        self,
        credential_type: str,
        context: NodeContext,
        credential_id: str | None = None,
    ) -> str | None:
        """Pull an OAuth/API-key token from the workspace credential list.

        When ``credential_id`` is supplied, only the credential with that
        exact id is considered — the user pinned this tool to a specific
        connection in the inspector and we honour that even if other
        connections of the same type exist.
        """
        for cred in context.credentials or []:
            if not isinstance(cred, dict):
                continue
            if credential_id and str(cred.get("id")) != str(credential_id):
                continue
            if cred.get("type") == credential_type:
                data = cred.get("data", {})
                if isinstance(data, dict):
                    token = data.get("access_token") or data.get("bot_token") or data.get("api_key")
                    if isinstance(token, str) and token.strip():
                        return token
        return None

    # ------------------------------------------------------------------
    # execute — version resolution + OAuth injection + retry
    # ------------------------------------------------------------------

    async def execute(
        self,
        tool_id: str,
        params: dict[str, Any],
        context: NodeContext,
        *,
        credential_id: str | None = None,
        retry_override: ToolRetryConfig | None = None,
    ) -> ToolResult:
        """Execute a registered tool.

        ``credential_id`` pins the OAuth resolution to a specific credential
        in the workspace — set by the agent when the user picked a
        connection in the per-tool inspector panel.

        ``retry_override`` replaces the tool's built-in retry config for this
        call — agent-side overrides set by the user.

        Special tool-id prefix ``workflow:<uuid>`` routes through the generic
        ``workflow_executor`` with the bound workflow id, so each workflow
        the inspector exposes as a tool runs without needing its own
        registered ``ToolDefinition``.
        """
        # Workflow-as-tool: strip the prefix and forward to the generic
        # `workflow_executor` with the workflow id baked into params.
        if tool_id.startswith("workflow:"):
            workflow_id = tool_id.split(":", 1)[1]
            params = {**params, "workflowId": workflow_id}
            tool_id = "workflow_executor"

        # Resolve versioned tool IDs first
        tool_id = self.resolve_tool_id(tool_id)

        defn = self._tools.get(tool_id)
        if not defn or tool_id not in self._executors:
            return ToolResult(success=False, error=f"Unknown tool: {tool_id}")

        # OAuth injection
        if defn.oauth and defn.oauth.required:
            token = self._resolve_oauth_token(
                defn.oauth.credential_type, context, credential_id=credential_id
            )
            if not token:
                return ToolResult(
                    success=False,
                    error=f"Credential '{defn.oauth.credential_type}' not found",
                )
            params = {**params, "_oauth_token": token}

        # Retry logic — user override wins over the tool's default.
        retry_cfg = retry_override if retry_override is not None else defn.retry
        max_attempts = (retry_cfg.max_retries + 1) if (retry_cfg and retry_cfg.enabled) else 1

        last_result: ToolResult = ToolResult(success=False, error="No attempts made")
        delay = retry_cfg.initial_delay_ms / 1000.0 if retry_cfg else 1.0
        max_delay = retry_cfg.max_delay_ms / 1000.0 if retry_cfg else 10.0

        for attempt in range(max_attempts):
            try:
                last_result = await self._executors[tool_id](params, context)
                if last_result.success:
                    return last_result
                if attempt < max_attempts - 1:
                    await asyncio.sleep(min(delay, max_delay))
                    delay *= 2
            except Exception as e:
                last_result = ToolResult(success=False, error=str(e))
                if attempt < max_attempts - 1:
                    await asyncio.sleep(min(delay, max_delay))
                    delay *= 2

        return last_result

    def to_openai_schema(self, tool_id: str) -> dict[str, Any] | None:
        """Convert a tool definition to OpenAI function calling schema.
        Includes only user-or-llm and llm-only params."""
        defn = self._tools.get(tool_id)
        if not defn:
            return None
        properties: dict[str, Any] = {}
        required: list[str] = []
        for name, param in defn.params.items():
            if param.visibility in ("user-or-llm", "llm-only"):
                prop: dict[str, Any] = {"type": self._to_json_type(param.type)}
                if param.description:
                    prop["description"] = param.description
                properties[name] = prop
                if param.required and param.visibility == "user-or-llm":
                    required.append(name)
        return {
            "type": "function",
            "function": {
                "name": tool_id,
                "description": defn.description,
                "parameters": {
                    "type": "object",
                    "properties": properties,
                    **({"required": required} if required else {}),
                },
            },
        }

    def _to_json_type(self, tool_type: str) -> str:
        return {"number": "number", "boolean": "boolean"}.get(tool_type, "string")


tool_registry = ToolRegistry()
