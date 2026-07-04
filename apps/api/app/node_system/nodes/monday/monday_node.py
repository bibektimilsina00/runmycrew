"""Monday.com action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.monday.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MondayNode = build_rest_node(MANIFEST)
