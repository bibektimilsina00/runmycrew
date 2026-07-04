"""Enrichment.io action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.enrichment.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

EnrichmentioNode = build_rest_node(MANIFEST)
