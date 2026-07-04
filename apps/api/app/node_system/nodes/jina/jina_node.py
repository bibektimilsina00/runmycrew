"""Jina AI action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.jina.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

JinaAINode = build_rest_node(MANIFEST)
