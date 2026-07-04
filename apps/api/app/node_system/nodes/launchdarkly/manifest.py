"""LaunchDarkly action node — LaunchDarkly — feature flags + segments.

REST at https://app.launchdarkly.com/api/v2. See sim-parity roadmap Phase 4.22.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.launchdarkly",
    name="LaunchDarkly",
    category="integration",
    description="LaunchDarkly — feature flags + segments.",
    icon_slug="launchdarkly",
    color="#1c1c1c",
    base_url="https://app.launchdarkly.com/api/v2",
    credential_type="launchdarkly_api_key",
    token_field=["api_key"],
    auth="header_token",
    auth_header_name="Authorization",
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
            id="list_flags",
            label="List Feature Flags",
            method="GET",
            path="/flags/{project_key}",
            visible_fields=["project_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_flag",
            label="Get Feature Flag",
            method="GET",
            path="/flags/{project_key}/{flag_key}",
            visible_fields=["project_key", "flag_key"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="toggle_flag",
            label="Toggle Flag (patch)",
            method="PATCH",
            path="/flags/{project_key}/{flag_key}",
            visible_fields=["project_key", "flag_key", "environment_key", "enabled"],
            body_builder=lambda v: [
                {
                    "op": "replace",
                    "path": f"/environments/{getattr(v, 'environment_key', '')}/on",
                    "value": (getattr(v, "enabled", None) or "false").lower() == "true",
                }
            ],
        ),
        OpSpec(
            id="list_projects",
            label="List Projects",
            method="GET",
            path="/projects",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
