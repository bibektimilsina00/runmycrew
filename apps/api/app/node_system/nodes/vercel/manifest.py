"""Vercel action node — manifest form.

Vercel's REST API lives at `https://api.vercel.com`. Bearer auth using
a personal access token. Ops we expose:

  - Deployments — list, get, cancel
  - Projects — list, get
  - Domains — list, add, remove
  - Env vars — list, create

`team_id` is a query param the user passes when their token belongs to
a personal account but they want to act on a team. Optional everywhere.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

MANIFEST = ProviderManifest(
    type="action.vercel",
    name="Vercel",
    category="integration",
    description="Manage Vercel deployments, projects, domains, and env vars.",
    icon_slug="vercel",
    color="#ffffff",
    base_url="https://api.vercel.com",
    credential_type="vercel_api_key",
    token_field=["api_key"],
    auth="bearer",
    fields=[
        FieldSpec(name="team_id", label="Team ID (optional)", type="string", mode="advanced"),
        FieldSpec(name="project_id", label="Project ID or name", type="string"),
        FieldSpec(name="deployment_id", label="Deployment ID", type="string"),
        FieldSpec(name="domain", label="Domain", type="string"),
        FieldSpec(name="limit", label="Limit", type="number", default=20, mode="advanced"),
        FieldSpec(name="env_key", label="Env Var Key", type="string"),
        FieldSpec(name="env_value", label="Env Var Value", type="string", secret=True),
        FieldSpec(
            name="env_target",
            label="Env Target (JSON array)",
            type="json",
            mode="advanced",
            placeholder='["production", "preview"]',
        ),
        FieldSpec(
            name="env_type",
            label="Env Var Type",
            type="options",
            default="encrypted",
            mode="advanced",
            options=[
                {"label": "Encrypted", "value": "encrypted"},
                {"label": "Plain", "value": "plain"},
                {"label": "System", "value": "system"},
                {"label": "Sensitive", "value": "sensitive"},
            ],
        ),
    ],
    operations=[
        OpSpec(
            id="list_deployments",
            label="List Deployments",
            method="GET",
            path="/v6/deployments",
            visible_fields=["project_id", "team_id", "limit"],
            query_fields=["project_id", "team_id", "limit"],
        ),
        OpSpec(
            id="get_deployment",
            label="Get Deployment",
            method="GET",
            path="/v13/deployments/{deployment_id}",
            visible_fields=["deployment_id", "team_id"],
            query_fields=["team_id"],
        ),
        OpSpec(
            id="cancel_deployment",
            label="Cancel Deployment",
            method="PATCH",
            path="/v12/deployments/{deployment_id}/cancel",
            visible_fields=["deployment_id", "team_id"],
            query_fields=["team_id"],
        ),
        OpSpec(
            id="list_projects",
            label="List Projects",
            method="GET",
            path="/v9/projects",
            visible_fields=["team_id", "limit"],
            query_fields=["team_id", "limit"],
        ),
        OpSpec(
            id="get_project",
            label="Get Project",
            method="GET",
            path="/v9/projects/{project_id}",
            visible_fields=["project_id", "team_id"],
            query_fields=["team_id"],
        ),
        OpSpec(
            id="list_domains",
            label="List Domains",
            method="GET",
            path="/v9/projects/{project_id}/domains",
            visible_fields=["project_id", "team_id"],
            query_fields=["team_id"],
        ),
        OpSpec(
            id="add_domain",
            label="Add Domain",
            method="POST",
            path="/v10/projects/{project_id}/domains",
            visible_fields=["project_id", "domain", "team_id"],
            query_fields=["team_id"],
            body_template={"name": "{domain}"},
        ),
        OpSpec(
            id="remove_domain",
            label="Remove Domain",
            method="DELETE",
            path="/v9/projects/{project_id}/domains/{domain}",
            visible_fields=["project_id", "domain", "team_id"],
            query_fields=["team_id"],
            success_payload_template={"deleted": True, "domain": "{domain}"},
        ),
        OpSpec(
            id="list_env_vars",
            label="List Env Vars",
            method="GET",
            path="/v9/projects/{project_id}/env",
            visible_fields=["project_id", "team_id"],
            query_fields=["team_id"],
        ),
        OpSpec(
            id="create_env_var",
            label="Create Env Var",
            method="POST",
            path="/v10/projects/{project_id}/env",
            visible_fields=[
                "project_id",
                "env_key",
                "env_value",
                "env_target",
                "env_type",
                "team_id",
            ],
            query_fields=["team_id"],
            body_builder=lambda props: {
                "key": getattr(props, "env_key", None),
                "value": getattr(props, "env_value", None),
                "type": getattr(props, "env_type", None) or "encrypted",
                "target": getattr(props, "env_target", None) or ["production"],
            },
        ),
    ],
    outputs_schema=[
        {"label": "id", "type": "string"},
        {"label": "name", "type": "string"},
        {"label": "url", "type": "string"},
        {"label": "state", "type": "string"},
        {"label": "items", "type": "array"},
        {"label": "deployments", "type": "array"},
        {"label": "projects", "type": "array"},
    ],
    allow_error=True,
)
