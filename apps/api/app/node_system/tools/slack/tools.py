from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.tools.base import ToolDefinition, ToolOAuth, ToolParam, ToolResult
from apps.api.app.node_system.tools.registry import tool_registry

SLACK_API_BASE = "https://slack.com/api"

_SLACK_OAUTH = ToolOAuth(required=True, credential_type="slack_oauth")


def _get_slack_token(params: dict[str, Any], context: NodeContext) -> str | None:
    # Injected by ToolRegistry when oauth is declared
    if (token := params.get("_oauth_token")) and isinstance(token, str) and token.strip():
        return token
    # Fallback: manual search (backwards compat)
    for cred in context.credentials or []:
        if not isinstance(cred, dict):
            continue
        if cred.get("type") in ("slack_oauth", "slack_bot_token"):
            data = cred.get("data", {})
            if isinstance(data, dict):
                token = data.get("access_token") or data.get("bot_token")
                if isinstance(token, str) and token.strip():
                    return token
    return None


async def _execute_slack(params: dict[str, Any], context: NodeContext) -> ToolResult:
    from apps.api.app.execution_engine.engine.node_executor import node_executor

    result = await node_executor.execute_node(
        node_type="action.slack",
        node_id="tool:slack",
        properties=params,
        input_data={},
        context=context,
    )
    return ToolResult(
        success=result.success,
        output=result.output_data,
        error=result.error,
    )


tool_registry.register(
    ToolDefinition(
        id="slack",
        name="Slack",
        description=(
            "Perform Slack operations: send/update/delete messages, list channels, "
            "manage users, add reactions, and more. "
            'Always set "operation" to one of the supported values.'
        ),
        params={
            "operation": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description=(
                    "Operation to perform. Must be one of: "
                    "send_message, update_message, delete_message, send_ephemeral, "
                    "list_channels, get_channel_info, create_channel, list_members, "
                    "invite_to_channel, list_users, get_user_info, get_user_presence, "
                    "add_reaction, remove_reaction, get_message"
                ),
            ),
            "channel": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="Channel ID (e.g. C1234567890) — required for most operations",
            ),
            "text": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="Message text — required for send_message, update_message, send_ephemeral",
            ),
            "ts": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="Message timestamp — required for update_message, delete_message, get_message",
            ),
            "thread_ts": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="Thread timestamp to reply into an existing thread",
            ),
            "user": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="User ID — required for send_ephemeral, get_user_info, get_user_presence, invite_to_channel",
            ),
            "name": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="New channel name for create_channel; emoji name (without colons) for add_reaction/remove_reaction",
            ),
            "users": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="Comma-separated user IDs for invite_to_channel",
            ),
            "blocks": ToolParam(
                type="json",
                visibility="user-or-llm",
                description="Slack Block Kit JSON array — optional, for rich message formatting",
            ),
            "trigger_id": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="Trigger ID for modal operations (open_view, push_view)",
            ),
            "view": ToolParam(
                type="json",
                visibility="user-or-llm",
                description="Block Kit view payload for modal operations",
            ),
            "view_id": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="View ID for update_view",
            ),
        },
    ),
    _execute_slack,
)


async def _slack_post(
    token: str,
    endpoint: str,
    payload: dict[str, Any],
    http_client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    should_close = http_client is None
    client = http_client or httpx.AsyncClient()
    try:
        resp = await client.post(
            f"{SLACK_API_BASE}/{endpoint}",
            headers={
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json; charset=utf-8",
            },
            json=payload,
        )
        resp.raise_for_status()
        return resp.json()
    finally:
        if should_close:
            await client.aclose()


async def _slack_get(
    token: str,
    endpoint: str,
    params: dict[str, Any] | None = None,
    http_client: httpx.AsyncClient | None = None,
) -> dict[str, Any]:
    should_close = http_client is None
    client = http_client or httpx.AsyncClient()
    try:
        resp = await client.get(
            f"{SLACK_API_BASE}/{endpoint}",
            headers={"Authorization": f"Bearer {token}"},
            params=params or {},
        )
        resp.raise_for_status()
        return resp.json()
    finally:
        if should_close:
            await client.aclose()


# ---------------------------------------------------------------------------
# send_message
# ---------------------------------------------------------------------------


async def _execute_send_message(params: dict[str, Any], context: NodeContext) -> ToolResult:
    token = _get_slack_token(params, context)
    if not token:
        return ToolResult(success=False, error="Slack credential not found")

    payload: dict[str, Any] = {
        "channel": params.get("channel", ""),
        "text": params.get("text", ""),
    }
    if params.get("thread_ts"):
        payload["thread_ts"] = params["thread_ts"]
    if params.get("blocks") is not None:
        payload["blocks"] = params["blocks"]

    data = await _slack_post(token, "chat.postMessage", payload, context.http_client)
    if not data.get("ok"):
        return ToolResult(success=False, error=data.get("error", "Slack API error"))
    return ToolResult(success=True, output=data)


tool_registry.register(
    ToolDefinition(
        id="slack_send_message",
        name="Send Slack Message",
        description="Send a message to a Slack channel",
        params={
            "channel": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description="Channel ID (e.g. C1234567890)",
            ),
            "text": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description="Message text",
            ),
            "thread_ts": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="Thread timestamp to reply to",
            ),
            "blocks": ToolParam(
                type="json",
                visibility="user-or-llm",
                description="Block Kit blocks JSON",
            ),
        },
        oauth=_SLACK_OAUTH,
    ),
    _execute_send_message,
)


