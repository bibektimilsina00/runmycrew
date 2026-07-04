"""Box action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.box.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

BoxNode = build_rest_node(MANIFEST)
