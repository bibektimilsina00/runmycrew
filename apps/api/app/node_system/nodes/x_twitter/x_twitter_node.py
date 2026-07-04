"""X (Twitter) action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.x_twitter.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

XTwitterNode = build_rest_node(MANIFEST)
