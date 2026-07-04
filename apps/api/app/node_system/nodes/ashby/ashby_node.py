"""Ashby action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.ashby.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AshbyNode = build_rest_node(MANIFEST)
