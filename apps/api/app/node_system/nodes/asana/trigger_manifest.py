"""Asana polling trigger — manifest form.

Watches tasks in a project. Asana's `/tasks?project=X&modified_since=Y`
returns tasks modified after Y — perfect for `since_timestamp`
diffing. `/tasks?project=X` alone returns all with a stable ordering
for `known_ids` diffing.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.asana import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    PollingEvent,
    PollingTriggerManifest,
    register_flatten,
)


def _flatten_task(item):
    return {
        "gid": item.get("gid"),
        "name": item.get("name"),
        "notes": item.get("notes"),
        "completed": item.get("completed"),
        "due_on": item.get("due_on"),
        "assignee": (item.get("assignee") or {}).get("name") if item.get("assignee") else None,
        "modified_at": item.get("modified_at"),
        "created_at": item.get("created_at"),
        "permalink_url": item.get("permalink_url"),
    }


register_flatten("asana.task", _flatten_task)


MANIFEST = PollingTriggerManifest(
    type="trigger.asana",
    name=NAME,
    description="Poll Asana for new / recently-modified tasks in a project.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://app.asana.com/api/1.0",
    credential_type="asana_oauth",
    token_field=["access_token"],
    auth="bearer",
    provider="asana",
    default_poll_interval_seconds=90,
    common_fields=[
        FieldSpec(
            name="project_id",
            label="Project ID",
            type="string",
            required=True,
        ),
        FieldSpec(
            name="limit",
            label="Limit",
            type="number",
            default=50,
            mode="advanced",
        ),
    ],
    events=[
        PollingEvent(
            id="new_task",
            label="New Task",
            list_path="/tasks",
            list_params={
                "project": "{project_id}",
                "limit": "{limit}",
                "opt_fields": "name,notes,completed,due_on,assignee.name,modified_at,created_at,permalink_url",
            },
            strategy="known_ids",
            id_field="gid",
            flatten="asana.task",
        ),
        PollingEvent(
            id="task_modified",
            label="Task Modified",
            list_path="/tasks",
            list_params={
                "project": "{project_id}",
                "limit": "{limit}",
                "opt_fields": "name,notes,completed,due_on,assignee.name,modified_at,created_at,permalink_url",
            },
            strategy="since_timestamp",
            timestamp_field="modified_at",
            flatten="asana.task",
        ),
    ],
    outputs_schema=[
        {"label": "gid", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "completed", "type": "boolean"},
        {"label": "due_on", "type": "string"},
        {"label": "assignee", "type": "string"},
        {"label": "modified_at", "type": "string"},
    ],
)
