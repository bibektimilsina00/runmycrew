"""HubSpot action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.hubspot.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

HubSpotNode = build_rest_node(MANIFEST)
