"""Linear provider manifest — GraphQL via the scaffold's custom-handler hook.

Linear's API is GraphQL-only, so every op is a custom handler: the
scaffold's declarative `method`/`path` path doesn't apply. The factory
still wires up the inspector schema, prop model, credential injection,
and exception → `NodeResult` framing — the handler only has to build
the GraphQL request and shape the response.

Auth: a Linear API key goes into the `Authorization` header *as-is*
(no `Bearer` prefix), so the manifest uses `auth="header_token"` rather
than the bearer scheme.
"""

from __future__ import annotations

from typing import Any

import httpx
from pydantic import BaseModel

from apps.api.app.node_system.base.node_result import NodeResult
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

LINEAR_API = "https://api.linear.app/graphql"


async def _gql(
    client: httpx.AsyncClient,
    headers: dict[str, str],
    query: str,
    variables: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Issue one GraphQL POST and unwrap `errors`/`data`.

    The scaffold's `RESTError` covers HTTP-level failures; GraphQL hands
    back HTTP 200 with an `errors` array on logical failure, so we lift
    that into a regular `RuntimeError` here. The factory converts it to
    a `NodeResult(success=False)` upstream.
    """
    resp = await client.post(
        LINEAR_API,
        headers={**headers, "Content-Type": "application/json"},
        json={"query": query, "variables": variables or {}},
        timeout=30,
    )
    resp.raise_for_status()
    data = resp.json()
    if data.get("errors"):
        raise RuntimeError(data["errors"][0].get("message") or "Linear GraphQL error")
    return data.get("data") or {}


def _issue_input(props: BaseModel) -> dict[str, Any]:
    """Project node props into Linear's `IssueCreateInput` / `IssueUpdateInput`
    shape — skipping unset keys so the API doesn't blank fields the user
    didn't touch."""
    payload: dict[str, Any] = {}
    title = getattr(props, "title", None)
    if title:
        payload["title"] = title
    description = getattr(props, "description", None)
    if description:
        payload["description"] = description
    team_id = getattr(props, "team_id", None)
    if team_id:
        payload["teamId"] = team_id
    state_id = getattr(props, "state_id", None)
    if state_id:
        payload["stateId"] = state_id
    assignee_id = getattr(props, "assignee_id", None)
    if assignee_id:
        payload["assigneeId"] = assignee_id
    priority = getattr(props, "priority", None)
    if priority is not None:
        payload["priority"] = priority
    return payload


# ── handlers ─────────────────────────────────────────────────────────


async def _create_issue(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.title or not node.props.team_id:
        return NodeResult(success=False, error="title and team_id required")
    query = (
        "mutation CreateIssue($input: IssueCreateInput!) {"
        " issueCreate(input: $input) { success issue { id title url identifier } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": _issue_input(node.props)})
    return NodeResult(success=True, output_data=data.get("issueCreate", {}).get("issue", {}))


async def _update_issue(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.issue_id:
        return NodeResult(success=False, error="issue_id required")
    query = (
        "mutation UpdateIssue($id: String!, $input: IssueUpdateInput!) {"
        " issueUpdate(id: $id, input: $input) { success issue { id title url } }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {"id": node.props.issue_id, "input": _issue_input(node.props)},
    )
    return NodeResult(success=True, output_data=data.get("issueUpdate", {}).get("issue", {}))


async def _get_issue(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    if not node.props.issue_id:
        return NodeResult(success=False, error="issue_id required")
    query = (
        "query GetIssue($id: String!) {"
        " issue(id: $id) {"
        " id title description url state { name } assignee { name email } priority createdAt"
        " }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.issue_id})
    return NodeResult(success=True, output_data=data.get("issue") or {})


async def _list_issues(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    query = (
        "query ListIssues {"
        " issues(first: 50) {"
        " nodes { id title url state { name } priority createdAt }"
        " }"
        " }"
    )
    data = await _gql(client, headers, query)
    issues = (data.get("issues") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"issues": issues, "count": len(issues)})


async def _list_teams(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    query = "query ListTeams { teams { nodes { id name key } } }"
    data = await _gql(client, headers, query)
    teams = (data.get("teams") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"teams": teams, "count": len(teams)})


async def _get_viewer(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    query = "query Me { viewer { id name email } }"
    data = await _gql(client, headers, query)
    return NodeResult(success=True, output_data=data.get("viewer") or {})


# ── manifest ─────────────────────────────────────────────────────────


MANIFEST = ProviderManifest(
    type="action.linear",
    name="Linear",
    category="integration",
    description="Create and manage Linear issues, projects, and teams.",
    icon_slug="linear",
    color="#1c1c1c",
    # base_url is unused by the GraphQL handlers (they hit
    # `LINEAR_API` directly), but the scaffold requires a value.
    base_url="https://api.linear.app",
    credential_type="linear_api_key",
    token_field=["api_key"],
    # Linear expects the key bare in `Authorization` — no `Bearer ` prefix.
    auth="header_token",
    auth_header_name="Authorization",
    fields=[
        FieldSpec(
            name="title",
            label="Title",
            type="string",
        ),
        FieldSpec(
            name="description",
            label="Description (Markdown)",
            type="string",
        ),
        FieldSpec(
            name="team_id",
            label="Team ID",
            type="string",
        ),
        FieldSpec(
            name="issue_id",
            label="Issue ID",
            type="string",
        ),
        FieldSpec(
            name="state_id",
            label="State ID",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="assignee_id",
            label="Assignee ID",
            type="string",
            mode="advanced",
        ),
        FieldSpec(
            name="priority",
            label="Priority (0=none,1=urgent,2=high,3=medium,4=low)",
            type="number",
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="create_issue",
            label="Create Issue",
            visible_fields=[
                "title",
                "description",
                "team_id",
                "state_id",
                "assignee_id",
                "priority",
            ],
            handler=_create_issue,
        ),
        OpSpec(
            id="update_issue",
            label="Update Issue",
            visible_fields=[
                "issue_id",
                "title",
                "description",
                "state_id",
                "assignee_id",
                "priority",
            ],
            handler=_update_issue,
        ),
        OpSpec(
            id="get_issue",
            label="Get Issue",
            visible_fields=["issue_id"],
            handler=_get_issue,
        ),
        OpSpec(
            id="list_issues",
            label="List Issues",
            handler=_list_issues,
        ),
        OpSpec(
            id="list_teams",
            label="List Teams",
            handler=_list_teams,
        ),
        OpSpec(
            id="get_viewer",
            label="Get Viewer (me)",
            handler=_get_viewer,
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "issues", "type": "array"},
        {"label": "teams", "type": "array"},
    ],
    allow_error=True,
)
