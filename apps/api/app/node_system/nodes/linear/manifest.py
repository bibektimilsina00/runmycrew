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
from apps.api.app.node_system.nodes.linear import COLOR, ICON_SLUG, NAME
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


# ── added handlers (depth fill) ──────────────────────────────────────


async def _archive_issue(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.issue_id:
        return NodeResult(success=False, error="issue_id required")
    query = "mutation ArchiveIssue($id: String!) { issueArchive(id: $id) { success } }"
    data = await _gql(client, headers, query, {"id": node.props.issue_id})
    return NodeResult(success=True, output_data=data.get("issueArchive") or {})


async def _delete_issue(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.issue_id:
        return NodeResult(success=False, error="issue_id required")
    query = "mutation DeleteIssue($id: String!) { issueDelete(id: $id) { success } }"
    data = await _gql(client, headers, query, {"id": node.props.issue_id})
    return NodeResult(success=True, output_data=data.get("issueDelete") or {})


async def _search_issues(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    term = getattr(node.props, "search_term", None) or ""
    query = (
        "query SearchIssues($term: String!) {"
        " issueSearch(term: $term) {"
        " nodes { id title url state { name } priority createdAt }"
        " }"
        " }"
    )
    data = await _gql(client, headers, query, {"term": term})
    nodes = (data.get("issueSearch") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"issues": nodes, "count": len(nodes)})


async def _create_comment(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.issue_id or not getattr(node.props, "comment_body", None):
        return NodeResult(success=False, error="issue_id and comment_body required")
    query = (
        "mutation CreateComment($input: CommentCreateInput!) {"
        " commentCreate(input: $input) { success comment { id body url } }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {"input": {"issueId": node.props.issue_id, "body": node.props.comment_body}},
    )
    return NodeResult(success=True, output_data=data.get("commentCreate", {}).get("comment") or {})


async def _list_comments(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.issue_id:
        return NodeResult(success=False, error="issue_id required")
    query = (
        "query IssueComments($id: String!) {"
        " issue(id: $id) { comments { nodes { id body user { name } createdAt } } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.issue_id})
    comments = ((data.get("issue") or {}).get("comments") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"comments": comments, "count": len(comments)})


async def _list_projects(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    query = (
        "query ListProjects { projects(first: 50) {"
        " nodes { id name url state startDate targetDate progress }"
        " } }"
    )
    data = await _gql(client, headers, query)
    projects = (data.get("projects") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"projects": projects, "count": len(projects)})


async def _get_project(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    if not getattr(node.props, "project_id", None):
        return NodeResult(success=False, error="project_id required")
    query = (
        "query GetProject($id: String!) {"
        " project(id: $id) { id name description url state progress startDate targetDate }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.project_id})
    return NodeResult(success=True, output_data=data.get("project") or {})


async def _create_project(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    name = getattr(node.props, "title", None)
    team_id = getattr(node.props, "team_id", None)
    if not name or not team_id:
        return NodeResult(success=False, error="title and team_id required")
    query = (
        "mutation CreateProject($input: ProjectCreateInput!) {"
        " projectCreate(input: $input) { success project { id name url } }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {
            "input": {
                "name": name,
                "description": getattr(node.props, "description", None) or "",
                "teamIds": [team_id],
            }
        },
    )
    return NodeResult(success=True, output_data=data.get("projectCreate", {}).get("project") or {})


async def _list_users(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    query = "query ListUsers { users(first: 100) { nodes { id name email active } } }"
    data = await _gql(client, headers, query)
    users = (data.get("users") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"users": users, "count": len(users)})


async def _list_labels(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    query = "query ListLabels { issueLabels { nodes { id name color } } }"
    data = await _gql(client, headers, query)
    labels = (data.get("issueLabels") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"labels": labels, "count": len(labels)})


async def _list_workflow_states(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    query = "query ListStates { workflowStates { nodes { id name type color team { name } } } }"
    data = await _gql(client, headers, query)
    states = (data.get("workflowStates") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"states": states, "count": len(states)})


async def _list_cycles(node: Any, client: httpx.AsyncClient, headers: dict[str, str]) -> NodeResult:
    query = (
        "query ListCycles { cycles(first: 50) {"
        " nodes { id number name startsAt endsAt progress team { name } }"
        " } }"
    )
    data = await _gql(client, headers, query)
    cycles = (data.get("cycles") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"cycles": cycles, "count": len(cycles)})


async def _add_label_to_issue(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.issue_id or not getattr(node.props, "label_id", None):
        return NodeResult(success=False, error="issue_id and label_id required")
    query = (
        "mutation AddLabel($id: String!, $labelId: String!) {"
        " issueAddLabel(id: $id, labelId: $labelId) { success }"
        " }"
    )
    data = await _gql(
        client, headers, query, {"id": node.props.issue_id, "labelId": node.props.label_id}
    )
    return NodeResult(success=True, output_data=data.get("issueAddLabel") or {})


async def _remove_label_from_issue(
    node: Any, client: httpx.AsyncClient, headers: dict[str, str]
) -> NodeResult:
    if not node.props.issue_id or not getattr(node.props, "label_id", None):
        return NodeResult(success=False, error="issue_id and label_id required")
    query = (
        "mutation RemoveLabel($id: String!, $labelId: String!) {"
        " issueRemoveLabel(id: $id, labelId: $labelId) { success }"
        " }"
    )
    data = await _gql(
        client, headers, query, {"id": node.props.issue_id, "labelId": node.props.label_id}
    )
    return NodeResult(success=True, output_data=data.get("issueRemoveLabel") or {})


# ── Phase 4-close-6h — remaining 58 ops via GraphQL handler factories ─
#
# Rather than hand-write 58 near-identical GraphQL handlers, define
# small helpers that emit the standard shapes (list / get / create /
# update / delete / archive / unarchive). Each handler validates its
# required inputs, issues one GraphQL round-trip via `_gql`, and
# unwraps the response.


def _entity_input(props: Any, keys: list[tuple[str, str]]) -> dict[str, Any]:
    """Project node props into a GraphQL input dict, dropping unset
    keys so Linear doesn't blank out fields the caller didn't touch.
    `keys` is a list of `(prop_name, gql_field_name)` tuples."""
    payload: dict[str, Any] = {}
    for prop_name, gql_name in keys:
        val = getattr(props, prop_name, None)
        if val is None or val == "":
            continue
        payload[gql_name] = val
    return payload


async def _list_first_50(
    node: Any,
    client: httpx.AsyncClient,
    headers: dict[str, str],
    *,
    connection: str,
    fields: str,
    filter_arg: str = "",
) -> NodeResult:
    """Generic `xxx(first: 50) { nodes { ... } }` query."""
    args = "(first: 50" + (", " + filter_arg if filter_arg else "") + ")"
    query = f"query List {{ {connection}{args} {{ nodes {{ {fields} }} }} }}"
    data = await _gql(client, headers, query)
    nodes = (data.get(connection) or {}).get("nodes") or []
    return NodeResult(success=True, output_data={connection: nodes, "count": len(nodes)})


async def _by_id_query(
    node: Any,
    client: httpx.AsyncClient,
    headers: dict[str, str],
    *,
    resource: str,
    id_prop: str,
    fields: str,
) -> NodeResult:
    id_val = getattr(node.props, id_prop, None)
    if not id_val:
        return NodeResult(success=False, error=f"{id_prop} required")
    query = f"query Get($id: String!) {{ {resource}(id: $id) {{ {fields} }} }}"
    data = await _gql(client, headers, query, {"id": id_val})
    return NodeResult(success=True, output_data=data.get(resource) or {})


async def _mutation_id_only(
    node: Any,
    client: httpx.AsyncClient,
    headers: dict[str, str],
    *,
    mutation: str,
    id_prop: str = "issue_id",
    result_key: str | None = None,
) -> NodeResult:
    """Mutations that take just `id`: archive, unarchive, delete."""
    id_val = getattr(node.props, id_prop, None)
    if not id_val:
        return NodeResult(success=False, error=f"{id_prop} required")
    query = f"mutation Do($id: String!) {{ {mutation}(id: $id) {{ success }} }}"
    data = await _gql(client, headers, query, {"id": id_val})
    return NodeResult(success=True, output_data=data.get(result_key or mutation) or {})


async def _mutation_with_input(
    node: Any,
    client: httpx.AsyncClient,
    headers: dict[str, str],
    *,
    mutation: str,
    input_type: str,
    input_data: dict[str, Any],
    result_key: str,
    result_fields: str = "id",
    result_container: str | None = None,
) -> NodeResult:
    """Mutations of the shape `xxxCreate(input: {...}) { success xxx { ... } }`."""
    container = result_container or result_key.replace("Create", "").replace("Update", "").replace(
        "Delete", ""
    )
    container = container[0].lower() + container[1:]
    query = (
        f"mutation Do($input: {input_type}!) {{"
        f" {mutation}(input: $input) {{ success {container} {{ {result_fields} }} }}"
        f" }}"
    )
    data = await _gql(client, headers, query, {"input": input_data})
    return NodeResult(success=True, output_data=(data.get(mutation) or {}).get(container) or {})


# ── issue extras ─────────────────────────────────────────────────


async def _unarchive_issue(node, client, headers):
    return await _mutation_id_only(node, client, headers, mutation="issueUnarchive")


async def _update_comment(node, client, headers):
    if not getattr(node.props, "comment_id", None):
        return NodeResult(success=False, error="comment_id required")
    query = (
        "mutation UpdateComment($id: String!, $input: CommentUpdateInput!) {"
        " commentUpdate(id: $id, input: $input) { success comment { id body } }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {
            "id": node.props.comment_id,
            "input": {"body": getattr(node.props, "comment_body", "") or ""},
        },
    )
    return NodeResult(
        success=True, output_data=(data.get("commentUpdate") or {}).get("comment") or {}
    )


async def _delete_comment(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="commentDelete", id_prop="comment_id"
    )


# ── projects extras ──────────────────────────────────────────────


async def _update_project(node, client, headers):
    if not getattr(node.props, "project_id", None):
        return NodeResult(success=False, error="project_id required")
    payload = _entity_input(node.props, [("title", "name"), ("description", "description")])
    query = (
        "mutation UpdateProject($id: String!, $input: ProjectUpdateInput!) {"
        " projectUpdate(id: $id, input: $input) { success project { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.project_id, "input": payload})
    return NodeResult(
        success=True, output_data=(data.get("projectUpdate") or {}).get("project") or {}
    )


async def _archive_project(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="projectArchive", id_prop="project_id"
    )


async def _delete_project(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="projectDelete", id_prop="project_id"
    )


# ── labels extras ────────────────────────────────────────────────


async def _create_label(node, client, headers):
    if not getattr(node.props, "title", None):
        return NodeResult(success=False, error="title required")
    payload = _entity_input(
        node.props,
        [
            ("title", "name"),
            ("description", "description"),
            ("team_id", "teamId"),
            ("label_color", "color"),
        ],
    )
    query = (
        "mutation CreateLabel($input: IssueLabelCreateInput!) {"
        " issueLabelCreate(input: $input) { success issueLabel { id name color } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("issueLabelCreate") or {}).get("issueLabel") or {}
    )


async def _update_label(node, client, headers):
    if not getattr(node.props, "label_id", None):
        return NodeResult(success=False, error="label_id required")
    payload = _entity_input(
        node.props, [("title", "name"), ("description", "description"), ("label_color", "color")]
    )
    query = (
        "mutation UpdateLabel($id: String!, $input: IssueLabelUpdateInput!) {"
        " issueLabelUpdate(id: $id, input: $input) { success issueLabel { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.label_id, "input": payload})
    return NodeResult(
        success=True, output_data=(data.get("issueLabelUpdate") or {}).get("issueLabel") or {}
    )


async def _archive_label(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="issueLabelArchive", id_prop="label_id"
    )


# ── workflow states extras ───────────────────────────────────────


async def _create_workflow_state(node, client, headers):
    payload = _entity_input(
        node.props,
        [
            ("title", "name"),
            ("team_id", "teamId"),
            ("state_type", "type"),
            ("label_color", "color"),
        ],
    )
    query = (
        "mutation CreateState($input: WorkflowStateCreateInput!) {"
        " workflowStateCreate(input: $input) { success workflowState { id name type } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("workflowStateCreate") or {}).get("workflowState") or {}
    )


async def _update_workflow_state(node, client, headers):
    if not getattr(node.props, "state_id", None):
        return NodeResult(success=False, error="state_id required")
    payload = _entity_input(node.props, [("title", "name"), ("label_color", "color")])
    query = (
        "mutation UpdateState($id: String!, $input: WorkflowStateUpdateInput!) {"
        " workflowStateUpdate(id: $id, input: $input) { success workflowState { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.state_id, "input": payload})
    return NodeResult(
        success=True, output_data=(data.get("workflowStateUpdate") or {}).get("workflowState") or {}
    )


# ── cycles extras ────────────────────────────────────────────────


async def _get_cycle(node, client, headers):
    return await _by_id_query(
        node,
        client,
        headers,
        resource="cycle",
        id_prop="cycle_id",
        fields="id number name startsAt endsAt progress",
    )


async def _create_cycle(node, client, headers):
    payload = _entity_input(
        node.props,
        [
            ("team_id", "teamId"),
            ("title", "name"),
            ("starts_at", "startsAt"),
            ("ends_at", "endsAt"),
        ],
    )
    query = (
        "mutation CreateCycle($input: CycleCreateInput!) {"
        " cycleCreate(input: $input) { success cycle { id number name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(success=True, output_data=(data.get("cycleCreate") or {}).get("cycle") or {})


async def _get_active_cycle(node, client, headers):
    if not getattr(node.props, "team_id", None):
        return NodeResult(success=False, error="team_id required")
    query = (
        "query ActiveCycle($id: String!) {"
        " team(id: $id) { activeCycle { id number name startsAt endsAt progress } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.team_id})
    return NodeResult(success=True, output_data=(data.get("team") or {}).get("activeCycle") or {})


# ── attachments ─────────────────────────────────────────────────


async def _create_attachment(node, client, headers):
    payload = _entity_input(
        node.props,
        [
            ("issue_id", "issueId"),
            ("title", "title"),
            ("attachment_url", "url"),
            ("attachment_subtitle", "subtitle"),
        ],
    )
    query = (
        "mutation CreateAttachment($input: AttachmentCreateInput!) {"
        " attachmentCreate(input: $input) { success attachment { id title url } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("attachmentCreate") or {}).get("attachment") or {}
    )


async def _list_attachments(node, client, headers):
    if not getattr(node.props, "issue_id", None):
        return NodeResult(success=False, error="issue_id required")
    query = (
        "query IssueAttachments($id: String!) {"
        " issue(id: $id) { attachments { nodes { id title url subtitle } } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.issue_id})
    atts = ((data.get("issue") or {}).get("attachments") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"attachments": atts, "count": len(atts)})


async def _update_attachment(node, client, headers):
    if not getattr(node.props, "attachment_id", None):
        return NodeResult(success=False, error="attachment_id required")
    payload = _entity_input(node.props, [("title", "title"), ("attachment_subtitle", "subtitle")])
    query = (
        "mutation UpdateAttachment($id: String!, $input: AttachmentUpdateInput!) {"
        " attachmentUpdate(id: $id, input: $input) { success attachment { id title } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.attachment_id, "input": payload})
    return NodeResult(
        success=True, output_data=(data.get("attachmentUpdate") or {}).get("attachment") or {}
    )


async def _delete_attachment(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="attachmentDelete", id_prop="attachment_id"
    )


# ── issue relations ─────────────────────────────────────────────


async def _create_issue_relation(node, client, headers):
    payload = _entity_input(
        node.props,
        [
            ("issue_id", "issueId"),
            ("related_issue_id", "relatedIssueId"),
            ("relation_type", "type"),
        ],
    )
    query = (
        "mutation CreateRel($input: IssueRelationCreateInput!) {"
        " issueRelationCreate(input: $input) { success issueRelation { id type } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("issueRelationCreate") or {}).get("issueRelation") or {}
    )


async def _list_issue_relations(node, client, headers):
    if not getattr(node.props, "issue_id", None):
        return NodeResult(success=False, error="issue_id required")
    query = (
        "query IssueRelations($id: String!) {"
        " issue(id: $id) { relations { nodes { id type relatedIssue { id title } } } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.issue_id})
    rels = ((data.get("issue") or {}).get("relations") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"relations": rels, "count": len(rels)})


async def _delete_issue_relation(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="issueRelationDelete", id_prop="relation_id"
    )


# ── favorites ────────────────────────────────────────────────────


async def _create_favorite(node, client, headers):
    payload = _entity_input(node.props, [("issue_id", "issueId"), ("project_id", "projectId")])
    if not payload:
        return NodeResult(success=False, error="issue_id or project_id required")
    query = (
        "mutation CreateFav($input: FavoriteCreateInput!) {"
        " favoriteCreate(input: $input) { success favorite { id } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("favoriteCreate") or {}).get("favorite") or {}
    )


async def _list_favorites(node, client, headers):
    query = (
        "query Favs { favorites(first: 50) {"
        " nodes { id type folderName issue { id title } project { id name } } } }"
    )
    data = await _gql(client, headers, query)
    favs = (data.get("favorites") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"favorites": favs, "count": len(favs)})


# ── project updates ─────────────────────────────────────────────


async def _create_project_update(node, client, headers):
    payload = _entity_input(
        node.props,
        [("project_id", "projectId"), ("update_body", "body"), ("update_health", "health")],
    )
    query = (
        "mutation CreatePU($input: ProjectUpdateCreateInput!) {"
        " projectUpdateCreate(input: $input) { success projectUpdate { id body health } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("projectUpdateCreate") or {}).get("projectUpdate") or {}
    )


async def _list_project_updates(node, client, headers):
    if not getattr(node.props, "project_id", None):
        return NodeResult(success=False, error="project_id required")
    query = (
        "query PU($id: String!) {"
        " project(id: $id) { projectUpdates { nodes { id body health createdAt } } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.project_id})
    updates = ((data.get("project") or {}).get("projectUpdates") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"projectUpdates": updates, "count": len(updates)})


# ── notifications ───────────────────────────────────────────────


async def _list_notifications(node, client, headers):
    query = (
        "query Notifs { notifications(first: 50) { nodes { id type readAt emailedAt createdAt } } }"
    )
    data = await _gql(client, headers, query)
    ns = (data.get("notifications") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"notifications": ns, "count": len(ns)})


async def _update_notification(node, client, headers):
    if not getattr(node.props, "notification_id", None):
        return NodeResult(success=False, error="notification_id required")
    payload = _entity_input(node.props, [("mark_read", "readAt")])
    query = (
        "mutation UpdateNotif($id: String!, $input: NotificationUpdateInput!) {"
        " notificationUpdate(id: $id, input: $input) { success notification { id readAt } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.notification_id, "input": payload})
    return NodeResult(
        success=True, output_data=(data.get("notificationUpdate") or {}).get("notification") or {}
    )


# ── customers (needs) ───────────────────────────────────────────


async def _create_customer(node, client, headers):
    payload = _entity_input(node.props, [("title", "name"), ("customer_domain", "domain")])
    query = (
        "mutation CreateCust($input: CustomerCreateInput!) {"
        " customerCreate(input: $input) { success customer { id name domain } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("customerCreate") or {}).get("customer") or {}
    )


async def _list_customers(node, client, headers):
    return await _list_first_50(
        node, client, headers, connection="customers", fields="id name domain size externalIds"
    )


async def _get_customer(node, client, headers):
    return await _by_id_query(
        node,
        client,
        headers,
        resource="customer",
        id_prop="customer_id",
        fields="id name domain size externalIds",
    )


async def _update_customer(node, client, headers):
    if not getattr(node.props, "customer_id", None):
        return NodeResult(success=False, error="customer_id required")
    payload = _entity_input(node.props, [("title", "name"), ("customer_domain", "domain")])
    query = (
        "mutation UpdateCust($id: String!, $input: CustomerUpdateInput!) {"
        " customerUpdate(id: $id, input: $input) { success customer { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.customer_id, "input": payload})
    return NodeResult(
        success=True, output_data=(data.get("customerUpdate") or {}).get("customer") or {}
    )


async def _delete_customer(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="customerDelete", id_prop="customer_id"
    )


async def _merge_customers(node, client, headers):
    if not getattr(node.props, "customer_id", None) or not getattr(
        node.props, "target_customer_id", None
    ):
        return NodeResult(success=False, error="customer_id and target_customer_id required")
    query = (
        "mutation Merge($id: String!, $into: String!) {"
        " customerMerge(id: $id, mergeIntoId: $into) { success customer { id name } }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {"id": node.props.customer_id, "into": node.props.target_customer_id},
    )
    return NodeResult(
        success=True, output_data=(data.get("customerMerge") or {}).get("customer") or {}
    )


# ── customer requests ───────────────────────────────────────────


async def _create_customer_request(node, client, headers):
    payload = _entity_input(
        node.props,
        [("customer_id", "customerId"), ("issue_id", "issueId"), ("customer_request_body", "body")],
    )
    query = (
        "mutation CreateCR($input: CustomerNeedCreateInput!) {"
        " customerNeedCreate(input: $input) { success customerNeed { id body } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("customerNeedCreate") or {}).get("customerNeed") or {}
    )


async def _update_customer_request(node, client, headers):
    if not getattr(node.props, "customer_request_id", None):
        return NodeResult(success=False, error="customer_request_id required")
    payload = _entity_input(node.props, [("customer_request_body", "body")])
    query = (
        "mutation UpdateCR($id: String!, $input: CustomerNeedUpdateInput!) {"
        " customerNeedUpdate(id: $id, input: $input) { success customerNeed { id body } }"
        " }"
    )
    data = await _gql(
        client, headers, query, {"id": node.props.customer_request_id, "input": payload}
    )
    return NodeResult(
        success=True, output_data=(data.get("customerNeedUpdate") or {}).get("customerNeed") or {}
    )


async def _list_customer_requests(node, client, headers):
    return await _list_first_50(
        node,
        client,
        headers,
        connection="customerNeeds",
        fields="id body customer { id name } issue { id title }",
    )


# ── customer statuses ───────────────────────────────────────────


async def _create_customer_status(node, client, headers):
    payload = _entity_input(
        node.props, [("title", "name"), ("label_color", "color"), ("status_type", "type")]
    )
    query = (
        "mutation CreateCS($input: CustomerStatusCreateInput!) {"
        " customerStatusCreate(input: $input) { success customerStatus { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True,
        output_data=(data.get("customerStatusCreate") or {}).get("customerStatus") or {},
    )


async def _update_customer_status(node, client, headers):
    if not getattr(node.props, "customer_status_id", None):
        return NodeResult(success=False, error="customer_status_id required")
    payload = _entity_input(node.props, [("title", "name"), ("label_color", "color")])
    query = (
        "mutation UpdateCS($id: String!, $input: CustomerStatusUpdateInput!) {"
        " customerStatusUpdate(id: $id, input: $input) { success customerStatus { id name } }"
        " }"
    )
    data = await _gql(
        client, headers, query, {"id": node.props.customer_status_id, "input": payload}
    )
    return NodeResult(
        success=True,
        output_data=(data.get("customerStatusUpdate") or {}).get("customerStatus") or {},
    )


async def _delete_customer_status(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="customerStatusDelete", id_prop="customer_status_id"
    )


async def _list_customer_statuses(node, client, headers):
    return await _list_first_50(
        node, client, headers, connection="customerStatuses", fields="id name color type"
    )


# ── customer tiers ──────────────────────────────────────────────


async def _create_customer_tier(node, client, headers):
    payload = _entity_input(node.props, [("title", "name"), ("label_color", "color")])
    query = (
        "mutation CreateCT($input: CustomerTierCreateInput!) {"
        " customerTierCreate(input: $input) { success customerTier { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("customerTierCreate") or {}).get("customerTier") or {}
    )


async def _update_customer_tier(node, client, headers):
    if not getattr(node.props, "customer_tier_id", None):
        return NodeResult(success=False, error="customer_tier_id required")
    payload = _entity_input(node.props, [("title", "name"), ("label_color", "color")])
    query = (
        "mutation UpdateCT($id: String!, $input: CustomerTierUpdateInput!) {"
        " customerTierUpdate(id: $id, input: $input) { success customerTier { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.customer_tier_id, "input": payload})
    return NodeResult(
        success=True, output_data=(data.get("customerTierUpdate") or {}).get("customerTier") or {}
    )


async def _delete_customer_tier(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="customerTierDelete", id_prop="customer_tier_id"
    )


async def _list_customer_tiers(node, client, headers):
    return await _list_first_50(
        node, client, headers, connection="customerTiers", fields="id name color"
    )


# ── project labels ──────────────────────────────────────────────


async def _create_project_label(node, client, headers):
    payload = _entity_input(node.props, [("title", "name"), ("label_color", "color")])
    query = (
        "mutation CreatePL($input: ProjectLabelCreateInput!) {"
        " projectLabelCreate(input: $input) { success projectLabel { id name color } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("projectLabelCreate") or {}).get("projectLabel") or {}
    )


async def _update_project_label(node, client, headers):
    if not getattr(node.props, "project_label_id", None):
        return NodeResult(success=False, error="project_label_id required")
    payload = _entity_input(node.props, [("title", "name"), ("label_color", "color")])
    query = (
        "mutation UpdatePL($id: String!, $input: ProjectLabelUpdateInput!) {"
        " projectLabelUpdate(id: $id, input: $input) { success projectLabel { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.project_label_id, "input": payload})
    return NodeResult(
        success=True, output_data=(data.get("projectLabelUpdate") or {}).get("projectLabel") or {}
    )


async def _delete_project_label(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="projectLabelDelete", id_prop="project_label_id"
    )


async def _list_project_labels(node, client, headers):
    return await _list_first_50(
        node, client, headers, connection="projectLabels", fields="id name color"
    )


async def _add_label_to_project(node, client, headers):
    if not getattr(node.props, "project_id", None) or not getattr(
        node.props, "project_label_id", None
    ):
        return NodeResult(success=False, error="project_id and project_label_id required")
    query = (
        "mutation AddLabelToProject($id: String!, $labelId: String!) {"
        " projectAddLabel(id: $id, labelId: $labelId) { success }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {"id": node.props.project_id, "labelId": node.props.project_label_id},
    )
    return NodeResult(success=True, output_data=data.get("projectAddLabel") or {})


async def _remove_label_from_project(node, client, headers):
    if not getattr(node.props, "project_id", None) or not getattr(
        node.props, "project_label_id", None
    ):
        return NodeResult(success=False, error="project_id and project_label_id required")
    query = (
        "mutation RemoveLabelFromProject($id: String!, $labelId: String!) {"
        " projectRemoveLabel(id: $id, labelId: $labelId) { success }"
        " }"
    )
    data = await _gql(
        client,
        headers,
        query,
        {"id": node.props.project_id, "labelId": node.props.project_label_id},
    )
    return NodeResult(success=True, output_data=data.get("projectRemoveLabel") or {})


# ── project milestones ──────────────────────────────────────────


async def _create_project_milestone(node, client, headers):
    payload = _entity_input(
        node.props,
        [
            ("project_id", "projectId"),
            ("title", "name"),
            ("description", "description"),
            ("target_date", "targetDate"),
        ],
    )
    query = (
        "mutation CreatePM($input: ProjectMilestoneCreateInput!) {"
        " projectMilestoneCreate(input: $input) { success projectMilestone { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True,
        output_data=(data.get("projectMilestoneCreate") or {}).get("projectMilestone") or {},
    )


async def _update_project_milestone(node, client, headers):
    if not getattr(node.props, "milestone_id", None):
        return NodeResult(success=False, error="milestone_id required")
    payload = _entity_input(
        node.props,
        [("title", "name"), ("description", "description"), ("target_date", "targetDate")],
    )
    query = (
        "mutation UpdatePM($id: String!, $input: ProjectMilestoneUpdateInput!) {"
        " projectMilestoneUpdate(id: $id, input: $input) { success projectMilestone { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.milestone_id, "input": payload})
    return NodeResult(
        success=True,
        output_data=(data.get("projectMilestoneUpdate") or {}).get("projectMilestone") or {},
    )


async def _delete_project_milestone(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="projectMilestoneDelete", id_prop="milestone_id"
    )


async def _list_project_milestones(node, client, headers):
    if not getattr(node.props, "project_id", None):
        return NodeResult(success=False, error="project_id required")
    query = (
        "query PM($id: String!) {"
        " project(id: $id) { projectMilestones { nodes { id name description targetDate progress } } }"
        " }"
    )
    data = await _gql(client, headers, query, {"id": node.props.project_id})
    ms = ((data.get("project") or {}).get("projectMilestones") or {}).get("nodes") or []
    return NodeResult(success=True, output_data={"projectMilestones": ms, "count": len(ms)})


# ── project statuses ────────────────────────────────────────────


async def _create_project_status(node, client, headers):
    payload = _entity_input(
        node.props, [("title", "name"), ("label_color", "color"), ("status_type", "type")]
    )
    query = (
        "mutation CreatePS($input: ProjectStatusCreateInput!) {"
        " projectStatusCreate(input: $input) { success projectStatus { id name } }"
        " }"
    )
    data = await _gql(client, headers, query, {"input": payload})
    return NodeResult(
        success=True, output_data=(data.get("projectStatusCreate") or {}).get("projectStatus") or {}
    )


async def _update_project_status(node, client, headers):
    if not getattr(node.props, "project_status_id", None):
        return NodeResult(success=False, error="project_status_id required")
    payload = _entity_input(node.props, [("title", "name"), ("label_color", "color")])
    query = (
        "mutation UpdatePS($id: String!, $input: ProjectStatusUpdateInput!) {"
        " projectStatusUpdate(id: $id, input: $input) { success projectStatus { id name } }"
        " }"
    )
    data = await _gql(
        client, headers, query, {"id": node.props.project_status_id, "input": payload}
    )
    return NodeResult(
        success=True, output_data=(data.get("projectStatusUpdate") or {}).get("projectStatus") or {}
    )


async def _delete_project_status(node, client, headers):
    return await _mutation_id_only(
        node, client, headers, mutation="projectStatusDelete", id_prop="project_status_id"
    )


async def _list_project_statuses(node, client, headers):
    return await _list_first_50(
        node, client, headers, connection="projectStatuses", fields="id name color type"
    )


# ── manifest ─────────────────────────────────────────────────────────

MANIFEST = ProviderManifest(
    type="action.linear",
    name=NAME,
    category="integration",
    description="Create and manage Linear issues, projects, and teams.",
    icon_slug=ICON_SLUG,
    color=COLOR,
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
        FieldSpec(name="comment_body", label="Comment Body", type="string"),
        FieldSpec(name="search_term", label="Search Term", type="string"),
        FieldSpec(name="project_id", label="Project ID", type="string"),
        FieldSpec(name="label_id", label="Label ID", type="string"),
        # Phase 4-close-6h additions
        FieldSpec(name="comment_id", label="Comment ID", type="string"),
        FieldSpec(name="label_color", label="Label Color (hex)", type="string"),
        FieldSpec(name="state_type", label="Workflow State Type", type="string"),
        FieldSpec(name="cycle_id", label="Cycle ID", type="string"),
        FieldSpec(name="starts_at", label="Starts At (ISO)", type="string"),
        FieldSpec(name="ends_at", label="Ends At (ISO)", type="string"),
        FieldSpec(name="attachment_id", label="Attachment ID", type="string"),
        FieldSpec(name="attachment_url", label="Attachment URL", type="string"),
        FieldSpec(name="attachment_subtitle", label="Attachment Subtitle", type="string"),
        FieldSpec(name="related_issue_id", label="Related Issue ID", type="string"),
        FieldSpec(
            name="relation_type", label="Relation Type (blocks|duplicate|related)", type="string"
        ),
        FieldSpec(name="relation_id", label="Relation ID", type="string"),
        FieldSpec(name="notification_id", label="Notification ID", type="string"),
        FieldSpec(name="mark_read", label="Mark Read Timestamp (ISO)", type="string"),
        FieldSpec(name="customer_id", label="Customer ID", type="string"),
        FieldSpec(name="customer_domain", label="Customer Domain", type="string"),
        FieldSpec(
            name="target_customer_id", label="Target Customer ID (merge into)", type="string"
        ),
        FieldSpec(name="customer_request_id", label="Customer Request ID", type="string"),
        FieldSpec(name="customer_request_body", label="Customer Request Body", type="string"),
        FieldSpec(name="customer_status_id", label="Customer Status ID", type="string"),
        FieldSpec(name="status_type", label="Status Type (active|churned|prospect)", type="string"),
        FieldSpec(name="customer_tier_id", label="Customer Tier ID", type="string"),
        FieldSpec(name="project_label_id", label="Project Label ID", type="string"),
        FieldSpec(name="milestone_id", label="Milestone ID", type="string"),
        FieldSpec(name="target_date", label="Target Date (ISO)", type="string"),
        FieldSpec(name="project_status_id", label="Project Status ID", type="string"),
        FieldSpec(name="update_body", label="Update Body (Markdown)", type="string"),
        FieldSpec(
            name="update_health", label="Update Health (onTrack|atRisk|offTrack)", type="string"
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
        # ─── depth expansions ─────────────────────────────────────
        OpSpec(
            id="archive_issue",
            label="Archive Issue",
            visible_fields=["issue_id"],
            handler=_archive_issue,
        ),
        OpSpec(
            id="delete_issue",
            label="Delete Issue",
            visible_fields=["issue_id"],
            handler=_delete_issue,
        ),
        OpSpec(
            id="search_issues",
            label="Search Issues",
            visible_fields=["search_term"],
            handler=_search_issues,
        ),
        OpSpec(
            id="create_comment",
            label="Create Comment",
            visible_fields=["issue_id", "comment_body"],
            handler=_create_comment,
        ),
        OpSpec(
            id="list_comments",
            label="List Issue Comments",
            visible_fields=["issue_id"],
            handler=_list_comments,
        ),
        OpSpec(id="list_projects", label="List Projects", handler=_list_projects),
        OpSpec(
            id="get_project",
            label="Get Project",
            visible_fields=["project_id"],
            handler=_get_project,
        ),
        OpSpec(
            id="create_project",
            label="Create Project",
            visible_fields=["title", "description", "team_id"],
            handler=_create_project,
        ),
        OpSpec(id="list_users", label="List Users", handler=_list_users),
        OpSpec(id="list_labels", label="List Labels", handler=_list_labels),
        OpSpec(
            id="list_workflow_states",
            label="List Workflow States",
            handler=_list_workflow_states,
        ),
        OpSpec(id="list_cycles", label="List Cycles", handler=_list_cycles),
        OpSpec(
            id="add_label_to_issue",
            label="Add Label to Issue",
            visible_fields=["issue_id", "label_id"],
            handler=_add_label_to_issue,
        ),
        OpSpec(
            id="remove_label_from_issue",
            label="Remove Label from Issue",
            visible_fields=["issue_id", "label_id"],
            handler=_remove_label_from_issue,
        ),
        # ─── Phase 4-close-6h — remaining 58 GraphQL ops ───────────
        # issues
        OpSpec(
            id="unarchive_issue",
            label="Unarchive Issue",
            visible_fields=["issue_id"],
            handler=_unarchive_issue,
        ),
        # comments
        OpSpec(
            id="update_comment",
            label="Update Comment",
            visible_fields=["comment_id", "comment_body"],
            handler=_update_comment,
        ),
        OpSpec(
            id="delete_comment",
            label="Delete Comment",
            visible_fields=["comment_id"],
            handler=_delete_comment,
        ),
        # projects
        OpSpec(
            id="update_project",
            label="Update Project",
            visible_fields=["project_id", "title", "description"],
            handler=_update_project,
        ),
        OpSpec(
            id="archive_project",
            label="Archive Project",
            visible_fields=["project_id"],
            handler=_archive_project,
        ),
        OpSpec(
            id="delete_project",
            label="Delete Project",
            visible_fields=["project_id"],
            handler=_delete_project,
        ),
        # labels
        OpSpec(
            id="create_label",
            label="Create Label",
            visible_fields=["title", "description", "team_id", "label_color"],
            handler=_create_label,
        ),
        OpSpec(
            id="update_label",
            label="Update Label",
            visible_fields=["label_id", "title", "description", "label_color"],
            handler=_update_label,
        ),
        OpSpec(
            id="archive_label",
            label="Archive Label",
            visible_fields=["label_id"],
            handler=_archive_label,
        ),
        # workflow states
        OpSpec(
            id="create_workflow_state",
            label="Create Workflow State",
            visible_fields=["title", "team_id", "state_type", "label_color"],
            handler=_create_workflow_state,
        ),
        OpSpec(
            id="update_workflow_state",
            label="Update Workflow State",
            visible_fields=["state_id", "title", "label_color"],
            handler=_update_workflow_state,
        ),
        # cycles
        OpSpec(id="get_cycle", label="Get Cycle", visible_fields=["cycle_id"], handler=_get_cycle),
        OpSpec(
            id="create_cycle",
            label="Create Cycle",
            visible_fields=["team_id", "title", "starts_at", "ends_at"],
            handler=_create_cycle,
        ),
        OpSpec(
            id="get_active_cycle",
            label="Get Active Cycle (team)",
            visible_fields=["team_id"],
            handler=_get_active_cycle,
        ),
        # attachments
        OpSpec(
            id="create_attachment",
            label="Create Attachment",
            visible_fields=["issue_id", "title", "attachment_url", "attachment_subtitle"],
            handler=_create_attachment,
        ),
        OpSpec(
            id="list_attachments",
            label="List Issue Attachments",
            visible_fields=["issue_id"],
            handler=_list_attachments,
        ),
        OpSpec(
            id="update_attachment",
            label="Update Attachment",
            visible_fields=["attachment_id", "title", "attachment_subtitle"],
            handler=_update_attachment,
        ),
        OpSpec(
            id="delete_attachment",
            label="Delete Attachment",
            visible_fields=["attachment_id"],
            handler=_delete_attachment,
        ),
        # issue relations
        OpSpec(
            id="create_issue_relation",
            label="Create Issue Relation",
            visible_fields=["issue_id", "related_issue_id", "relation_type"],
            handler=_create_issue_relation,
        ),
        OpSpec(
            id="list_issue_relations",
            label="List Issue Relations",
            visible_fields=["issue_id"],
            handler=_list_issue_relations,
        ),
        OpSpec(
            id="delete_issue_relation",
            label="Delete Issue Relation",
            visible_fields=["relation_id"],
            handler=_delete_issue_relation,
        ),
        # favorites
        OpSpec(
            id="create_favorite",
            label="Create Favorite",
            visible_fields=["issue_id", "project_id"],
            handler=_create_favorite,
        ),
        OpSpec(id="list_favorites", label="List Favorites", handler=_list_favorites),
        # project updates
        OpSpec(
            id="create_project_update",
            label="Create Project Update",
            visible_fields=["project_id", "update_body", "update_health"],
            handler=_create_project_update,
        ),
        OpSpec(
            id="list_project_updates",
            label="List Project Updates",
            visible_fields=["project_id"],
            handler=_list_project_updates,
        ),
        # notifications
        OpSpec(id="list_notifications", label="List Notifications", handler=_list_notifications),
        OpSpec(
            id="update_notification",
            label="Update Notification (mark read)",
            visible_fields=["notification_id", "mark_read"],
            handler=_update_notification,
        ),
        # customers
        OpSpec(
            id="create_customer",
            label="Create Customer",
            visible_fields=["title", "customer_domain"],
            handler=_create_customer,
        ),
        OpSpec(id="list_customers", label="List Customers", handler=_list_customers),
        OpSpec(
            id="get_customer",
            label="Get Customer",
            visible_fields=["customer_id"],
            handler=_get_customer,
        ),
        OpSpec(
            id="update_customer",
            label="Update Customer",
            visible_fields=["customer_id", "title", "customer_domain"],
            handler=_update_customer,
        ),
        OpSpec(
            id="delete_customer",
            label="Delete Customer",
            visible_fields=["customer_id"],
            handler=_delete_customer,
        ),
        OpSpec(
            id="merge_customers",
            label="Merge Customers",
            visible_fields=["customer_id", "target_customer_id"],
            handler=_merge_customers,
        ),
        # customer requests
        OpSpec(
            id="create_customer_request",
            label="Create Customer Request",
            visible_fields=["customer_id", "issue_id", "customer_request_body"],
            handler=_create_customer_request,
        ),
        OpSpec(
            id="update_customer_request",
            label="Update Customer Request",
            visible_fields=["customer_request_id", "customer_request_body"],
            handler=_update_customer_request,
        ),
        OpSpec(
            id="list_customer_requests",
            label="List Customer Requests",
            handler=_list_customer_requests,
        ),
        # customer statuses
        OpSpec(
            id="create_customer_status",
            label="Create Customer Status",
            visible_fields=["title", "label_color", "status_type"],
            handler=_create_customer_status,
        ),
        OpSpec(
            id="update_customer_status",
            label="Update Customer Status",
            visible_fields=["customer_status_id", "title", "label_color"],
            handler=_update_customer_status,
        ),
        OpSpec(
            id="delete_customer_status",
            label="Delete Customer Status",
            visible_fields=["customer_status_id"],
            handler=_delete_customer_status,
        ),
        OpSpec(
            id="list_customer_statuses",
            label="List Customer Statuses",
            handler=_list_customer_statuses,
        ),
        # customer tiers
        OpSpec(
            id="create_customer_tier",
            label="Create Customer Tier",
            visible_fields=["title", "label_color"],
            handler=_create_customer_tier,
        ),
        OpSpec(
            id="update_customer_tier",
            label="Update Customer Tier",
            visible_fields=["customer_tier_id", "title", "label_color"],
            handler=_update_customer_tier,
        ),
        OpSpec(
            id="delete_customer_tier",
            label="Delete Customer Tier",
            visible_fields=["customer_tier_id"],
            handler=_delete_customer_tier,
        ),
        OpSpec(id="list_customer_tiers", label="List Customer Tiers", handler=_list_customer_tiers),
        # project labels
        OpSpec(
            id="create_project_label",
            label="Create Project Label",
            visible_fields=["title", "label_color"],
            handler=_create_project_label,
        ),
        OpSpec(
            id="update_project_label",
            label="Update Project Label",
            visible_fields=["project_label_id", "title", "label_color"],
            handler=_update_project_label,
        ),
        OpSpec(
            id="delete_project_label",
            label="Delete Project Label",
            visible_fields=["project_label_id"],
            handler=_delete_project_label,
        ),
        OpSpec(id="list_project_labels", label="List Project Labels", handler=_list_project_labels),
        OpSpec(
            id="add_label_to_project",
            label="Add Label to Project",
            visible_fields=["project_id", "project_label_id"],
            handler=_add_label_to_project,
        ),
        OpSpec(
            id="remove_label_from_project",
            label="Remove Label from Project",
            visible_fields=["project_id", "project_label_id"],
            handler=_remove_label_from_project,
        ),
        # project milestones
        OpSpec(
            id="create_project_milestone",
            label="Create Project Milestone",
            visible_fields=["project_id", "title", "description", "target_date"],
            handler=_create_project_milestone,
        ),
        OpSpec(
            id="update_project_milestone",
            label="Update Project Milestone",
            visible_fields=["milestone_id", "title", "description", "target_date"],
            handler=_update_project_milestone,
        ),
        OpSpec(
            id="delete_project_milestone",
            label="Delete Project Milestone",
            visible_fields=["milestone_id"],
            handler=_delete_project_milestone,
        ),
        OpSpec(
            id="list_project_milestones",
            label="List Project Milestones",
            visible_fields=["project_id"],
            handler=_list_project_milestones,
        ),
        # project statuses
        OpSpec(
            id="create_project_status",
            label="Create Project Status",
            visible_fields=["title", "label_color", "status_type"],
            handler=_create_project_status,
        ),
        OpSpec(
            id="update_project_status",
            label="Update Project Status",
            visible_fields=["project_status_id", "title", "label_color"],
            handler=_update_project_status,
        ),
        OpSpec(
            id="delete_project_status",
            label="Delete Project Status",
            visible_fields=["project_status_id"],
            handler=_delete_project_status,
        ),
        OpSpec(
            id="list_project_statuses",
            label="List Project Statuses",
            handler=_list_project_statuses,
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
