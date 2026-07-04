"""Wiza action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.wiza.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

WizaNode = build_rest_node(MANIFEST)
