"""Plivo action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.plivo.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

PlivoNode = build_rest_node(MANIFEST)
