"""Mem0 action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.mem0.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

Mem0Node = build_rest_node(MANIFEST)
