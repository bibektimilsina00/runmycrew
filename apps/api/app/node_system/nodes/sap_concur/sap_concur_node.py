"""SAP Concur action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.sap_concur.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SAPConcurNode = build_rest_node(MANIFEST)
