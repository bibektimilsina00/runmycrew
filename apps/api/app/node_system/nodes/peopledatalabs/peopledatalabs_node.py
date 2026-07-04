"""People Data Labs action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.peopledatalabs.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

PeopleDataLabsNode = build_rest_node(MANIFEST)
