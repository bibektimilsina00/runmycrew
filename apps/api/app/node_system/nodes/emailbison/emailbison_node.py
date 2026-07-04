"""Emailbison action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.emailbison.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

EmailbisonNode = build_rest_node(MANIFEST)
