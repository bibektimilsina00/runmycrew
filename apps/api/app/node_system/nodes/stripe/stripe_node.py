"""Stripe action node — built via the REST scaffold.

Previously a custom BaseNode with hand-rolled per-op dispatch. Now
declarative via `manifest.py`.
"""

from apps.api.app.node_system.nodes.stripe.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

StripeNode = build_rest_node(MANIFEST)
