"""AWS Secrets Manager action node — built from a manifest via the REST scaffold."""

from apps.api.app.node_system.nodes.aws_secrets_manager.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSSecretsManagerNode = build_rest_node(MANIFEST)
