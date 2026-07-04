"""Google Slides action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google_slides.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GoogleSlidesNode = build_rest_node(MANIFEST)
