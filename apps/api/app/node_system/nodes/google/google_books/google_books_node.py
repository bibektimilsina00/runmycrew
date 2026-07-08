"""Google Books action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google.google_books.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GoogleBooksNode = build_rest_node(MANIFEST)
