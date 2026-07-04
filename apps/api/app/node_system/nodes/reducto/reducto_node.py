"""Reducto action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.reducto.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ReductoNode = build_rest_node(MANIFEST)
