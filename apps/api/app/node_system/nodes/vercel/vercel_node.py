"""Vercel action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.vercel.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

VercelNode = build_rest_node(MANIFEST)
