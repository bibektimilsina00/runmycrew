"""AWS STS action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.aws_sts.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSSTSNode = build_rest_node(MANIFEST)
