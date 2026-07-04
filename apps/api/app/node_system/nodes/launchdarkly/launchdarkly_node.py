"""LaunchDarkly action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.launchdarkly.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LaunchDarklyNode = build_rest_node(MANIFEST)
