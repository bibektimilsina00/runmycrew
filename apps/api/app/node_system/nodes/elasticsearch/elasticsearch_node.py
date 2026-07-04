"""Elasticsearch action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.elasticsearch.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ElasticsearchNode = build_rest_node(MANIFEST)
