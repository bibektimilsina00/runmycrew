"""Google Contacts polling trigger — built from a manifest via the
polling scaffold. Ops, output shape, cursor strategies, and scheduler
binding are unchanged from the previous hand-written class; the
implementation moved into `trigger_manifest.py` plus the scaffold in
`apps/api/app/node_system/scaffolds/`."""

from apps.api.app.node_system.nodes.google.gpeople.trigger_manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_polling_trigger

GooglePeopleTriggerNode = build_polling_trigger(MANIFEST)
