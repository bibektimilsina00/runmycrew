"""Linear polling trigger — manifest form.

Linear is GraphQL-only; the scaffold's default GET-based fetcher
doesn't fit. Custom paginate_fn issues a GraphQL POST against
`https://api.linear.app/graphql` with an issues/comments query
sorted by createdAt / updatedAt desc.

Auth: raw key in `Authorization` (no `Bearer` prefix — Linear
convention).
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)

_LINEAR_API = "https://api.linear.app/graphql"

# Team-scoped issue query. `filter` is threaded in when the user
# supplies a team_id in props.
_ISSUES_QUERY_NEW = """
query NewIssues($first: Int!, $filter: IssueFilter) {
  issues(first: $first, orderBy: createdAt, filter: $filter) {
    nodes {
      id identifier title url priority createdAt updatedAt
      state { id name type }
      assignee { id name email }
      team { id name key }
    }
  }
}
"""

_ISSUES_QUERY_UPDATED = """
query UpdatedIssues($first: Int!, $filter: IssueFilter) {
  issues(first: $first, orderBy: updatedAt, filter: $filter) {
    nodes {
      id identifier title url priority createdAt updatedAt
      state { id name type }
      assignee { id name email }
      team { id name key }
    }
  }
}
"""

_COMMENTS_QUERY = """
query NewComments($first: Int!) {
  comments(first: $first, orderBy: createdAt) {
    nodes {
      id body createdAt updatedAt url
      user { id name email }
      issue { id identifier title url }
    }
  }
}
"""


def _flatten_issue(item):
    state = item.get("state") or {}
    assignee = item.get("assignee") or {}
    team = item.get("team") or {}
    return {
        "id": item.get("id"),
        "identifier": item.get("identifier"),
        "title": item.get("title"),
        "url": item.get("url"),
        "priority": item.get("priority"),
        "createdAt": item.get("createdAt"),
        "updatedAt": item.get("updatedAt"),
        "state_name": state.get("name"),
        "state_type": state.get("type"),
        "assignee_name": assignee.get("name"),
        "assignee_email": assignee.get("email"),
        "team_key": team.get("key"),
    }


def _flatten_comment(item):
    user = item.get("user") or {}
    issue = item.get("issue") or {}
    return {
        "id": item.get("id"),
        "body": item.get("body"),
        "createdAt": item.get("createdAt"),
        "url": item.get("url"),
        "user_name": user.get("name"),
        "user_email": user.get("email"),
        "issue_id": issue.get("id"),
        "issue_identifier": issue.get("identifier"),
        "issue_title": issue.get("title"),
    }


register_flatten("linear.issue", _flatten_issue)
register_flatten("linear.comment", _flatten_comment)


async def _walk_linear(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """One GraphQL POST per poll — Linear's connection type gives us
    a bounded window with the same freshness ordering as timeline
    scrolling."""
    headers = {
        "Authorization": token or "",
        "Content-Type": "application/json",
        "Accept": "application/json",
    }
    max_per = getattr(props, "max_per_poll", 25) or 25
    try:
        first = max(1, min(int(max_per), 50))
    except (TypeError, ValueError):
        first = 25

    if event.id == "new_comment":
        query = _COMMENTS_QUERY
        variables: dict[str, Any] = {"first": first}
        pick = "comments"
    else:
        team_id = getattr(props, "team_id", None) or None
        filter_ = {"team": {"id": {"eq": team_id}}} if team_id else None
        query = _ISSUES_QUERY_UPDATED if event.id == "updated_issue" else _ISSUES_QUERY_NEW
        variables = {"first": first, "filter": filter_}
        pick = "issues"

    resp = await client.post(
        _LINEAR_API,
        headers=headers,
        json={"query": query, "variables": variables},
        timeout=30,
    )
    resp.raise_for_status()
    payload = resp.json() or {}
    if payload.get("errors"):
        raise RuntimeError(payload["errors"][0].get("message") or "Linear GraphQL error")
    data = payload.get("data") or {}
    nodes = (data.get(pick) or {}).get("nodes")
    return nodes if isinstance(nodes, list) else []


MANIFEST = PollingTriggerManifest(
    type="trigger.linear",
    name="Linear",
    description="Poll Linear for new / updated issues or new comments.",
    icon_slug="linear",
    color="#1c1c1c",
    base_url="https://api.linear.app",
    credential_type="linear_api_key",
    token_field=["api_key"],
    auth="header_token",
    provider="linear",
    default_poll_interval_seconds=60,
    common_fields=[
        FieldSpec(
            name="team_id",
            label="Team ID (optional; blank = all teams)",
            type="string",
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_issue",
            label="New Issue",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="linear.issue",
        ),
        PollingEvent(
            id="updated_issue",
            label="Issue Updated",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updatedAt",
            flatten="linear.issue",
        ),
        PollingEvent(
            id="new_comment",
            label="New Comment",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="linear.comment",
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "identifier", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "createdAt", "type": "string"},
        {"label": "updatedAt", "type": "string"},
    ],
    paginate_fn=_walk_linear,
)
