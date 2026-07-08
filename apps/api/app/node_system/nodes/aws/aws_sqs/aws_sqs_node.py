"""AWS SQS action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.aws.aws_sqs.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSSQSNode = build_rest_node(MANIFEST)
