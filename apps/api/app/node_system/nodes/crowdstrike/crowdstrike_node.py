"""CrowdStrike Falcon action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.crowdstrike.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

CrowdStrikeNode = build_rest_node(MANIFEST)
