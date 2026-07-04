"""Customer.io action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.customer_io.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

CustomerIONode = build_rest_node(MANIFEST)
