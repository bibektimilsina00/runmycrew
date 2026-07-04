"""Zendesk action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.zendesk.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ZendeskNode = build_rest_node(MANIFEST)
