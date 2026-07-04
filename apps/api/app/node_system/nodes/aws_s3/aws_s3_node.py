"""AWS S3 action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.aws_s3.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSS3Node = build_rest_node(MANIFEST)
