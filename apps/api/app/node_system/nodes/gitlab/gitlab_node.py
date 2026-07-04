"""GitLab action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.gitlab.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GitLabNode = build_rest_node(MANIFEST)
