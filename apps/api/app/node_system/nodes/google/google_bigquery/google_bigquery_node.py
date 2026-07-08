"""Google BigQuery action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google.google_bigquery.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GoogleBigQueryNode = build_rest_node(MANIFEST)
