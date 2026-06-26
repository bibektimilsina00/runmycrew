"""Airtable node — built from a manifest via the REST scaffold.

The behavior, ops, and output shape are unchanged from the previous
hand-written class; the implementation moved into `manifest.py` plus
the scaffold in `apps/api/app/node_system/scaffolds/`. Kept this file
as the public entry point so existing imports (`from
…airtable.airtable_node import AirtableNode`) keep working without
touching the registry on every port.
"""

from apps.api.app.node_system.nodes.airtable.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AirtableNode = build_rest_node(MANIFEST)
