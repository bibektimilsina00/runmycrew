"""WordPress action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.wordpress.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

WordPressNode = build_rest_node(MANIFEST)
