"""AWS Textract action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.textract.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSTextractNode = build_rest_node(MANIFEST)
