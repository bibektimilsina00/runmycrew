"""Enrich.so action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.enrich.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

EnrichsoNode = build_rest_node(MANIFEST)
