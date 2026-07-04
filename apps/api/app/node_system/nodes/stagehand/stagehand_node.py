"""Stagehand action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.stagehand.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

StagehandNode = build_rest_node(MANIFEST)
