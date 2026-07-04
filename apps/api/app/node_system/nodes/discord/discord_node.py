"""Discord action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.discord.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

DiscordNode = build_rest_node(MANIFEST)
