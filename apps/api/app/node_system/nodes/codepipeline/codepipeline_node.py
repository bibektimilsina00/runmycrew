"""AWS CodePipeline action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.codepipeline.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

AWSCodePipelineNode = build_rest_node(MANIFEST)
