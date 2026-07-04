"""Microsoft Entra ID action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.microsoft_ad.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MicrosoftEntraNode = build_rest_node(MANIFEST)
