from __future__ import annotations

import asyncio
import re
from collections.abc import Awaitable, Callable
from typing import Any

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.tools.base import ToolDefinition, ToolResult


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

    def _resolve_oauth_token(self, credential_type: str, context: NodeContext) -> str | None:
        for cred in context.credentials or []:
            if not isinstance(cred, dict):
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
        self, tool_id: str, params: dict[str, Any], context: NodeContext
    ) -> ToolResult:
        # Resolve versioned tool IDs first
        tool_id = self.resolve_tool_id(tool_id)

        defn = self._tools.get(tool_id)
        if not defn or tool_id not in self._executors:
            return ToolResult(success=False, error=f"Unknown tool: {tool_id}")

        # OAuth injection
        if defn.oauth and defn.oauth.required:
            token = self._resolve_oauth_token(defn.oauth.credential_type, context)
            if not token:
                return ToolResult(
                    success=False,
                    error=f"Credential '{defn.oauth.credential_type}' not found",
                )
            params = {**params, "_oauth_token": token}

        # Retry logic
        retry_cfg = defn.retry
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
