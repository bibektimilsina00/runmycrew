"""MCP (Model Context Protocol) action node.

Talks to an MCP server over its **HTTP transport** — the streamable-HTTP
mode servers expose at `/mcp` (or equivalent). Not a stdio subprocess.
This keeps the node stateless and cheap: one initialize + one call +
one close per execution.

Not the official `mcp` SDK — we speak the JSON-RPC 2.0 wire format
directly so a) we don't ship a heavyweight dep, b) the whole flow fits
in one execute() and c) SSE/stdio transports can be layered on later
without changing this contract.

Ops:
  - `list_tools`  — discover tools exposed by the server
  - `call_tool`   — invoke a specific tool with JSON arguments

Credential `mcp_credentials` carries:
  - `endpoint`     — full URL, e.g. https://mcp.example.com/mcp
  - `bearer_token` — optional; passed as `Authorization: Bearer ...`
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

_PROTOCOL_VERSION = "2024-11-05"


class McpProperties(BaseModel):
    operation: str = "call_tool"
    tool_name: str = ""
    arguments: dict[str, Any] = {}


class McpNode(BaseNode[McpProperties]):
    @classmethod
    def get_properties_model(cls):
        return McpProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.mcp",
            name="MCP",
            category="integration",
            inputs=1,
            outputs=1,
            description="Call a Model Context Protocol tool via HTTP transport.",
            icon="mcp",
            color="#1c1c1c",
            credential_type="mcp_credentials",
            properties=[
                {
                    "name": "operation",
                    "label": "Operation",
                    "type": "options",
                    "default": "call_tool",
                    "options": [
                        {"label": "Call Tool", "value": "call_tool"},
                        {"label": "List Tools", "value": "list_tools"},
                    ],
                },
                {
                    "name": "tool_name",
                    "label": "Tool Name",
                    "type": "string",
                    "condition": {"field": "operation", "value": ["call_tool"]},
                },
                {
                    "name": "arguments",
                    "label": "Arguments (JSON)",
                    "type": "json",
                    "default": {},
                    "condition": {"field": "operation", "value": ["call_tool"]},
                },
            ],
            outputs_schema=[
                {"label": "operation", "type": "string"},
                {"label": "tools", "type": "array"},
                {"label": "result", "type": "object"},
                {"label": "content", "type": "array"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        cred = self.credential or {}
        endpoint = cred.get("endpoint") or ""
        if not endpoint:
            return NodeResult(success=False, error="MCP credential missing endpoint URL")

        headers: dict[str, str] = {
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
        }
        token = cred.get("bearer_token") or ""
        if token:
            headers["Authorization"] = f"Bearer {token}"

        p = self.props
        try:
            async with httpx.AsyncClient(timeout=60) as client:
                # Handshake — MCP requires `initialize` before any tool call.
                init_resp = await self._rpc(
                    client,
                    endpoint,
                    headers,
                    "initialize",
                    {
                        "protocolVersion": _PROTOCOL_VERSION,
                        "capabilities": {},
                        "clientInfo": {"name": "runmycrew", "version": "1.0"},
                    },
                    request_id=1,
                )
                if "error" in init_resp:
                    return NodeResult(
                        success=False, error=f"MCP initialize failed: {init_resp['error']}"
                    )

                # `initialized` notification (no id, no response).
                await self._notify(client, endpoint, headers, "notifications/initialized")

                if p.operation == "list_tools":
                    resp = await self._rpc(
                        client, endpoint, headers, "tools/list", {}, request_id=2
                    )
                    if "error" in resp:
                        return NodeResult(success=False, error=str(resp["error"]))
                    return NodeResult(
                        success=True,
                        output_data={
                            "operation": "list_tools",
                            "tools": (resp.get("result") or {}).get("tools") or [],
                        },
                    )

                if p.operation == "call_tool":
                    if not p.tool_name:
                        return NodeResult(success=False, error="tool_name required for call_tool")
                    resp = await self._rpc(
                        client,
                        endpoint,
                        headers,
                        "tools/call",
                        {"name": p.tool_name, "arguments": p.arguments or {}},
                        request_id=2,
                    )
                    if "error" in resp:
                        return NodeResult(success=False, error=str(resp["error"]))
                    result = resp.get("result") or {}
                    return NodeResult(
                        success=True,
                        output_data={
                            "operation": "call_tool",
                            "tool_name": p.tool_name,
                            "result": result,
                            "content": result.get("content") or [],
                            "is_error": bool(result.get("isError")),
                        },
                    )

                return NodeResult(success=False, error=f"Unknown MCP operation: {p.operation}")
        except httpx.HTTPError as e:
            return NodeResult(success=False, error=f"MCP transport failed: {e}")

    @staticmethod
    async def _rpc(
        client: httpx.AsyncClient,
        endpoint: str,
        headers: dict[str, str],
        method: str,
        params: dict[str, Any],
        *,
        request_id: int,
    ) -> dict[str, Any]:
        r = await client.post(
            endpoint,
            headers=headers,
            json={"jsonrpc": "2.0", "id": request_id, "method": method, "params": params},
        )
        r.raise_for_status()
        return r.json()

    @staticmethod
    async def _notify(
        client: httpx.AsyncClient,
        endpoint: str,
        headers: dict[str, str],
        method: str,
    ) -> None:
        # Notifications carry no id and expect no response body.
        await client.post(
            endpoint,
            headers=headers,
            json={"jsonrpc": "2.0", "method": method},
        )