# ---------------------------------------------------------------------------
# update_message
# ---------------------------------------------------------------------------


async def _execute_update_message(params: dict[str, Any], context: NodeContext) -> ToolResult:
    token = _get_slack_token(params, context)
    if not token:
        return ToolResult(success=False, error="Slack credential not found")

    payload: dict[str, Any] = {
        "channel": params.get("channel", ""),
        "ts": params.get("ts", ""),
    }
    if params.get("text") is not None:
        payload["text"] = params["text"]
    if params.get("blocks") is not None:
        payload["blocks"] = params["blocks"]

    data = await _slack_post(token, "chat.update", payload, context.http_client)
    if not data.get("ok"):
        return ToolResult(success=False, error=data.get("error", "Slack API error"))
    return ToolResult(success=True, output=data)


tool_registry.register(
    ToolDefinition(
        id="slack_update_message",
        name="Update Slack Message",
        description="Update an existing message in a Slack channel",
        params={
            "channel": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description="Channel ID",
            ),
            "ts": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description="Message timestamp to update",
            ),
            "text": ToolParam(
                type="string",
                visibility="user-or-llm",
                description="New message text",
            ),
            "blocks": ToolParam(
                type="json",
                visibility="user-or-llm",
                description="New Block Kit blocks JSON",
            ),
        },
        oauth=_SLACK_OAUTH,
    ),
    _execute_update_message,
)


# ---------------------------------------------------------------------------
# delete_message
# ---------------------------------------------------------------------------


async def _execute_delete_message(params: dict[str, Any], context: NodeContext) -> ToolResult:
    token = _get_slack_token(params, context)
    if not token:
        return ToolResult(success=False, error="Slack credential not found")

    payload: dict[str, Any] = {
        "channel": params.get("channel", ""),
        "ts": params.get("ts", ""),
    }

    data = await _slack_post(token, "chat.delete", payload, context.http_client)
    if not data.get("ok"):
        return ToolResult(success=False, error=data.get("error", "Slack API error"))
    return ToolResult(success=True, output=data)


tool_registry.register(
    ToolDefinition(
        id="slack_delete_message",
        name="Delete Slack Message",
        description="Delete a message from a Slack channel",
        params={
            "channel": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description="Channel ID",
            ),
            "ts": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description="Message timestamp to delete",
            ),
        },
        oauth=_SLACK_OAUTH,
    ),
    _execute_delete_message,
)


# ---------------------------------------------------------------------------
# list_channels
# ---------------------------------------------------------------------------


async def _execute_list_channels(params: dict[str, Any], context: NodeContext) -> ToolResult:
    token = _get_slack_token(params, context)
    if not token:
        return ToolResult(success=False, error="Slack credential not found")

    query_params: dict[str, Any] = {}
    if params.get("limit") is not None:
        query_params["limit"] = int(params["limit"])

    data = await _slack_get(token, "conversations.list", query_params, context.http_client)
    if not data.get("ok"):
        return ToolResult(success=False, error=data.get("error", "Slack API error"))
    return ToolResult(success=True, output=data)


tool_registry.register(
    ToolDefinition(
        id="slack_list_channels",
        name="List Slack Channels",
        description="List all channels in a Slack workspace",
        params={
            "limit": ToolParam(
                type="number",
                visibility="user-only",
                description="Maximum number of channels to return",
            ),
        },
        oauth=_SLACK_OAUTH,
    ),
    _execute_list_channels,
)


# ---------------------------------------------------------------------------
# get_channel_info
# ---------------------------------------------------------------------------


async def _execute_get_channel_info(params: dict[str, Any], context: NodeContext) -> ToolResult:
    token = _get_slack_token(params, context)
    if not token:
        return ToolResult(success=False, error="Slack credential not found")

    data = await _slack_get(
        token,
        "conversations.info",
        {"channel": params.get("channel", "")},
        context.http_client,
    )
    if not data.get("ok"):
        return ToolResult(success=False, error=data.get("error", "Slack API error"))
    return ToolResult(success=True, output=data)


tool_registry.register(
    ToolDefinition(
        id="slack_get_channel_info",
        name="Get Slack Channel Info",
        description="Get information about a Slack channel",
        params={
            "channel": ToolParam(
                type="string",
                required=True,
                visibility="user-or-llm",
                description="Channel ID",
            ),
        },
        oauth=_SLACK_OAUTH,
    ),
    _execute_get_channel_info,
)
