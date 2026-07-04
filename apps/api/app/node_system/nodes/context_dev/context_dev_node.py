"""Context action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.context_dev.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ContextNode = build_rest_node(MANIFEST)
