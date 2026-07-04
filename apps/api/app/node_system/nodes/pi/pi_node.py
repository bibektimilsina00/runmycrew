"""Pi action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.pi.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

PiNode = build_rest_node(MANIFEST)
