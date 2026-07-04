"""Findymail action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.findymail.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

FindymailNode = build_rest_node(MANIFEST)
