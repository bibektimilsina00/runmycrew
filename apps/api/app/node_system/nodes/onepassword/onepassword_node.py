"""1Password Connect action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.onepassword.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

OnePasswordConnectNode = build_rest_node(MANIFEST)
