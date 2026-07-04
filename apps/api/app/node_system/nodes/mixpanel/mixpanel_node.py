"""Mixpanel action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.mixpanel.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MixpanelNode = build_rest_node(MANIFEST)
