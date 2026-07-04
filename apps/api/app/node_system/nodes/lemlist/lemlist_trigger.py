"""Lemlist polling trigger — built via the polling scaffold."""

from apps.api.app.node_system.nodes.lemlist.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

LemlistTriggerNode = build_polling_trigger(MANIFEST)
