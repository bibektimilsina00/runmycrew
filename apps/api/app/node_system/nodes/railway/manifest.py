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
        FieldSpec(name="gql_query", label="GraphQL Query", type="string"),
        FieldSpec(name="project_id", label="Project ID", type="string"),
        FieldSpec(name="project_name", label="Project Name", type="string"),
        FieldSpec(name="environment_id", label="Environment ID", type="string"),
        FieldSpec(name="environment_name", label="Environment Name", type="string"),
        FieldSpec(name="service_id", label="Service ID", type="string"),
        FieldSpec(name="service_name", label="Service Name", type="string"),
        FieldSpec(name="deployment_id", label="Deployment ID", type="string"),
        FieldSpec(name="var_name", label="Variable Name", type="string"),
        FieldSpec(name="var_value", label="Variable Value", type="string"),
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
            id="list_projects",
            label="List Projects",
            method="POST",
            path="/graphql/v2",
            visible_fields=["gql_query"],
            body_builder=lambda v: {
                "query": "query { projects { edges { node { id name description } } } }"
            },
        ),
        OpSpec(
            id="get_project",
            label="Get Project",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id"],
            body_builder=lambda v: {
                "query": "query($id: String!) { project(id: $id) { id name description environments { edges { node { id name } } } services { edges { node { id name } } } } }",
                "variables": {"id": getattr(v, "project_id", "") or ""},
            },
        ),
        OpSpec(
            id="create_project",
            label="Create Project",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_name"],
            body_builder=lambda v: {
                "query": "mutation($name: String!) { projectCreate(input: {name: $name}) { id name } }",
                "variables": {"name": getattr(v, "project_name", "") or ""},
            },
        ),
        OpSpec(
            id="delete_project",
            label="Delete Project",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!) { projectDelete(id: $id) }",
                "variables": {"id": getattr(v, "project_id", "") or ""},
            },
        ),
        OpSpec(
            id="create_environment",
            label="Create Environment",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id", "environment_name"],
            body_builder=lambda v: {
                "query": "mutation($projectId: String!, $name: String!) { environmentCreate(input: {projectId: $projectId, name: $name}) { id name } }",
                "variables": {
                    "projectId": getattr(v, "project_id", "") or "",
                    "name": getattr(v, "environment_name", "") or "",
                },
            },
        ),
        OpSpec(
            id="delete_environment",
            label="Delete Environment",
            method="POST",
            path="/graphql/v2",
            visible_fields=["environment_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!) { environmentDelete(id: $id) }",
                "variables": {"id": getattr(v, "environment_id", "") or ""},
            },
        ),
        OpSpec(
            id="create_service",
            label="Create Service",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id", "service_name"],
            body_builder=lambda v: {
                "query": "mutation($projectId: String!, $name: String!) { serviceCreate(input: {projectId: $projectId, name: $name}) { id name } }",
                "variables": {
                    "projectId": getattr(v, "project_id", "") or "",
                    "name": getattr(v, "service_name", "") or "",
                },
            },
        ),
        OpSpec(
            id="delete_service",
            label="Delete Service",
            method="POST",
            path="/graphql/v2",
            visible_fields=["service_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!) { serviceDelete(id: $id) }",
                "variables": {"id": getattr(v, "service_id", "") or ""},
            },
        ),
        OpSpec(
            id="list_deployments",
            label="List Deployments",
            method="POST",
            path="/graphql/v2",
            visible_fields=["service_id"],
            body_builder=lambda v: {
                "query": "query($id: String!) { service(id: $id) { deployments { edges { node { id status createdAt } } } } }",
                "variables": {"id": getattr(v, "service_id", "") or ""},
            },
        ),
        OpSpec(
            id="get_deployment",
            label="Get Deployment",
            method="POST",
            path="/graphql/v2",
            visible_fields=["deployment_id"],
            body_builder=lambda v: {
                "query": "query($id: String!) { deployment(id: $id) { id status url meta } }",
                "variables": {"id": getattr(v, "deployment_id", "") or ""},
            },
        ),
        OpSpec(
            id="deploy_service",
            label="Deploy Service",
            method="POST",
            path="/graphql/v2",
            visible_fields=["service_id", "environment_id"],
            body_builder=lambda v: {
                "query": "mutation($serviceId: String!, $environmentId: String!) { serviceInstanceDeploy(serviceId: $serviceId, environmentId: $environmentId) }",
                "variables": {
                    "serviceId": getattr(v, "service_id", "") or "",
                    "environmentId": getattr(v, "environment_id", "") or "",
                },
            },
        ),
        OpSpec(
            id="restart_deployment",
            label="Restart Deployment",
            method="POST",
            path="/graphql/v2",
            visible_fields=["deployment_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!) { deploymentRestart(id: $id) }",
                "variables": {"id": getattr(v, "deployment_id", "") or ""},
            },
        ),
        OpSpec(
            id="rollback_deployment",
            label="Rollback Deployment",
            method="POST",
            path="/graphql/v2",
            visible_fields=["deployment_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!) { deploymentRollback(id: $id) }",
                "variables": {"id": getattr(v, "deployment_id", "") or ""},
            },
        ),
        OpSpec(
            id="get_deployment_logs",
            label="Get Deployment Logs",
            method="POST",
            path="/graphql/v2",
            visible_fields=["deployment_id"],
            body_builder=lambda v: {
                "query": "query($id: String!) { deploymentLogs(deploymentId: $id) { timestamp message } }",
                "variables": {"id": getattr(v, "deployment_id", "") or ""},
            },
        ),
        OpSpec(
            id="list_variables",
            label="List Variables",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id", "environment_id", "service_id"],
            body_builder=lambda v: {
                "query": "query($projectId: String!, $environmentId: String!, $serviceId: String) { variables(projectId: $projectId, environmentId: $environmentId, serviceId: $serviceId) }",
                "variables": {
                    "projectId": getattr(v, "project_id", "") or "",
                    "environmentId": getattr(v, "environment_id", "") or "",
                    "serviceId": getattr(v, "service_id", None) or None,
                },
            },
        ),
        OpSpec(
            id="upsert_variable",
            label="Upsert Variable",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id", "environment_id", "service_id", "var_name", "var_value"],
            body_builder=lambda v: {
                "query": "mutation($input: VariableUpsertInput!) { variableUpsert(input: $input) }",
                "variables": {
                    "input": {
                        "projectId": getattr(v, "project_id", "") or "",
                        "environmentId": getattr(v, "environment_id", "") or "",
                        "serviceId": getattr(v, "service_id", None) or None,
                        "name": getattr(v, "var_name", "") or "",
                        "value": getattr(v, "var_value", "") or "",
                    }
                },
            },
        ),
        OpSpec(
            id="delete_variable",
            label="Delete Variable",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id", "environment_id", "service_id", "var_name"],
            body_builder=lambda v: {
                "query": "mutation($input: VariableDeleteInput!) { variableDelete(input: $input) }",
                "variables": {
                    "input": {
                        "projectId": getattr(v, "project_id", "") or "",
                        "environmentId": getattr(v, "environment_id", "") or "",
                        "serviceId": getattr(v, "service_id", None) or None,
                        "name": getattr(v, "var_name", "") or "",
                    }
                },
            },
        ),
        OpSpec(
            id="list_project_members",
            label="List Project Members",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id"],
            body_builder=lambda v: {
                "query": "query($id: String!) { project(id: $id) { members { edges { node { id user { email name } role } } } } }",
                "variables": {"id": getattr(v, "project_id", "") or ""},
            },
        ),
        OpSpec(
            id="transfer_project",
            label="Transfer Project",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id", "workspace_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!, $wsId: String!) { projectTransfer(projectId: $id, workspaceId: $wsId) }",
                "variables": {
                    "id": getattr(v, "project_id", "") or "",
                    "wsId": getattr(v, "workspace_id", "") or "",
                },
            },
        ),
        OpSpec(
            id="update_project",
            label="Update Project",
            method="POST",
            path="/graphql/v2",
            visible_fields=["project_id", "project_name"],
            body_builder=lambda v: {
                "query": "mutation($id: String!, $name: String!) { projectUpdate(id: $id, input: {name: $name}) { id name } }",
                "variables": {
                    "id": getattr(v, "project_id", "") or "",
                    "name": getattr(v, "project_name", "") or "",
                },
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
