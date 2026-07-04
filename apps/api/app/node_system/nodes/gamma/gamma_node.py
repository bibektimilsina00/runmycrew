"""Gamma action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.gamma.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GammaNode = build_rest_node(MANIFEST)
