"""Microsoft Teams action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.microsoft_teams.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MicrosoftTeamsNode = build_rest_node(MANIFEST)
