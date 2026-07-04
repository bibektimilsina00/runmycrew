"""Postmark action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.postmark.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

PostmarkNode = build_rest_node(MANIFEST)
