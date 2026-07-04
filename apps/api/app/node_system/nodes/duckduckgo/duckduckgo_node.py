"""DuckDuckGo action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.duckduckgo.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DuckDuckGoNode = build_rest_node(MANIFEST)
