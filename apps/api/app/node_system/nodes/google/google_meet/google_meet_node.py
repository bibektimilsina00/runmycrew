"""Google Meet action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google.google_meet.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GoogleMeetNode = build_rest_node(MANIFEST)
