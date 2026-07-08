"""Monday.com action node — manifest form.

Monday's API is GraphQL-only. Every op below is a `CustomHandler`
that builds a GraphQL request; the scaffold owns prop validation +
credential injection + error framing.

Auth: API key in the `Authorization` header *bare* (no Bearer prefix),
same pattern as Linear — use `auth="header_token"`.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.nodes.monday import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MONDAY_API = "https://api.monday.com/v2"


async def _gql(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Issue one GraphQL POST. Lifts `errors` into a RuntimeError so the
    scaffold turns them into a structured NodeResult failure."""
    resp = await client.post(
        MONDAY_API,
        headers={**headers, "Content-Type": "application/json", "API-Version": "2024-01"},
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json() or {}
    if data.get("errors"):
        raise RuntimeError(data["errors"][0].get("message") or "Monday GraphQL error")
    return data.get("data") or {}


async def _list_boards(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    limit = int(getattr(node.props, "limit", 25) or 25)
    query = "query ListBoards($limit: Int) { boards(limit: $limit) { id name state board_kind } }"
    data = await _gql(client, headers, query, {"limit": limit})
    boards = data.get("boards") or []
    return NodeResult(success=True, output_data={"boards": boards, "count": len(boards)})


async def _get_board(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    board_id = getattr(node.props, "board_id", None)
    if not board_id:
        return NodeResult(success=False, error="board_id required")
    query = (
        "query GetBoard($id: [ID!]) {"
        " boards(ids: $id) {"
        " id name state description"
        " items_page(limit: 100) { items { id name column_values { id text value } } }"
        " columns { id title type }"
        " }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": [str(board_id)]})
    boards = data.get("boards") or []
    return NodeResult(success=True, output_data=boards[0] if boards else {})


async def _create_item(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    board_id = getattr(node.props, "board_id", None)
    item_name = getattr(node.props, "item_name", None)
    if not board_id or not item_name:
        return NodeResult(success=False, error="board_id and item_name required")
    column_values = getattr(node.props, "column_values", None) or {}
    import json as _json

    query = (
        "mutation CreateItem($board: ID!, $name: String!, $vals: JSON) {"
        " create_item(board_id: $board, item_name: $name, column_values: $vals)"
        " { id name }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {"board": str(board_id), "name": item_name, "vals": _json.dumps(column_values)},
    )
    return NodeResult(success=True, output_data=data.get("create_item") or {})


async def _update_item(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    board_id = getattr(node.props, "board_id", None)
    item_id = getattr(node.props, "item_id", None)
    column_values = getattr(node.props, "column_values", None) or {}
    if not board_id or not item_id:
        return NodeResult(success=False, error="board_id and item_id required")
    import json as _json

    query = (
        "mutation UpdateItem($board: ID!, $item: ID!, $vals: JSON!) {"
        " change_multiple_column_values(board_id: $board, item_id: $item, column_values: $vals)"
        " { id name }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {"board": str(board_id), "item": str(item_id), "vals": _json.dumps(column_values)},
    )
    return NodeResult(success=True, output_data=data.get("change_multiple_column_values") or {})


async def _delete_item(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    item_id = getattr(node.props, "item_id", None)
    if not item_id:
        return NodeResult(success=False, error="item_id required")
    query = "mutation DeleteItem($id: ID!) { delete_item(item_id: $id) { id } }"
    data = await _gql(client, headers, query, {"id": str(item_id)})
    return NodeResult(success=True, output_data=data.get("delete_item") or {})


async def _add_update(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    item_id = getattr(node.props, "item_id", None)
    body = getattr(node.props, "body", None)
    if not item_id or not body:
        return NodeResult(success=False, error="item_id and body required")
    query = (
        "mutation AddUpdate($item: ID!, $body: String!) {"
        " create_update(item_id: $item, body: $body) { id body }"
        " }"
    )
    data = await _gql(client, headers, query, {"item": str(item_id), "body": body})
    return NodeResult(success=True, output_data=data.get("create_update") or {})


MANIFEST = ProviderManifest(
    type="action.monday",
    name=NAME,
    category="integration",
    description="Monday.com — manage boards, items, updates via GraphQL.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://api.monday.com",
    credential_type="monday_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="Authorization",
    fields=[
        FieldSpec(name="board_id", label="Board ID", type="string"),
        FieldSpec(name="item_id", label="Item ID", type="string"),
        FieldSpec(name="item_name", label="Item Name", type="string"),
        FieldSpec(name="column_values", label="Column Values (JSON)", type="json"),
        FieldSpec(name="body", label="Update body", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=25, mode="advanced"),
        FieldSpec(name="monday_query", label="GraphQL Query", type="string"),
        FieldSpec(
            name="monday_variables", label="GraphQL Variables (JSON)", type="json", default={}
        ),
    ],
    operations=[
        OpSpec(
            id="list_boards", label="List Boards", visible_fields=["limit"], handler=_list_boards
        ),
        OpSpec(id="get_board", label="Get Board", visible_fields=["board_id"], handler=_get_board),
        OpSpec(
            id="create_item",
            label="Create Item",
            visible_fields=["board_id", "item_name", "column_values"],
            handler=_create_item,
        ),
        OpSpec(
            id="update_item",
            label="Update Item",
            visible_fields=["board_id", "item_id", "column_values"],
            handler=_update_item,
        ),
        OpSpec(
            id="delete_item",
            label="Delete Item",
            visible_fields=["item_id"],
            handler=_delete_item,
        ),
        OpSpec(
            id="add_update",
            label="Add Update to Item",
            visible_fields=["item_id", "body"],
            handler=_add_update,
        ),
        OpSpec(
            id="get_item",
            label="Get Item",
            method="POST",
            path="/v2",
            visible_fields=["monday_variables"],
            body_builder=lambda v: {
                "query": "query($id: [ID!]) { items(ids: $id) { id name column_values { id text } } }",
                "variables": getattr(v, "monday_variables", None) or {},
            },
        ),
        OpSpec(
            id="get_items",
            label="Get Items",
            method="POST",
            path="/v2",
            visible_fields=["monday_variables"],
            body_builder=lambda v: {
                "query": "query($ids: [ID!]) { items(ids: $ids) { id name } }",
                "variables": getattr(v, "monday_variables", None) or {},
            },
        ),
        OpSpec(
            id="search_items",
            label="Search Items",
            method="POST",
            path="/v2",
            visible_fields=["monday_query"],
            body_builder=lambda v: {"query": getattr(v, "monday_query", "") or ""},
        ),
        OpSpec(
            id="archive_item",
            label="Archive Item",
            method="POST",
            path="/v2",
            visible_fields=["monday_variables"],
            body_builder=lambda v: {
                "query": "mutation($id: ID!) { archive_item(item_id: $id) { id } }",
                "variables": getattr(v, "monday_variables", None) or {},
            },
        ),
        OpSpec(
            id="move_item_to_group",
            label="Move Item to Group",
            method="POST",
            path="/v2",
            visible_fields=["monday_variables"],
            body_builder=lambda v: {
                "query": "mutation($item: ID!, $group: String!) { move_item_to_group(item_id: $item, group_id: $group) { id } }",
                "variables": getattr(v, "monday_variables", None) or {},
            },
        ),
        OpSpec(
            id="create_subitem",
            label="Create Subitem",
            method="POST",
            path="/v2",
            visible_fields=["monday_variables"],
            body_builder=lambda v: {
                "query": "mutation($parent: ID!, $name: String!) { create_subitem(parent_item_id: $parent, item_name: $name) { id } }",
                "variables": getattr(v, "monday_variables", None) or {},
            },
        ),
        OpSpec(
            id="create_update",
            label="Create Update (comment)",
            method="POST",
            path="/v2",
            visible_fields=["monday_variables"],
            body_builder=lambda v: {
                "query": "mutation($item: ID!, $body: String!) { create_update(item_id: $item, body: $body) { id } }",
                "variables": getattr(v, "monday_variables", None) or {},
            },
        ),
        OpSpec(
            id="create_group",
            label="Create Group on Board",
            method="POST",
            path="/v2",
            visible_fields=["monday_variables"],
            body_builder=lambda v: {
                "query": "mutation($board: ID!, $name: String!) { create_group(board_id: $board, group_name: $name) { id } }",
                "variables": getattr(v, "monday_variables", None) or {},
            },
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "boards", "type": "array"},
        {"label": "items", "type": "array"},
        {"label": "count", "type": "number"},
    ],
    allow_error=True,
)
