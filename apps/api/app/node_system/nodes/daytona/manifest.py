"""Daytona action node — Daytona — cloud dev environments.

REST at https://app.daytona.io/api. See sim-parity roadmap Phase 4.22.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.daytona",
    name="Daytona",
    category="integration",
    description="Daytona — cloud dev environments.",
    icon_slug="daytona",
    color="#ffffff",
    base_url="https://app.daytona.io/api",
    credential_type="daytona_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="query", label="GraphQL Query / Search Query", type="string"),
        FieldSpec(name="variables", label="Variables (JSON)", type="json"),
        FieldSpec(name="run_config", label="Run Config (JSON)", type="json"),
        FieldSpec(name="workspace_id", label="Workspace ID", type="string"),
        FieldSpec(name="name", label="Name", type="string"),
        FieldSpec(name="repository", label="Repository URL", type="string"),
        FieldSpec(name="project_key", label="Project Key", type="string"),
        FieldSpec(name="flag_key", label="Feature Flag Key", type="string"),
        FieldSpec(name="environment_key", label="Environment Key", type="string"),
        FieldSpec(name="enabled", label="Enabled (true/false)", type="string"),
        FieldSpec(name="severity_id", label="Severity ID", type="string"),
        FieldSpec(name="severity", label="Severity (slug)", type="string"),
        FieldSpec(name="summary", label="Summary", type="string"),
        FieldSpec(name="visibility", label="Visibility", type="string", default="public"),
        FieldSpec(name="incident_id", label="Incident ID", type="string"),
        FieldSpec(name="title", label="Title", type="string"),
        FieldSpec(name="status", label="Status", type="string"),
        FieldSpec(name="page_size", label="Page Size", type="number", default=25, mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="list_workspaces",
            label="List Workspaces",
            method="GET",
            path="/workspaces",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_workspace",
            label="Get Workspace",
            method="GET",
            path="/workspaces/{workspace_id}",
            visible_fields=["workspace_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_workspace",
            label="Create Workspace",
            method="POST",
            path="/workspaces",
            visible_fields=["name", "repository"],
            body_builder=lambda v: {
                "name": getattr(v, "name", "") or "",
                "repository": {"url": getattr(v, "repository", "") or ""},
            },
        ),
        OpSpec(
            id="delete_workspace",
            label="Delete Workspace",
            method="DELETE",
            path="/workspaces/{workspace_id}",
            visible_fields=["workspace_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="start_workspace",
            label="Start Workspace",
            method="POST",
            path="/workspaces/{workspace_id}/start",
            visible_fields=["workspace_id"],
            body_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
