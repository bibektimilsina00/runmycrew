"""Apollo.io action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.apollo.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

ApolloNode = build_rest_node(MANIFEST)
