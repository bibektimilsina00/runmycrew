"""Convex action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.convex.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ConvexNode = build_rest_node(MANIFEST)
