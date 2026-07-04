"""Grain action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.grain.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GrainNode = build_rest_node(MANIFEST)
