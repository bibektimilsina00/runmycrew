"""Parallel AI action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.parallel_ai.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ParallelAINode = build_rest_node(MANIFEST)
