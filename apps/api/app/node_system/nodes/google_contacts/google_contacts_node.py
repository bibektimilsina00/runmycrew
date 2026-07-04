"""Google Contacts action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.google_contacts.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GoogleContactsNode = build_rest_node(MANIFEST)
