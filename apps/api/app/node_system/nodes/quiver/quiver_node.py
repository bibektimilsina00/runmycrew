"""Quiver Quantitative action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.quiver.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

QuiverNode = build_rest_node(MANIFEST)
