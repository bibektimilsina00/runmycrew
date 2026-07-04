"""AWS Athena action node — manifest form.

JSON protocol. POST `https://athena.{region}.amazonaws.com/`.
Content-Type `application/x-amz-json-1.1`. `X-Amz-Target:
AmazonAthena.<Action>` per op.

Athena query execution is async: `StartQueryExecution` returns a
QueryExecutionId; `GetQueryExecution` polls; `GetQueryResults`
retrieves rows after status becomes `SUCCEEDED`.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://athena.{region}.amazonaws.com/"


MANIFEST = ProviderManifest(
    type="action.aws_athena",
    name="Amazon Athena",
    category="integration",
    description="Amazon Athena — run SQL queries against S3 data via SigV4.",
    icon_slug="aws-athena",
    color="#1c1c1c",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="athena",
    aws_default_region="us-east-1",
    content_type="application/x-amz-json-1.1",
    fields=[
        FieldSpec(name="query", label="SQL Query", type="string"),
        FieldSpec(name="database", label="Database", type="string", placeholder="default"),
        FieldSpec(name="workgroup", label="Workgroup", type="string", default="primary"),
        FieldSpec(
            name="output_location",
            label="Output S3 Location",
            type="string",
            placeholder="s3://my-athena-results/",
        ),
        FieldSpec(name="query_execution_id", label="Query Execution ID", type="string"),
        FieldSpec(
            name="max_results",
            label="Max Result Rows",
            type="number",
            default=1000,
            mode="advanced",
        ),
        FieldSpec(name="next_token", label="Next Token", type="string", mode="advanced"),
    ],
    operations=[
        OpSpec(
            id="start_query",
            label="Start Query Execution",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "AmazonAthena.StartQueryExecution"},
            visible_fields=["query", "database", "workgroup", "output_location"],
            body_builder=lambda v: {
                "QueryString": getattr(v, "query", None) or "",
                "QueryExecutionContext": {"Database": getattr(v, "database", None) or "default"},
                "WorkGroup": getattr(v, "workgroup", None) or "primary",
                "ResultConfiguration": {
                    "OutputLocation": getattr(v, "output_location", None) or "",
                },
            },
        ),
        OpSpec(
            id="get_query_execution",
            label="Get Query Execution",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "AmazonAthena.GetQueryExecution"},
            visible_fields=["query_execution_id"],
            body_builder=lambda v: {
                "QueryExecutionId": getattr(v, "query_execution_id", None) or "",
            },
        ),
        OpSpec(
            id="get_query_results",
            label="Get Query Results",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "AmazonAthena.GetQueryResults"},
            visible_fields=["query_execution_id", "max_results", "next_token"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "QueryExecutionId": getattr(v, "query_execution_id", None) or "",
                    "MaxResults": int(getattr(v, "max_results", 1000) or 1000),
                    "NextToken": getattr(v, "next_token", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="stop_query",
            label="Stop Query Execution",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "AmazonAthena.StopQueryExecution"},
            visible_fields=["query_execution_id"],
            body_builder=lambda v: {
                "QueryExecutionId": getattr(v, "query_execution_id", None) or "",
            },
            success_payload_template={
                "stopped": True,
                "query_execution_id": "{query_execution_id}",
            },
        ),
        OpSpec(
            id="list_databases",
            label="List Databases",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "AmazonAthena.ListDatabases"},
            body_builder=lambda v: {"CatalogName": "AwsDataCatalog"},
        ),
        OpSpec(
            id="list_workgroups",
            label="List Workgroups",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "AmazonAthena.ListWorkGroups"},
            body_builder=lambda v: {},
        ),
    ],
    outputs_schema=[
        {"label": "QueryExecutionId", "type": "string"},
        {"label": "QueryExecution", "type": "object"},
        {"label": "ResultSet", "type": "object"},
        {"label": "DatabaseList", "type": "array"},
        {"label": "WorkGroups", "type": "array"},
        {"label": "NextToken", "type": "string"},
    ],
    allow_error=True,
)
