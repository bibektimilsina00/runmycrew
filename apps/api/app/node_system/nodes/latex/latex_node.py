"""LaTeX (latexonline.cc) action node — built via the REST scaffold."""

from apps.api.app.node_system.nodes.latex.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

LatexNode = build_rest_node(MANIFEST)
