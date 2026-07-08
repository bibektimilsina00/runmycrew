"""Jira polling trigger — manifest form.

Jira Cloud REST v3 at `{base_url}/rest/api/3` + agile at
`{base_url}/rest/agile/1.0`. Basic auth using `{email}:{api_key}`.

Events (poll-observable subset of sim's 14):
  - `new_issue`         — known_ids on issue id (JQL-filtered)
  - `issue_updated`     — since_timestamp on updated field
  - `new_comment`       — comment adds on a specific issue
  - `new_worklog`       — worklog adds on a specific issue
  - `new_sprint`        — known_ids on sprint id (board-scoped)
  - `sprint_started`    — since_timestamp on startDate
  - `sprint_closed`     — since_timestamp on completeDate
  - `new_project`       — known_ids on project id (workspace-wide)

Not in polling (need webhook — see follow-up):
  issue_deleted, comment_deleted, comment_updated, worklog_deleted,
  worklog_updated, version_released.

For `issue_updated`, `sprint_started`, `sprint_closed`: the scaffold's
`diff_since_timestamp` reads `item[timestamp_field]` on the raw item.
Jira issue timestamps live at `fields.updated`; we hoist them to the
top level in the paginate_fn so the diff can read them without a
custom handler.
"""

from __future__ import annotations

from typing import Any

import httpx

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    build_auth,
    register_flatten,
)
from apps.api.app.node_system.scaffolds.field_resolvers import resolve_template


def _flatten_issue(item):
    fields = item.get("fields") or {}
    return {
        "key": item.get("key"),
        "id": item.get("id"),
        "summary": fields.get("summary"),
        "status": (fields.get("status") or {}).get("name"),
        "priority": (fields.get("priority") or {}).get("name"),
        "assignee": (fields.get("assignee") or {}).get("displayName"),
        "reporter": (fields.get("reporter") or {}).get("displayName"),
        "created": fields.get("created"),
        "updated": fields.get("updated"),
        "url": item.get("self"),
    }


def _flatten_comment(item):
    author = item.get("author") or {}
    return {
        "id": item.get("id"),
        "body": item.get("body"),
        "author_name": author.get("displayName"),
        "author_email": author.get("emailAddress"),
        "created": item.get("created"),
        "updated": item.get("updated"),
        "issue_key": item.get("_issue_key"),  # hoisted by paginate_fn
    }


def _flatten_worklog(item):
    author = item.get("author") or {}
    return {
        "id": item.get("id"),
        "comment": item.get("comment"),
        "time_spent": item.get("timeSpent"),
        "time_spent_seconds": item.get("timeSpentSeconds"),
        "author_name": author.get("displayName"),
        "started": item.get("started"),
        "created": item.get("created"),
        "updated": item.get("updated"),
        "issue_key": item.get("_issue_key"),
    }


def _flatten_sprint(item):
    return {
        "id": item.get("id"),
        "name": item.get("name"),
        "state": item.get("state"),
        "start_date": item.get("startDate"),
        "end_date": item.get("endDate"),
        "complete_date": item.get("completeDate"),
        "goal": item.get("goal"),
        "board_id": item.get("originBoardId"),
    }


def _flatten_project(item):
    return {
        "id": item.get("id"),
        "key": item.get("key"),
        "name": item.get("name"),
        "project_type": item.get("projectTypeKey"),
        "lead": (item.get("lead") or {}).get("displayName"),
        "url": item.get("self"),
    }


register_flatten("jira.issue", _flatten_issue)
register_flatten("jira.comment", _flatten_comment)
register_flatten("jira.worklog", _flatten_worklog)
register_flatten("jira.sprint", _flatten_sprint)
register_flatten("jira.project", _flatten_project)


async def _jira_get(
    client: httpx.AsyncClient,
    *,
    url: str,
    token: str | None,
    email: str,
    params: dict[str, Any] | None = None,
) -> Any:
    """Common Basic-auth GET helper used by every event's paginator."""
    auth_headers, _ = build_auth(
        token=token,
        scheme="basic",
        header_name="Authorization",
        value_template="",
        query_param="",
        basic_username=email,
    )
    headers = {**auth_headers, "Accept": "application/json"}
    resp = await client.get(url, headers=headers, params=params or None, timeout=30)
    resp.raise_for_status()
    return resp.json() or {}


