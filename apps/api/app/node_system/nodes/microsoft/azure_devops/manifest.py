"""Azure DevOps action node — manifest form.

Azure DevOps REST API 7.1 at
`https://dev.azure.com/{organization}/{project}/_apis`. Uses Basic
auth with an empty username + Personal Access Token as password —
the scaffold's `basic_token_only` scheme handles this exactly.

New action node — trigger + webhook already existed under
`trigger.azure_devops_webhook` but no action node was shipped.
"""

from __future__ import annotations

from apps.api.app.node_system.nodes.microsoft.azure_devops import COLOR, ICON_SLUG, NAME
from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.azure_devops",
    name=NAME,
    category="integration",
    description="Azure DevOps — pipelines, builds, work items, comments.",
    icon_slug=ICON_SLUG,
    color=COLOR,
    base_url="https://dev.azure.com/{organization}/{project}/_apis",
    credential_type="azure_devops_api_key",
    token_field=["api_key"],
    auth="basic_token_only",
    fields=[
        FieldSpec(name="pipeline_id", label="Pipeline ID", type="number"),
        FieldSpec(name="run_id", label="Pipeline Run ID", type="number"),
        FieldSpec(name="build_id", label="Build ID", type="number"),
        FieldSpec(name="log_id", label="Log ID", type="number"),
        FieldSpec(name="from_build_id", label="From Build ID", type="number"),
        FieldSpec(name="to_build_id", label="To Build ID", type="number"),
        FieldSpec(name="wiql_query", label="Work Item WIQL Query", type="string"),
        FieldSpec(name="work_item_id", label="Work Item ID", type="number"),
        FieldSpec(
            name="work_item_ids", label="Work Item IDs (JSON array)", type="json", default=[]
        ),
        FieldSpec(name="work_item_type", label="Work Item Type", type="string", default="Task"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="description", label="Description", type="string"),
        FieldSpec(name="assigned_to", label="Assigned To (email)", type="string"),
        FieldSpec(name="state", label="State", type="string"),
        FieldSpec(name="patch_body", label="Patch Body (JSON array)", type="json", default=[]),
        FieldSpec(name="comment_text", label="Comment Text", type="string"),
        FieldSpec(name="fields_expand", label="Fields to Expand", type="string", default="all"),
    ],
    operations=[
        OpSpec(
            id="list_pipelines",
            label="List Pipelines",
            method="GET",
            path="/pipelines?api-version=7.1",
            visible_fields=[],
        ),
        OpSpec(
            id="get_pipeline",
            label="Get Pipeline",
            method="GET",
            path="/pipelines/{pipeline_id}?api-version=7.1",
            visible_fields=["pipeline_id"],
        ),
        OpSpec(
            id="list_pipeline_runs",
            label="List Pipeline Runs",
            method="GET",
            path="/pipelines/{pipeline_id}/runs?api-version=7.1",
            visible_fields=["pipeline_id"],
        ),
        OpSpec(
            id="get_pipeline_run",
            label="Get Pipeline Run",
            method="GET",
            path="/pipelines/{pipeline_id}/runs/{run_id}?api-version=7.1",
            visible_fields=["pipeline_id", "run_id"],
        ),
        OpSpec(
            id="list_builds",
            label="List Builds",
            method="GET",
            path="/build/builds?api-version=7.1",
            visible_fields=[],
        ),
        OpSpec(
            id="list_build_logs",
            label="List Build Logs",
            method="GET",
            path="/build/builds/{build_id}/logs?api-version=7.1",
            visible_fields=["build_id"],
        ),
        OpSpec(
            id="get_build_log",
            label="Get Build Log",
            method="GET",
            path="/build/builds/{build_id}/logs/{log_id}?api-version=7.1",
            visible_fields=["build_id", "log_id"],
        ),
        OpSpec(
            id="get_build_timeline",
            label="Get Build Timeline",
            method="GET",
            path="/build/builds/{build_id}/timeline?api-version=7.1",
            visible_fields=["build_id"],
        ),
        OpSpec(
            id="get_work_items_between_builds",
            label="Get Work Items Between Builds",
            method="GET",
            path="/build/workitems?api-version=7.1",
            visible_fields=["from_build_id", "to_build_id"],
            query_builder=lambda v: {
                "fromBuildId": int(getattr(v, "from_build_id", 0) or 0),
                "toBuildId": int(getattr(v, "to_build_id", 0) or 0),
            },
        ),
        OpSpec(
            id="query_work_items",
            label="Query Work Items (WIQL)",
            method="POST",
            path="/wit/wiql?api-version=7.1",
            visible_fields=["wiql_query"],
            body_builder=lambda v: {"query": getattr(v, "wiql_query", "") or ""},
        ),
        OpSpec(
            id="get_work_item",
            label="Get Work Item",
            method="GET",
            path="/wit/workitems/{work_item_id}?api-version=7.1&$expand={fields_expand}",
            visible_fields=["work_item_id", "fields_expand"],
        ),
        OpSpec(
            id="get_work_items_batch",
            label="Get Work Items (batch)",
            method="POST",
            path="/wit/workitemsbatch?api-version=7.1",
            visible_fields=["work_item_ids"],
            body_builder=lambda v: {"ids": getattr(v, "work_item_ids", []) or []},
        ),
        OpSpec(
            id="create_work_item",
            label="Create Work Item",
            method="POST",
            path="/wit/workitems/${work_item_type}?api-version=7.1",
            visible_fields=["work_item_type", "title", "description", "assigned_to", "state"],
            body_builder=lambda v: [
                {
                    "op": "add",
                    "path": "/fields/System.Title",
                    "value": getattr(v, "title", "") or "",
                },
                {
                    "op": "add",
                    "path": "/fields/System.Description",
                    "value": getattr(v, "description", "") or "",
                },
                {
                    "op": "add",
                    "path": "/fields/System.AssignedTo",
                    "value": getattr(v, "assigned_to", None) or None,
                }
                if getattr(v, "assigned_to", None)
                else None,
                {
                    "op": "add",
                    "path": "/fields/System.State",
                    "value": getattr(v, "state", None) or None,
                }
                if getattr(v, "state", None)
                else None,
            ],
        ),
        OpSpec(
            id="update_work_item",
            label="Update Work Item",
            method="PATCH",
            path="/wit/workitems/{work_item_id}?api-version=7.1",
            visible_fields=["work_item_id", "patch_body"],
            body_builder=lambda v: getattr(v, "patch_body", None) or [],
        ),
        OpSpec(
            id="add_comment",
            label="Add Work Item Comment",
            method="POST",
            path="/wit/workitems/{work_item_id}/comments?api-version=7.1-preview.3",
            visible_fields=["work_item_id", "comment_text"],
            body_builder=lambda v: {"text": getattr(v, "comment_text", "") or ""},
        ),
        OpSpec(
            id="get_comments",
            label="Get Work Item Comments",
            method="GET",
            path="/wit/workitems/{work_item_id}/comments?api-version=7.1-preview.3",
            visible_fields=["work_item_id"],
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "number"},
    ],
    allow_error=True,
)
