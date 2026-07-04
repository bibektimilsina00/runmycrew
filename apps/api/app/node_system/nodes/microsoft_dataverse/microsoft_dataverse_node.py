"""Microsoft Dataverse action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.microsoft_dataverse.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MicrosoftDataverseNode = build_rest_node(MANIFEST)
