"""Azure DevOps action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.microsoft.azure_devops.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AzureDevOpsNode = build_rest_node(MANIFEST)
