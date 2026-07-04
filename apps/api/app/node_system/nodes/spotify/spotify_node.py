"""Spotify action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.spotify.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

SpotifyNode = build_rest_node(MANIFEST)
