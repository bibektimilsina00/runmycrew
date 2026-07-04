"""Clay action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.clay.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ClayNode = build_rest_node(MANIFEST)
