"""Airweave action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.airweave.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AirweaveNode = build_rest_node(MANIFEST)
