"""Exa action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.exa.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ExaNode = build_rest_node(MANIFEST)
