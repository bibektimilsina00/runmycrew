"""Confluence action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.atlassian.confluence.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ConfluenceNode = build_rest_node(MANIFEST)
