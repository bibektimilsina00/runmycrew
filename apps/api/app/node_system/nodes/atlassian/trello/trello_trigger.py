"""Trello polling trigger — built via the polling scaffold."""

from apps.api.app.node_system.nodes.atlassian.trello.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

TrelloTriggerNode = build_polling_trigger(MANIFEST)
