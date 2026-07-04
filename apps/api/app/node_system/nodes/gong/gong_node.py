"""Gong action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.gong.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GongNode = build_rest_node(MANIFEST)
