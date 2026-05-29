from __future__ import annotations

import json
from typing import Any

import httpx

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.tools.base import ToolDefinition, ToolParam, ToolResult

logger = get_logger(__name__)


class MCPClient:
    """
    HTTP-based MCP (Model Context Protocol) client.
    Communicates with an MCP server via JSON-RPC 2.0 over HTTP POST.
    """

    def __init__(self, server_name: str, url: str, api_key: str | None = None):
        self.server_name = server_name
        self.url = url.rstrip("/")
        self.api_key = api_key
        self._request_id = 0

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _next_id(self) -> int:
        self._request_id += 1
        return self._request_id

    def _tool_id(self, tool_name: str) -> str:
        return f"mcp:{self.server_name}:{tool_name}"

    async def list_tools(self) -> list[ToolDefinition]:
        """Fetch tool list from MCP server and convert to ToolDefinition objects."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/list",
            "params": {},
            "id": self._next_id(),
        }
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.post(self.url, headers=self._headers(), json=payload)
            response.raise_for_status()
            data = response.json()

        tools_raw = (data.get("result") or {}).get("tools") or []
        definitions: list[ToolDefinition] = []
        for tool in tools_raw:
            name = tool.get("name", "")
            if not name:
                continue
            description = tool.get("description", "")
            input_schema = tool.get("inputSchema") or {}
            properties = input_schema.get("properties") or {}
            required_fields = set(input_schema.get("required") or [])

            params: dict[str, ToolParam] = {}
            for param_name, param_schema in properties.items():
                param_type = param_schema.get("type", "string")
                if param_type not in ("string", "number", "boolean"):
                    param_type = "string"
                params[param_name] = ToolParam(
                    type=param_type,
                    required=param_name in required_fields,
                    description=param_schema.get("description", ""),
                    visibility="user-or-llm",
                )

            definitions.append(
                ToolDefinition(
                    id=self._tool_id(name),
                    name=f"{self.server_name}: {name}",
                    description=description,
                    params=params,
                )
            )
        return definitions

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> ToolResult:
        """Call a tool on the MCP server."""
        payload = {
            "jsonrpc": "2.0",
            "method": "tools/call",
            "params": {"name": tool_name, "arguments": arguments},
            "id": self._next_id(),
        }
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.url, headers=self._headers(), json=payload)
                response.raise_for_status()
                data = response.json()

            if "error" in data:
                error = data["error"]
                msg = error.get("message", str(error))
                return ToolResult(success=False, error=f"MCP error: {msg}")

            result = data.get("result") or {}
            content = result.get("content") or []

            # Extract text content from MCP content blocks
            output_parts: list[str] = []
            for block in content:
                if not isinstance(block, dict):
                    continue
                if block.get("type") == "text":
                    output_parts.append(block.get("text", ""))
                elif block.get("type") == "resource":
                    resource = block.get("resource") or {}
                    output_parts.append(resource.get("text", json.dumps(resource)))

            return ToolResult(
                success=True,
                output={"content": "\n".join(output_parts), "raw": content},
            )
        except httpx.HTTPStatusError as e:
            return ToolResult(
                success=False,
                error=f"MCP HTTP error {e.response.status_code}: {e.response.text[:200]}",
            )
        except Exception as e:
            return ToolResult(success=False, error=f"MCP call failed: {e}")
