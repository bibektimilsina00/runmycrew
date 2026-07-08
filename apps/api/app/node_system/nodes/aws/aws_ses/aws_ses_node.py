"""AWS SES action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.aws.aws_ses.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSSESNode = build_rest_node(MANIFEST)
