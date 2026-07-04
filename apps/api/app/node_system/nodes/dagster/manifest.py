"""Dagster Cloud action node — Dagster Cloud — asset pipelines, jobs, runs.

REST at https://{deployment}.dagster.cloud/graphql. See sim-parity roadmap Phase 4.22.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.dagster",
    name="Dagster Cloud",
    category="integration",
    description="Dagster Cloud — asset pipelines, jobs, runs.",
    icon_slug="dagster",
    color="#1c1c1c",
    base_url="https://{deployment}.dagster.cloud/graphql",
    credential_type="dagster_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="Dagster-Cloud-Api-Token",
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
            id="gql",
            label="GraphQL Query",
            method="POST",
            path="",
            visible_fields=["query", "variables"],
            body_builder=lambda v: {
                "query": getattr(v, "query", "") or "",
                "variables": getattr(v, "variables", None) or {},
            },
        ),
        OpSpec(
            id="launch_run",
            label="Launch Run",
            method="POST",
            path="",
            visible_fields=["run_config"],
            body_builder=lambda v: {
                "query": "mutation LaunchRun($runConfig: LaunchRunInput!) { launchRun(input: $runConfig) { __typename } }",
                "variables": {"runConfig": getattr(v, "run_config", None) or {}},
            },
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
