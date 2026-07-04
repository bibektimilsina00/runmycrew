"""Datagma action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.datagma.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DatagmaNode = build_rest_node(MANIFEST)
