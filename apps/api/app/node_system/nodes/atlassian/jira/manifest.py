"""Jira action node — manifest form.

Jira Cloud REST API v3 at `{domain}/rest/api/3` where `{domain}` is
the Atlassian tenant (`mycompany.atlassian.net`). Basic auth: email as
username + API token as password — the scaffold's `basic` scheme with
`auth_basic_username="{email}"` reads the email from the credential
and puts the token on the password side.

"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.jira",
    name="Jira",
    category="integration",
    description="Jira — issues, projects, comments, transitions, worklogs, sprints.",
    icon_slug="jira",
    color="#ffffff",
    base_url="https://{domain}/rest/api/3",
    credential_type="jira_api_key",
    token_field=["api_key"],
    auth="basic",
    auth_basic_username="{email}",
    fields=[
        FieldSpec(name="issue_key", label="Issue Key", type="string", placeholder="PROJ-123"),
        FieldSpec(
            name="project_key",
            label="Project",
            type="string",
            remote=RemoteLookup(provider="jira", resource="projects"),
        ),
        FieldSpec(
            name="project_id",
            label="Project",
            type="string",
            remote=RemoteLookup(provider="jira", resource="projects"),
        ),
        FieldSpec(name="summary", label="Summary", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(
            name="issue_type",
            label="Issue Type",
            type="string",
            default="Task",
            remote=RemoteLookup(
                provider="jira",
                resource="issue_types",
                params={"project": "${project_key}"},
                depends_on=["project_key"],
            ),
        ),
        FieldSpec(name="priority", label="Priority", type="string"),
        FieldSpec(name="assignee_id", label="Assignee Account ID", type="string"),
        FieldSpec(name="reporter_id", label="Reporter Account ID", type="string"),
        FieldSpec(name="labels", label="Labels (JSON array)", type="json", default=[]),
        FieldSpec(name="components", label="Components (JSON array)", type="json", default=[]),
        FieldSpec(name="jql", label="JQL", type="string"),
        FieldSpec(name="fields", label="Fields (comma-separated)", type="string"),
        FieldSpec(
            name="max_results", label="Max Results", type="number", default=50, mode="advanced"
        ),
        FieldSpec(name="start_at", label="Start At", type="number", default=0, mode="advanced"),
        FieldSpec(name="comment_body", label="Comment Body", type="string"),
        FieldSpec(name="comment_id", label="Comment ID", type="string"),
        FieldSpec(name="transition_id", label="Transition ID", type="string"),
        FieldSpec(
            name="worklog_time_spent", label="Worklog Time Spent (e.g. 1h 30m)", type="string"
        ),
        FieldSpec(name="worklog_comment", label="Worklog Comment", type="string"),
        FieldSpec(name="worklog_id", label="Worklog ID", type="string"),
        FieldSpec(name="version_name", label="Version Name", type="string"),
        FieldSpec(name="version_id", label="Version ID", type="string"),
        FieldSpec(name="version_released", label="Version Released", type="boolean", default=False),
        FieldSpec(name="attachment_url", label="Attachment URL", type="string"),
        FieldSpec(name="board_id", label="Board ID", type="string"),
        FieldSpec(name="sprint_id", label="Sprint ID", type="string"),
        FieldSpec(name="sprint_name", label="Sprint Name", type="string"),
        FieldSpec(name="watcher_account_id", label="Watcher Account ID", type="string"),
    ],
    operations=[
        OpSpec(
            id="create_issue",
            label="Create Issue",
            method="POST",
            path="/issue",
            visible_fields=[
                "project_key",
                "summary",
                "description",
                "issue_type",
                "priority",
                "assignee_id",
                "labels",
            ],
            body_builder=lambda v: {
                "fields": {
                    k: val
                    for k, val in {
                        "project": {"key": getattr(v, "project_key", "") or ""},
                        "summary": getattr(v, "summary", "") or "",
                        "description": getattr(v, "description", None) or None,
                        "issuetype": {"name": getattr(v, "issue_type", None) or "Task"},
                        "priority": {"name": getattr(v, "priority", None)}
                        if getattr(v, "priority", None)
                        else None,
                        "assignee": {"accountId": getattr(v, "assignee_id", None)}
                        if getattr(v, "assignee_id", None)
                        else None,
                        "labels": getattr(v, "labels", None) or None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="get_issue",
            label="Get Issue",
            method="GET",
            path="/issue/{issue_key}",
            visible_fields=["issue_key", "fields"],
            query_builder=lambda v: {"fields": getattr(v, "fields", None) or None},
        ),
        OpSpec(
            id="update_issue",
            label="Update Issue",
            method="PUT",
            path="/issue/{issue_key}",
            visible_fields=["issue_key", "summary", "description", "priority"],
            body_builder=lambda v: {
                "fields": {
                    k: val
                    for k, val in {
                        "summary": getattr(v, "summary", None) or None,
                        "description": getattr(v, "description", None) or None,
                        "priority": {"name": getattr(v, "priority", None)}
                        if getattr(v, "priority", None)
                        else None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="search_issues",
            label="Search Issues (JQL)",
            method="POST",
            path="/search",
            visible_fields=["jql", "max_results", "start_at", "fields"],
            body_builder=lambda v: {
                "jql": getattr(v, "jql", "") or "",
                "maxResults": int(getattr(v, "max_results", 50) or 50),
                "startAt": int(getattr(v, "start_at", 0) or 0),
                "fields": (getattr(v, "fields", None) or "").split(",")
                if getattr(v, "fields", None)
                else None,
            },
        ),
        OpSpec(
            id="add_comment",
            label="Add Comment",
            method="POST",
            path="/issue/{issue_key}/comment",
            visible_fields=["issue_key", "comment_body"],
            body_builder=lambda v: {"body": getattr(v, "comment_body", "") or ""},
        ),
        OpSpec(
            id="transition_issue",
            label="Transition Issue",
            method="POST",
            path="/issue/{issue_key}/transitions",
            visible_fields=["issue_key", "transition_id"],
            body_builder=lambda v: {"transition": {"id": getattr(v, "transition_id", "") or ""}},
        ),
        OpSpec(
            id="list_transitions",
            label="List Available Transitions",
            method="GET",
            path="/issue/{issue_key}/transitions",
            visible_fields=["issue_key"],
        ),
        # ─── issue depth ───────────────────────────────────────────
        OpSpec(
            id="delete_issue",
            label="Delete Issue",
            method="DELETE",
            path="/issue/{issue_key}",
            visible_fields=["issue_key"],
        ),
        OpSpec(
            id="assign_issue",
            label="Assign Issue",
            method="PUT",
            path="/issue/{issue_key}/assignee",
            visible_fields=["issue_key", "assignee_id"],
            body_builder=lambda v: {"accountId": getattr(v, "assignee_id", "") or ""},
        ),
        OpSpec(
            id="add_watcher",
            label="Add Watcher",
            method="POST",
            path="/issue/{issue_key}/watchers",
            visible_fields=["issue_key", "watcher_account_id"],
            body_builder=lambda v: getattr(v, "watcher_account_id", "") or "",
        ),
        OpSpec(
            id="list_watchers",
            label="List Watchers",
            method="GET",
            path="/issue/{issue_key}/watchers",
            visible_fields=["issue_key"],
        ),
        # ─── comments depth ────────────────────────────────────────
        OpSpec(
            id="list_comments",
            label="List Comments",
            method="GET",
            path="/issue/{issue_key}/comment",
            visible_fields=["issue_key"],
        ),
        OpSpec(
            id="get_comment",
            label="Get Comment",
            method="GET",
            path="/issue/{issue_key}/comment/{comment_id}",
            visible_fields=["issue_key", "comment_id"],
        ),
        OpSpec(
            id="update_comment",
            label="Update Comment",
            method="PUT",
            path="/issue/{issue_key}/comment/{comment_id}",
            visible_fields=["issue_key", "comment_id", "comment_body"],
            body_builder=lambda v: {"body": getattr(v, "comment_body", "") or ""},
        ),
        OpSpec(
            id="delete_comment",
            label="Delete Comment",
            method="DELETE",
            path="/issue/{issue_key}/comment/{comment_id}",
            visible_fields=["issue_key", "comment_id"],
        ),
        # ─── worklog ───────────────────────────────────────────────
        OpSpec(
            id="add_worklog",
            label="Add Worklog",
            method="POST",
            path="/issue/{issue_key}/worklog",
            visible_fields=["issue_key", "worklog_time_spent", "worklog_comment"],
            body_builder=lambda v: {
                "timeSpent": getattr(v, "worklog_time_spent", "") or "",
                "comment": getattr(v, "worklog_comment", None) or None,
            },
        ),
        OpSpec(
            id="list_worklogs",
            label="List Worklogs",
            method="GET",
            path="/issue/{issue_key}/worklog",
            visible_fields=["issue_key"],
        ),
        OpSpec(
            id="delete_worklog",
            label="Delete Worklog",
            method="DELETE",
            path="/issue/{issue_key}/worklog/{worklog_id}",
            visible_fields=["issue_key", "worklog_id"],
        ),
        # ─── projects + versions ───────────────────────────────────
        OpSpec(
            id="list_projects",
            label="List Projects",
            method="GET",
            path="/project",
        ),
        OpSpec(
            id="get_project",
            label="Get Project",
            method="GET",
            path="/project/{project_key}",
            visible_fields=["project_key"],
        ),
        OpSpec(
            id="list_project_versions",
            label="List Project Versions",
            method="GET",
            path="/project/{project_key}/versions",
            visible_fields=["project_key"],
        ),
        OpSpec(
            id="create_version",
            label="Create Version",
            method="POST",
            path="/version",
            visible_fields=["project_id", "version_name", "version_released"],
            body_builder=lambda v: {
                "projectId": getattr(v, "project_id", "") or "",
                "name": getattr(v, "version_name", "") or "",
                "released": bool(getattr(v, "version_released", False)),
            },
        ),
        OpSpec(
            id="update_version",
            label="Update Version",
            method="PUT",
            path="/version/{version_id}",
            visible_fields=["version_id", "version_name", "version_released"],
            body_builder=lambda v: {
                "name": getattr(v, "version_name", None) or None,
                "released": bool(getattr(v, "version_released", False)),
            },
        ),
        # ─── users + boards + sprints ──────────────────────────────
        OpSpec(
            id="get_current_user",
            label="Get Current User",
            method="GET",
            path="/myself",
        ),
        OpSpec(
            id="search_users",
            label="Search Users",
            method="GET",
            path="/user/search",
            visible_fields=["summary"],
            query_builder=lambda v: {"query": getattr(v, "summary", "") or ""},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "key", "type": "string"},
    ],
    allow_error=True,
)
