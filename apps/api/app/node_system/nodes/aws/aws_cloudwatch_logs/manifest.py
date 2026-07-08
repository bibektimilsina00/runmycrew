"""AWS CloudWatch Logs action node — manifest form.

Uses AWS's JSON protocol at `https://logs.{region}.amazonaws.com/`
with `X-Amz-Target: Logs_20140328.<Action>` and
Content-Type `application/x-amz-json-1.1`.

CloudWatch has two APIs — this covers Logs (log groups, streams,
events). Metrics API (PutMetricData, GetMetricStatistics) uses the
Query protocol and lives under a separate node when demand shows up.
"""

from __future__ import annotations

from apps.api.app.node_system.scaffolds import (
    FieldSpec,
    OpSpec,
    ProviderManifest,
)

_HOST = "https://logs.{region}.amazonaws.com/"

MANIFEST = ProviderManifest(
    type="action.aws_cloudwatch_logs",
    name="AWS CloudWatch Logs",
    category="integration",
    description="AWS CloudWatch Logs — log groups, streams, events, filters.",
    icon_slug="aws-cloudwatch",
    color="#ffffff",
    base_url="",
    credential_type="aws_credentials",
    token_field=["secret_access_key"],
    auth="aws_sigv4",
    aws_service="logs",
    aws_default_region="us-east-1",
    content_type="application/x-amz-json-1.1",
    fields=[
        FieldSpec(name="log_group_name", label="Log Group", type="string"),
        FieldSpec(name="log_stream_name", label="Log Stream", type="string"),
        FieldSpec(name="log_events", label="Log Events (JSON array)", type="json"),
        FieldSpec(name="filter_pattern", label="Filter Pattern", type="string", mode="advanced"),
        FieldSpec(name="start_time", label="Start Time (ms epoch)", type="number", mode="advanced"),
        FieldSpec(name="end_time", label="End Time (ms epoch)", type="number", mode="advanced"),
        FieldSpec(name="limit", label="Limit", type="number", default=100, mode="advanced"),
        FieldSpec(name="next_token", label="Next Token", type="string", mode="advanced"),
        FieldSpec(
            name="retention_days",
            label="Retention Days",
            type="number",
            default=30,
            mode="advanced",
        ),
    ],
    operations=[
        OpSpec(
            id="describe_log_groups",
            label="Describe Log Groups",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "Logs_20140328.DescribeLogGroups"},
            visible_fields=["log_group_name", "limit", "next_token"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "logGroupNamePrefix": getattr(v, "log_group_name", None),
                    "limit": int(getattr(v, "limit", 100) or 100),
                    "nextToken": getattr(v, "next_token", None),
                }.items()
                if val is not None
            },
        ),
        OpSpec(
            id="create_log_group",
            label="Create Log Group",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "Logs_20140328.CreateLogGroup"},
            visible_fields=["log_group_name"],
            body_builder=lambda v: {"logGroupName": getattr(v, "log_group_name", None) or ""},
        ),
        OpSpec(
            id="delete_log_group",
            label="Delete Log Group",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "Logs_20140328.DeleteLogGroup"},
            visible_fields=["log_group_name"],
            body_builder=lambda v: {"logGroupName": getattr(v, "log_group_name", None) or ""},
            success_payload_template={"deleted": True, "log_group_name": "{log_group_name}"},
        ),
        OpSpec(
            id="put_retention_policy",
            label="Put Retention Policy",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "Logs_20140328.PutRetentionPolicy"},
            visible_fields=["log_group_name", "retention_days"],
            body_builder=lambda v: {
                "logGroupName": getattr(v, "log_group_name", None) or "",
                "retentionInDays": int(getattr(v, "retention_days", 30) or 30),
            },
        ),
        OpSpec(
            id="describe_log_streams",
            label="Describe Log Streams",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "Logs_20140328.DescribeLogStreams"},
            visible_fields=["log_group_name", "limit"],
            body_builder=lambda v: {
                "logGroupName": getattr(v, "log_group_name", None) or "",
                "limit": int(getattr(v, "limit", 100) or 100),
            },
        ),
        OpSpec(
            id="create_log_stream",
            label="Create Log Stream",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "Logs_20140328.CreateLogStream"},
            visible_fields=["log_group_name", "log_stream_name"],
            body_builder=lambda v: {
                "logGroupName": getattr(v, "log_group_name", None) or "",
                "logStreamName": getattr(v, "log_stream_name", None) or "",
            },
        ),
        OpSpec(
            id="put_log_events",
            label="Put Log Events",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "Logs_20140328.PutLogEvents"},
            visible_fields=["log_group_name", "log_stream_name", "log_events"],
            body_builder=lambda v: {
                "logGroupName": getattr(v, "log_group_name", None) or "",
                "logStreamName": getattr(v, "log_stream_name", None) or "",
                "logEvents": getattr(v, "log_events", None) or [],
            },
        ),
        OpSpec(
            id="filter_log_events",
            label="Filter Log Events",
            method="POST",
            path=_HOST,
            extra_headers={"X-Amz-Target": "Logs_20140328.FilterLogEvents"},
            visible_fields=["log_group_name", "filter_pattern", "start_time", "end_time", "limit"],
            body_builder=lambda v: {
                k: val
                for k, val in {
                    "logGroupName": getattr(v, "log_group_name", None) or "",
                    "filterPattern": getattr(v, "filter_pattern", None),
                    "startTime": (
                        int(v.start_time) if getattr(v, "start_time", None) is not None else None
                    ),
                    "endTime": (
                        int(v.end_time) if getattr(v, "end_time", None) is not None else None
                    ),
                    "limit": int(getattr(v, "limit", 100) or 100),
                }.items()
                if val is not None
            },
        ),
    ],
    outputs_schema=[
        {"label": "logGroups", "type": "array"},
        {"label": "logStreams", "type": "array"},
        {"label": "events", "type": "array"},
        {"label": "nextToken", "type": "string"},
        {"label": "nextForwardToken", "type": "string"},
    ],
    allow_error=True,
)
