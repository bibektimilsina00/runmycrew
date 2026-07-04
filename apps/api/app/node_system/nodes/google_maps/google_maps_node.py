"""Google Maps action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google_maps.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GoogleMapsNode = build_rest_node(MANIFEST)
