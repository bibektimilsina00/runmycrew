"""AWS Identity Center action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.identity_center.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSIdentityCenterNode = build_rest_node(MANIFEST)
