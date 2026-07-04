"""New Relic action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.new_relic.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

NewRelicNode = build_rest_node(MANIFEST)
