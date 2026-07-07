"""Brand-icon resolver.

Icons live in the backend node system, keyed by filename (the slug):

- ``node_system/nodes/<node>/<slug>.svg`` — colocated with a node, so adding
  a node + its icon is a single-folder change.
- ``node_system/icons/<slug>.svg`` — a shared drop-folder for brand icons that
  aren't tied to one node (integration credential logos, etc). Wins on a
  filename clash.

Drop a ``<slug>.svg`` in either place and the ``/icons/<slug>`` endpoint serves
it — no frontend change, no registry to edit. ``<slug>`` is the value the
frontend already asks for: a node's lowercase ``icon`` or a provider's
``icon_slug``.
"""

from functools import lru_cache
from pathlib import Path

_NODE_SYSTEM = Path(__file__).resolve().parents[2] / "node_system"


@lru_cache(maxsize=1)
def _icon_map() -> dict[str, str]:
    """slug -> absolute svg path. Built once per process (a deploy/restart
    picks up newly-added icons)."""
    mapping: dict[str, str] = {}
    nodes_dir = _NODE_SYSTEM / "nodes"
    if nodes_dir.is_dir():
        for svg in nodes_dir.glob("*/*.svg"):
            mapping.setdefault(svg.stem.lower(), str(svg))
    shared_dir = _NODE_SYSTEM / "icons"
    if shared_dir.is_dir():
        for svg in shared_dir.glob("*.svg"):
            mapping[svg.stem.lower()] = str(svg)  # shared drop-folder wins
    return mapping


def resolve_icon_path(slug: str) -> str | None:
    """Return the absolute path of ``<slug>.svg`` if it exists, else None."""
    return _icon_map().get(slug.lower())
