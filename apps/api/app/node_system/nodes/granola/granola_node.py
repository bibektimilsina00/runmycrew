"""Granola action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.granola.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GranolaNode = build_rest_node(MANIFEST)
