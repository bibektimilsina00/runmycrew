"""GitHub action node — built via the REST scaffold.

Previously a custom BaseNode with hand-rolled per-op dispatch through
`GitHubService`. Refactored to declarative scaffold — endpoint mapping
lives in `manifest.py`, execution goes through `build_rest_node`.
`GitHubService` stays in `apps/api/app/integrations/github/` for use
by feature-layer callers (settings screens, admin flows).
"""

from apps.api.app.node_system.nodes.github.manifest import MANIFEST
from apps.api.app.node_system.scaffolds import build_rest_node

GitHubNode = build_rest_node(MANIFEST)
