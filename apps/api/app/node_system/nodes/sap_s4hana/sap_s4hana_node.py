"""SAP S/4HANA Cloud action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.sap_s4hana.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SAPS4HANANode = build_rest_node(MANIFEST)
