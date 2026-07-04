"""Lemlist action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.lemlist.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LemlistNode = build_rest_node(MANIFEST)
