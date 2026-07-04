"""incident.io action node — incident.io — incident response + postmortems.

REST at https://api.incident.io/v2. See sim-parity roadmap Phase 4.22.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.incidentio",
    name="incident.io",
    category="integration",
    description="incident.io — incident response + postmortems.",
    icon_slug="incidentio",
    color="#1c1c1c",
    base_url="https://api.incident.io/v2",
    credential_type="incidentio_api_key",
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
            id="create_incident",
            label="Create Incident",
            method="POST",
            path="/incidents",
            visible_fields=["name", "severity_id", "summary", "visibility"],
            body_builder=lambda v: {
                "name": getattr(v, "name", "") or "",
                "severity_id": getattr(v, "severity_id", None) or None,
                "summary": getattr(v, "summary", None) or None,
                "visibility": getattr(v, "visibility", None) or "public",
                "idempotency_key": (getattr(v, "name", "") or "")
                + "-"
                + (getattr(v, "severity_id", None) or ""),
            },
        ),
        OpSpec(
            id="list_incidents",
            label="List Incidents",
            method="GET",
            path="/incidents",
            visible_fields=["page_size"],
            query_builder=lambda v: {"page_size": int(getattr(v, "page_size", 25) or 25)},
        ),
        OpSpec(
            id="get_incident",
            label="Get Incident",
            method="GET",
            path="/incidents/{incident_id}",
            visible_fields=["incident_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="update_incident",
            label="Update Incident",
            method="POST",
            path="/incident_updates",
            visible_fields=["incident_id", "summary"],
            body_builder=lambda v: {
                "incident_update": {
                    "incident_id": getattr(v, "incident_id", "") or "",
                    "message": getattr(v, "summary", "") or "",
                }
            },
        ),
        OpSpec(
            id="list_severities",
            label="List Severities",
            method="GET",
            path="/severities",
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
