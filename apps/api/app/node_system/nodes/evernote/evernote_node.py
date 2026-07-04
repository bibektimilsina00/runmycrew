"""Evernote action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.evernote.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

EvernoteNode = build_rest_node(MANIFEST)
