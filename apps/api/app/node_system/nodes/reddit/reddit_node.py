"""Reddit action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.reddit.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

RedditNode = build_rest_node(MANIFEST)
