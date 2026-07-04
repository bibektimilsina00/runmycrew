"""Railway action node — Railway — deploy + manage services.

REST at https://backboard.railway.app/graphql/v2. See sim-parity roadmap Phase 4.22.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.railway",
    name="Railway",
    category="integration",
    description="Railway — deploy + manage services.",
    icon_slug="railway",
    color="#1c1c1c",
    base_url="https://backboard.railway.app/graphql/v2",
    credential_type="railway_api_key",
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
    ],
    outputs_schema=[
        {"label": "data", "type": "object"},
        {"label": "id", "type": "string"},
        {"label": "status", "type": "string"},
    ],
    allow_error=True,
)
