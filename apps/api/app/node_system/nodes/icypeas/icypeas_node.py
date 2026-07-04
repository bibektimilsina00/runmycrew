"""Icypeas action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.icypeas.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

IcypeasNode = build_rest_node(MANIFEST)
