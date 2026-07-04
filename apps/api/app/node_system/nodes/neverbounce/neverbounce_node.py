"""NeverBounce action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.neverbounce.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

NeverBounceNode = build_rest_node(MANIFEST)
