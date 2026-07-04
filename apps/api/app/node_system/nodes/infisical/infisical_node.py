"""Infisical action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.infisical.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

InfisicalNode = build_rest_node(MANIFEST)
