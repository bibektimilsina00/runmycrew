"""AWS CloudWatch Logs action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.aws.aws_cloudwatch_logs.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSCloudWatchLogsNode = build_rest_node(MANIFEST)
