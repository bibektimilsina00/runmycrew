"""AWS AppConfig action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.aws_appconfig.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSAppConfigNode = build_rest_node(MANIFEST)