async def _walk_jira(
    client: httpx.AsyncClient,
    *,
    manifest,
    event,
    token: str | None,
    props: Any,
) -> list[dict[str, Any]]:
    """Route by event id — each Jira endpoint has its own shape.

    For `issue_updated`, hoist `fields.updated` to `updated` on each
    item so the scaffold's `since_timestamp` diff sees it. Same for
    sprint start/complete date events.
    """
    cred = getattr(props, "_cred", None) or {}
    base_url = (cred.get("base_url") or "").rstrip("/")
    email = str(cred.get("email") or "")

    if event.id in ("new_issue", "issue_updated"):
        url = f"{base_url}/rest/api/3/search"
        params: dict[str, Any] = {
            "jql": resolve_template(event.list_params.get("jql") or "", props),
            "maxResults": resolve_template(event.list_params.get("maxResults") or "50", props),
        }
        if "expand" in event.list_params:
            params["expand"] = event.list_params["expand"]
        body = await _jira_get(client, url=url, token=token, email=email, params=params)
        issues = body.get("issues") or []
        # Hoist fields.updated → updated so since_timestamp can diff.
        for issue in issues:
            fields = issue.get("fields") or {}
            if "updated" in fields:
                issue["updated"] = fields["updated"]
        return issues

    if event.id == "new_comment":
        issue_key = resolve_template("{issue_key}", props) or ""
        if not issue_key:
            return []
        url = f"{base_url}/rest/api/3/issue/{issue_key}/comment"
        body = await _jira_get(client, url=url, token=token, email=email)
        comments = body.get("comments") or []
        for c in comments:
            c["_issue_key"] = issue_key
        return comments

    if event.id == "new_worklog":
        issue_key = resolve_template("{issue_key}", props) or ""
        if not issue_key:
            return []
        url = f"{base_url}/rest/api/3/issue/{issue_key}/worklog"
        body = await _jira_get(client, url=url, token=token, email=email)
        worklogs = body.get("worklogs") or []
        for w in worklogs:
            w["_issue_key"] = issue_key
        return worklogs

    if event.id in ("new_sprint", "sprint_started", "sprint_closed"):
        board_id = resolve_template("{board_id}", props) or ""
        if not board_id:
            return []
        state_filter = {
            "new_sprint": None,
            "sprint_started": "active",
            "sprint_closed": "closed",
        }[event.id]
        url = f"{base_url}/rest/agile/1.0/board/{board_id}/sprint"
        params = {}
        if state_filter:
            params["state"] = state_filter
        body = await _jira_get(client, url=url, token=token, email=email, params=params or None)
        sprints = body.get("values") or []
        # Hoist the right timestamp field per event so since_timestamp
        # can diff without a custom handler.
        for s in sprints:
            if event.id == "sprint_started":
                s["updated"] = s.get("startDate") or ""
            elif event.id == "sprint_closed":
                s["updated"] = s.get("completeDate") or ""
        return sprints

    if event.id == "new_project":
        url = f"{base_url}/rest/api/3/project/search"
        params = {"orderBy": "-lastIssueUpdatedTime"}
        body = await _jira_get(client, url=url, token=token, email=email, params=params)
        return body.get("values") or []

    return []


MANIFEST = PollingTriggerManifest(
    type="trigger.jira",
    name="Jira",
    description=(
        "Poll Jira for new issues, updates, comments, worklogs, sprints, "
        "or projects. Basic auth via email + API token."
    ),
    icon_slug="jira",
    color="#ffffff",
    base_url="",
    credential_type="jira_api_key",
    token_field=["api_key"],
    auth="basic",
    provider="jira",
    default_poll_interval_seconds=90,
    common_fields=[
        FieldSpec(
            name="jql",
            label="JQL (for issue events)",
            type="string",
            placeholder='project = "ABC" AND status = "To Do"',
        ),
        FieldSpec(
            name="max_results",
            label="Max Results",
            type="number",
            default=50,
            mode="advanced",
        ),
        FieldSpec(
            name="issue_key",
            label="Issue Key (for comment/worklog events)",
            type="string",
            placeholder="ABC-123",
        ),
        FieldSpec(
            name="board_id",
            label="Board ID (for sprint events)",
            type="string",
            placeholder="12",
        ),
    ],
    events=[
        PollingEvent(
            id="new_issue",
            label="New Issue Matching JQL",
            list_path="",
            list_params={"jql": "{jql}", "maxResults": "{max_results}"},
            strategy="known_ids",
            id_field="id",
            flatten="jira.issue",
            extra_fields=["jql", "max_results"],
        ),
        PollingEvent(
            id="issue_updated",
            label="Issue Updated",
            list_path="",
            list_params={
                "jql": "{jql} ORDER BY updated DESC",
                "maxResults": "{max_results}",
                "expand": "changelog",
            },
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="jira.issue",
            extra_fields=["jql", "max_results"],
        ),
        PollingEvent(
            id="new_comment",
            label="New Comment on Issue",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="jira.comment",
            extra_fields=["issue_key"],
        ),
        PollingEvent(
            id="new_worklog",
            label="New Worklog on Issue",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="jira.worklog",
            extra_fields=["issue_key"],
        ),
        PollingEvent(
            id="new_sprint",
            label="New Sprint on Board",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="jira.sprint",
            extra_fields=["board_id"],
        ),
        PollingEvent(
            id="sprint_started",
            label="Sprint Started",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="jira.sprint",
            extra_fields=["board_id"],
        ),
        PollingEvent(
            id="sprint_closed",
            label="Sprint Closed",
            list_path="",
            strategy="since_timestamp",
            timestamp_field="updated",
            flatten="jira.sprint",
            extra_fields=["board_id"],
        ),
        PollingEvent(
            id="new_project",
            label="New Project",
            list_path="",
            strategy="known_ids",
            id_field="id",
            flatten="jira.project",
        ),
    ],
    outputs_schema=[
        {"label": "key", "type": "string"},
        {"label": "id", "type": "string"},
        {"label": "summary", "type": "string"},
        {"label": "status", "type": "string"},
        {"label": "updated", "type": "string"},
        {"label": "body", "type": "string"},
        {"label": "issue_key", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "state", "type": "string"},
    ],
    paginate_fn=_walk_jira,
)
