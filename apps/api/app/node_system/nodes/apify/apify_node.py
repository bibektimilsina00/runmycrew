"""Apify action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.apify.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ApifyNode = build_rest_node(MANIFEST)
