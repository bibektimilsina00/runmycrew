"""Rootly action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.rootly.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

RootlyNode = build_rest_node(MANIFEST)
