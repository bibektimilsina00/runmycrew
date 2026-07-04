"""Google Groups action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google_groups.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GoogleGroupsNode = build_rest_node(MANIFEST)
