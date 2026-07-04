"""Google Translate action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google_translate.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GoogleTranslateNode = build_rest_node(MANIFEST)
