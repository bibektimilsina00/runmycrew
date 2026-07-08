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
    color="#ffffff",
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
        FieldSpec(name="job_name", label="Job Name", type="string"),
        FieldSpec(name="run_id", label="Run ID", type="string"),
        FieldSpec(name="schedule_name", label="Schedule Name", type="string"),
        FieldSpec(name="sensor_name", label="Sensor Name", type="string"),
        FieldSpec(name="asset_key", label="Asset Key (slash-separated)", type="string"),
        FieldSpec(name="asset_keys", label="Asset Keys (JSON array)", type="json", default=[]),
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
        OpSpec(
            id="get_run",
            label="Get Run",
            method="POST",
            path="/graphql",
            visible_fields=["run_id"],
            body_builder=lambda v: {
                "query": "query($id: ID!) { pipelineRunOrError(runId: $id) { ... on PipelineRun { id status runConfigYaml } } }",
                "variables": {"id": getattr(v, "run_id", "") or ""},
            },
        ),
        OpSpec(
            id="get_run_logs",
            label="Get Run Logs",
            method="POST",
            path="/graphql",
            visible_fields=["run_id"],
            body_builder=lambda v: {
                "query": "query($id: ID!) { pipelineRunOrError(runId: $id) { ... on PipelineRun { events { message level timestamp } } } }",
                "variables": {"id": getattr(v, "run_id", "") or ""},
            },
        ),
        OpSpec(
            id="list_runs",
            label="List Runs",
            method="POST",
            path="/graphql",
            visible_fields=[],
            body_builder=lambda v: {
                "query": "query { pipelineRunsOrError { ... on PipelineRuns { results { id status jobName createdAt } } } }"
            },
        ),
        OpSpec(
            id="list_jobs",
            label="List Jobs",
            method="POST",
            path="/graphql",
            visible_fields=[],
            body_builder=lambda v: {
                "query": "query { repositoriesOrError { ... on RepositoryConnection { nodes { name jobs { name } } } } }"
            },
        ),
        OpSpec(
            id="reexecute_run",
            label="Re-execute Run",
            method="POST",
            path="/graphql",
            visible_fields=["run_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!) { launchPipelineReexecution(executionParams: {parentRunId: $id}) { __typename } }",
                "variables": {"id": getattr(v, "run_id", "") or ""},
            },
        ),
        OpSpec(
            id="terminate_run",
            label="Terminate Run",
            method="POST",
            path="/graphql",
            visible_fields=["run_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!) { terminateRun(runId: $id) { __typename } }",
                "variables": {"id": getattr(v, "run_id", "") or ""},
            },
        ),
        OpSpec(
            id="delete_run",
            label="Delete Run",
            method="POST",
            path="/graphql",
            visible_fields=["run_id"],
            body_builder=lambda v: {
                "query": "mutation($id: String!) { deletePipelineRun(runId: $id) { __typename } }",
                "variables": {"id": getattr(v, "run_id", "") or ""},
            },
        ),
        OpSpec(
            id="list_schedules",
            label="List Schedules",
            method="POST",
            path="/graphql",
            visible_fields=[],
            body_builder=lambda v: {
                "query": "query { schedulesOrError { ... on Schedules { results { name status { status } } } } }"
            },
        ),
        OpSpec(
            id="start_schedule",
            label="Start Schedule",
            method="POST",
            path="/graphql",
            visible_fields=["schedule_name"],
            body_builder=lambda v: {
                "query": "mutation($name: String!) { startSchedule(scheduleSelector: {scheduleName: $name}) { __typename } }",
                "variables": {"name": getattr(v, "schedule_name", "") or ""},
            },
        ),
        OpSpec(
            id="stop_schedule",
            label="Stop Schedule",
            method="POST",
            path="/graphql",
            visible_fields=["schedule_name"],
            body_builder=lambda v: {
                "query": "mutation($name: String!) { stopRunningSchedule(scheduleName: $name) { __typename } }",
                "variables": {"name": getattr(v, "schedule_name", "") or ""},
            },
        ),
        OpSpec(
            id="list_sensors",
            label="List Sensors",
            method="POST",
            path="/graphql",
            visible_fields=[],
            body_builder=lambda v: {
                "query": "query { sensorsOrError { ... on Sensors { results { name status } } } }"
            },
        ),
        OpSpec(
            id="start_sensor",
            label="Start Sensor",
            method="POST",
            path="/graphql",
            visible_fields=["sensor_name"],
            body_builder=lambda v: {
                "query": "mutation($name: String!) { startSensor(sensorSelector: {sensorName: $name}) { __typename } }",
                "variables": {"name": getattr(v, "sensor_name", "") or ""},
            },
        ),
        OpSpec(
            id="stop_sensor",
            label="Stop Sensor",
            method="POST",
            path="/graphql",
            visible_fields=["sensor_name"],
            body_builder=lambda v: {
                "query": "mutation($name: String!) { stopSensor(sensorName: $name) { __typename } }",
                "variables": {"name": getattr(v, "sensor_name", "") or ""},
            },
        ),
        OpSpec(
            id="list_assets",
            label="List Assets",
            method="POST",
            path="/graphql",
            visible_fields=[],
            body_builder=lambda v: {
                "query": "query { assetNodes { assetKey { path } computeKind } }"
            },
        ),
        OpSpec(
            id="get_asset",
            label="Get Asset",
            method="POST",
            path="/graphql",
            visible_fields=["asset_key"],
            body_builder=lambda v: {
                "query": "query($key: [String!]!) { assetNodeOrError(assetKey: {path: $key}) { ... on AssetNode { assetKey { path } description } } }",
                "variables": {"key": (getattr(v, "asset_key", None) or "").split("/")},
            },
        ),
        OpSpec(
            id="materialize_assets",
            label="Materialize Assets",
            method="POST",
            path="/graphql",
            visible_fields=["asset_keys"],
            body_builder=lambda v: {
                "query": "mutation($keys: [AssetKeyInput!]!) { launchAssetLoadingJob(executionParams: {selector: {}, assetSelection: $keys}) { __typename } }",
                "variables": {"keys": getattr(v, "asset_keys", []) or []},
            },
        ),
        OpSpec(
            id="report_asset_materialization",
            label="Report Asset Materialization",
            method="POST",
            path="/graphql",
            visible_fields=["asset_key"],
            body_builder=lambda v: {
                "query": "mutation($key: [String!]!) { reportRunlessAssetEvents(eventParams: {assetKey: {path: $key}, eventType: ASSET_MATERIALIZATION}) { __typename } }",
                "variables": {"key": (getattr(v, "asset_key", None) or "").split("/")},
            },
        ),
        OpSpec(
            id="wipe_asset",
            label="Wipe Asset",
            method="POST",
            path="/graphql",
            visible_fields=["asset_key"],
            body_builder=lambda v: {
                "query": "mutation($key: [String!]!) { wipeAssets(assetKeys: [{path: $key}]) { __typename } }",
                "variables": {"key": (getattr(v, "asset_key", None) or "").split("/")},
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
