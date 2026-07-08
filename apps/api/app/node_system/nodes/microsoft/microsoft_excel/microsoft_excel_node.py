"""Microsoft Excel action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.microsoft.microsoft_excel.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

MicrosoftExcelNode = build_rest_node(MANIFEST)
