"""Kalshi action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.kalshi.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

KalshiNode = build_rest_node(MANIFEST)
