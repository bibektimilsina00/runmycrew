"""Dropcontact action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.dropcontact.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DropcontactNode = build_rest_node(MANIFEST)
