"""Obsidian Local REST action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.obsidian.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ObsidianNode = build_rest_node(MANIFEST)
