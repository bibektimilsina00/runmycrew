"""Rootly action node — Rootly — incident response, retros, integrations.

REST at https://api.rootly.com/v1. See sim-parity roadmap Phase 4.22.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import FieldSpec, OpSpec, ProviderManifest

MANIFEST = ProviderManifest(
    type="action.rootly",
    name="Rootly",
    category="integration",
    description="Rootly — incident response, retros, integrations.",
    icon_slug="rootly",
    color="#1c1c1c",
    base_url="https://api.rootly.com/v1",
    credential_type="rootly_api_key",
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
        FieldSpec(name="incident_body", label="Incident Body (JSON)", type="json", default={}),
        FieldSpec(name="service_id", label="Service ID", type="string"),
        FieldSpec(name="playbook_id", label="Playbook ID", type="string"),
        FieldSpec(
            name="action_item_body", label="Action Item Body (JSON)", type="json", default={}
        ),
    ],
    operations=[
        OpSpec(
            id="create_incident",
            label="Create Incident",
            method="POST",
            path="/incidents",
            visible_fields=["title", "severity", "summary"],
            body_builder=lambda v: {
                "data": {
                    "type": "incidents",
                    "attributes": {
                        k: val
                        for k, val in {
                            "title": getattr(v, "title", None) or None,
                            "severity": getattr(v, "severity", None) or None,
                            "summary": getattr(v, "summary", None) or None,
                        }.items()
                        if val is not None
                    },
                }
            },
        ),
        OpSpec(
            id="list_incidents",
            label="List Incidents",
            method="GET",
            path="/incidents",
            visible_fields=["page_size"],
            query_builder=lambda v: {"page[size]": int(getattr(v, "page_size", 25) or 25)},
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
            method="PATCH",
            path="/incidents/{incident_id}",
            visible_fields=["incident_id", "title", "status"],
            body_builder=lambda v: {
                "data": {
                    "type": "incidents",
                    "attributes": {
                        k: val
                        for k, val in {
                            "title": getattr(v, "title", None) or None,
                            "status": getattr(v, "status", None) or None,
                        }.items()
                        if val is not None
                    },
                }
            },
        ),
        OpSpec(
            id="resolve_incident",
            label="Resolve Incident",
            method="PUT",
            path="/v1/incidents/{incident_id}/resolve",
            visible_fields=["incident_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="cancel_incident",
            label="Cancel Incident",
            method="PUT",
            path="/v1/incidents/{incident_id}/cancel",
            visible_fields=["incident_id"],
            body_builder=lambda v: {},
        ),
        OpSpec(
            id="list_services",
            label="List Services",
            method="GET",
            path="/v1/services",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_service",
            label="Get Service",
            method="GET",
            path="/v1/services/{service_id}",
            visible_fields=["service_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_teams",
            label="List Teams",
            method="GET",
            path="/v1/teams",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_users",
            label="List Users",
            method="GET",
            path="/v1/users",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_severities",
            label="List Severities",
            method="GET",
            path="/v1/severities",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_environments",
            label="List Environments",
            method="GET",
            path="/v1/environments",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_functionalities",
            label="List Functionalities",
            method="GET",
            path="/v1/functionalities",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_playbooks",
            label="List Playbooks",
            method="GET",
            path="/v1/playbooks",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="get_playbook",
            label="Get Playbook",
            method="GET",
            path="/v1/playbooks/{playbook_id}",
            visible_fields=["playbook_id"],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_action_items",
            label="List Action Items",
            method="GET",
            path="/v1/action_items",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="create_action_item",
            label="Create Action Item",
            method="POST",
            path="/v1/action_items",
            visible_fields=["action_item_body"],
            body_builder=lambda v: getattr(v, "action_item_body", None) or {},
        ),
        OpSpec(
            id="list_alerts",
            label="List Alerts",
            method="GET",
            path="/v1/alerts",
            visible_fields=[],
            query_builder=lambda v: {},
        ),
        OpSpec(
            id="list_events",
            label="List Events",
            method="GET",
            path="/v1/incident_events",
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
