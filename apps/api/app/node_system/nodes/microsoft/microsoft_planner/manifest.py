"""Microsoft Planner action node — manifest form.

Graph endpoints at `/v1.0/planner/...`. Bearer auth via the shared
microsoft_oauth credential (Tasks.ReadWrite scope). Plans, buckets,
tasks lifecycle.

Planner's task update endpoints require an `If-Match: <etag>` header
matching the resource's ETag — the manifest exposes an `etag` field
that the user pastes from a prior `get_task` / `get_plan` response.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
    RemoteLookup,
)

MANIFEST = ProviderManifest(
    type="action.microsoft_planner",
    name="Microsoft Planner",
    category="integration",
    description="Microsoft Planner — plans, buckets, tasks.",
    icon_slug="microsoft-planner",
    color="#ffffff",
    base_url="https://graph.microsoft.com/v1.0",
    credential_type="microsoft_oauth",
    token_field=["access_token"],
    auth="bearer",
    fields=[
        FieldSpec(
            name="group_id",
            label="Team",
            type="string",
            remote=RemoteLookup(provider="microsoft", resource="teams"),
        ),
        FieldSpec(
            name="plan_id",
            label="Plan",
            type="string",
            remote=RemoteLookup(
                provider="microsoft",
                resource="planner_plans",
                params={"group_id": "${group_id}"},
                depends_on=["group_id"],
            ),
        ),
        FieldSpec(name="bucket_id", label="Bucket ID", type="string"),
        FieldSpec(name="task_id", label="Task ID", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="etag", label="ETag (@odata.etag)", type="string", mode="advanced"),
        FieldSpec(
            name="percent_complete",
            label="Percent Complete (0-100)",
            type="number",
            mode="advanced",
        ),
        FieldSpec(name="due_date", label="Due date (ISO)", type="string", mode="advanced"),
        FieldSpec(
            name="assignees",
            label="Assignees (JSON object userId→role)",
            type="json",
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="list_plans",
            label="List Plans (by Group)",
            method="GET",
            path="/groups/{group_id}/planner/plans",
            visible_fields=["group_id"],
        ),
        OpSpec(
            id="get_plan",
            label="Get Plan",
            method="GET",
            path="/planner/plans/{plan_id}",
            visible_fields=["plan_id"],
        ),
        OpSpec(
            id="create_plan",
            label="Create Plan",
            method="POST",
            path="/planner/plans",
            visible_fields=["group_id", "title"],
            body_builder=lambda v: {
                "owner": getattr(v, "group_id", None) or "",
                "title": getattr(v, "title", None) or "",
            },
        ),
        OpSpec(
            id="list_buckets",
            label="List Buckets",
            method="GET",
            path="/planner/plans/{plan_id}/buckets",
            visible_fields=["plan_id"],
        ),
        OpSpec(
            id="create_bucket",
            label="Create Bucket",
            method="POST",
            path="/planner/buckets",
            visible_fields=["plan_id", "title"],
            body_builder=lambda v: {
                "name": getattr(v, "title", None) or "",
                "planId": getattr(v, "plan_id", None) or "",
                "orderHint": " !",
            },
        ),
        OpSpec(
            id="list_tasks",
            label="List Tasks",
            method="GET",
            path="/planner/plans/{plan_id}/tasks",
            visible_fields=["plan_id"],
        ),
        OpSpec(
            id="get_task",
            label="Get Task",
            method="GET",
            path="/planner/tasks/{task_id}",
            visible_fields=["task_id"],
        ),
        OpSpec(
            id="create_task",
            label="Create Task",
            method="POST",
            path="/planner/tasks",
            visible_fields=["plan_id", "bucket_id", "title", "due_date", "assignees"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "planId": getattr(v, "plan_id", None),
                    "bucketId": getattr(v, "bucket_id", None),
                    "title": getattr(v, "title", None) or "",
                    "dueDateTime": getattr(v, "due_date", None),
                    "assignments": getattr(v, "assignees", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="update_task",
            label="Update Task (If-Match required)",
            method="PATCH",
            path="/planner/tasks/{task_id}",
            visible_fields=["task_id", "etag", "title", "percent_complete", "due_date"],
            extra_headers={"If-Match": "{etag}"},
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "title": getattr(v, "title", None),
                    "percentComplete": (
                        int(v.percent_complete)
                        if getattr(v, "percent_complete", None) is not None
                        else None
                    ),
                    "dueDateTime": getattr(v, "due_date", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="delete_task",
            label="Delete Task (If-Match required)",
            method="DELETE",
            path="/planner/tasks/{task_id}",
            visible_fields=["task_id", "etag"],
            extra_headers={"If-Match": "{etag}"},
            success_payload_template={"deleted": True, "task_id": "{task_id}"},
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "title", "type": "string"},
        {"label": "@odata.etag", "type": "string"},
        {"label": "value", "type": "array"},
        {"label": "planId", "type": "string"},
        {"label": "bucketId", "type": "string"},
    ],
    allow_error=True,
)
