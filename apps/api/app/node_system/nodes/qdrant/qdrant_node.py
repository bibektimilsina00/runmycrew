"""Qdrant action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.qdrant.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

QdrantNode = build_rest_node(MANIFEST)
