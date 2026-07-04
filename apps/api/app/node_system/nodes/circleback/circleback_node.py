"""Circleback action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.circleback.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

CirclebackNode = build_rest_node(MANIFEST)
