"""incident.io action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.incidentio.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

IncidentIONode = build_rest_node(MANIFEST)
