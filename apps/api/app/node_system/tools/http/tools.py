from __future__ import annotations

import json
from typing import Any

import httpx

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.tools.base import ToolDefinition, ToolParam, ToolResult
from apps.api.app.node_system.tools.registry import tool_registry


async def _execute_http_request(params: dict[str, Any], context: NodeContext) -> ToolResult:
    url = params.get("url")
    if not isinstance(url, str) or not url.strip():
        return ToolResult(success=False, error="'url' parameter is required")

    method = str(params.get("method") or "GET").upper()
    raw_headers = params.get("headers")
    raw_body = params.get("body")

    headers: dict[str, str] = {}
    if isinstance(raw_headers, dict):
        headers = {str(k): str(v) for k, v in raw_headers.items()}
    elif isinstance(raw_headers, str) and raw_headers.strip():
        try:
            parsed = json.loads(raw_headers)
            if isinstance(parsed, dict):
                headers = {str(k): str(v) for k, v in parsed.items()}
        except json.JSONDecodeError:
            pass

    body: Any = None
    if raw_body is not None:
        if isinstance(raw_body, (dict, list)):
            body = raw_body
        elif isinstance(raw_body, str) and raw_body.strip():
            try:
                body = json.loads(raw_body)
            except json.JSONDecodeError:
                body = raw_body

    should_close = context.http_client is None
    client: httpx.AsyncClient = context.http_client or httpx.AsyncClient()
    try:
        request_kwargs: dict[str, Any] = {
            "url": url,
            "headers": headers,
        }
        if body is not None:
            if isinstance(body, (dict, list)):
                request_kwargs["json"] = body
            else:
                request_kwargs["content"] = str(body).encode()

        resp = await client.request(method, **request_kwargs)
        try:
            response_body = resp.json()
        except Exception:
            response_body = resp.text

        return ToolResult(
            success=True,
            output={
                "status_code": resp.status_code,
                "headers": dict(resp.headers),
                "body": response_body,
            },
        )
    except httpx.HTTPStatusError as e:
        return ToolResult(
            success=False,
            error=f"HTTP {e.response.status_code}: {e.response.text[:500]}",
        )
    finally:
        if should_close:
            await client.aclose()


tool_registry.register(
    ToolDefinition(
        id="http_request",
        name="HTTP Request",
        description="Make an HTTP request to any URL",
        params={
            "url": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description="URL to request",
            ),
            "method": ToolParam(
                type="string",
                visibility="user-only",
                description="HTTP method (GET, POST, PUT, DELETE, PATCH). Defaults to GET if not set.",
            ),
            "headers": ToolParam(
                type="json",
                visibility="user-only",
                description="HTTP headers as JSON object",
            ),
            "body": ToolParam(
                type="json",
                visibility="user-or-llm",
                description="Request body as JSON",
            ),
        },
    ),
    _execute_http_request,
)
