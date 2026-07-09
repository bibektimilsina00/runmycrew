"""Asana action node — manifest form.

Asana REST API at `https://app.asana.com/api/1.0`. Bearer auth via
the new asana_oauth credential. Workspaces, projects, tasks, sections,
and team metadata.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.asana import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.asana",
    name=NAME,
    category="integration",
    description="Asana — projects, tasks, sections, teams.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://app.asana.com/api/1.0",
    credential_type="asana_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="workspace_id",
            label="Workspace",
            type="string",
            remote=RemoteLookup(provider="asana", resource="workspaces"),
        ),
        FieldSpec(
            name="project_id",
            label="Project",
            type="string",
            remote=RemoteLookup(
                provider="asana",
                resource="projects",
                params={"workspace_id": "${workspace_id}"},
                depends_on=["workspace_id"],
            ),
        ),
        FieldSpec(name="task_id", label="Task ID", type="string"),
        FieldSpec(name="section_id", label="Section ID", type="string", mode="advanced"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="notes", label="Notes", type="string", mode="advanced"),
        FieldSpec(
            name="assignee", label="Assignee (user ID or email)", type="string", mode="advanced"
        ),
        FieldSpec(name="due_on", label="Due date (YYYY-MM-DD)", type="string", mode="advanced"),
        FieldSpec(name="completed", label="Completed", type="boolean", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=50, mode="advanced"),
        FieldSpec(name="comment_text", label="Comment", type="string"),
    ],
    operations=[
        OpSpec(id="list_workspaces", label="List Workspaces", method="GET", path="/workspaces"),
        OpSpec(
            id="list_projects",
            label="List Projects",
            method="GET",
            path="/projects",
            visible_fields=["workspace_id", "limit"],
            query_builder=lambda v: {
                k: val
                for k, val in {
                    "workspace": getattr(v, "workspace_id", None),
                    "limit": int(getattr(v, "limit", 50) or 50),
                }.items()
                if val
            },
        ),
        OpSpec(
            id="get_project",
            label="Get Project",
            method="GET",
            path="/projects/{project_id}",
            visible_fields=["project_id"],
        ),
        OpSpec(
            id="list_tasks",
            label="List Tasks in Project",
            method="GET",
            path="/projects/{project_id}/tasks",
            visible_fields=["project_id", "limit"],
            query_builder=lambda v: {"limit": int(getattr(v, "limit", 50) or 50)},
        ),
        OpSpec(
            id="get_task",
            label="Get Task",
            method="GET",
            path="/tasks/{task_id}",
            visible_fields=["task_id"],
        ),
        OpSpec(
            id="create_task",
            label="Create Task",
            method="POST",
            path="/tasks",
            visible_fields=["project_id", "name", "notes", "assignee", "due_on"],
            body_builder=lambda v: {
                "data": {
                    k: val
                    for k, val in {
                        "name": getattr(v, "name", None) or "",
                        "notes": getattr(v, "notes", None),
                        "assignee": getattr(v, "assignee", None),
                        "due_on": getattr(v, "due_on", None),
                        "projects": [getattr(v, "project_id", None)]
                        if getattr(v, "project_id", None)
                        else None,
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="update_task",
            label="Update Task",
            method="PUT",
            path="/tasks/{task_id}",
            visible_fields=["task_id", "name", "notes", "assignee", "due_on", "completed"],
            body_builder=lambda v: {
                "data": {
                    k: val
                    for k, val in {
                        "name": getattr(v, "name", None),
                        "notes": getattr(v, "notes", None),
                        "assignee": getattr(v, "assignee", None),
                        "due_on": getattr(v, "due_on", None),
                        "completed": getattr(v, "completed", None),
                    }.items()
                    if val is not None
                }
            },
        ),
        OpSpec(
            id="delete_task",
            label="Delete Task",
            method="DELETE",
            path="/tasks/{task_id}",
            visible_fields=["task_id"],
            success_payload_template={"deleted": True, "id": "{task_id}"},
        ),
        OpSpec(
            id="add_comment",
            label="Add Comment",
            method="POST",
            path="/tasks/{task_id}/stories",
            visible_fields=["task_id", "comment_text"],
            body_builder=lambda v: {"data": {"text": getattr(v, "comment_text", None) or ""}},
        ),
        OpSpec(
            id="list_sections",
            label="List Sections",
            method="GET",
            path="/projects/{project_id}/sections",
            visible_fields=["project_id"],
        ),
        OpSpec(
            id="get_me",
            label="Get Authenticated User",
            method="GET",
            path="/users/me",
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "gid", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "next_page", "type": "object"},
    ],
    allow_error=True,
)
