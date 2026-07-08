"""AWS RDS action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.aws.aws_rds.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSRDSNode = build_rest_node(MANIFEST)
