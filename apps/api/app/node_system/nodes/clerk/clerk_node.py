"""Clerk action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.clerk.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ClerkNode = build_rest_node(MANIFEST)
