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

from pathlib import Path

_NODE_SYSTEM = Path(__file__).resolve().parents[2] / "node_system"


_EXTS = (".svg", ".png", ".webp", ".jpg", ".jpeg")


def resolve_icon_path(slug: str) -> str | None:
    """Return the absolute path of ``<slug>.<ext>`` if it exists, else None.

    SVG preferred, but any of ``.svg .png .webp .jpg .jpeg`` matches — a
    raster brand logo (e.g. Clearbit PNG) drops in the same way. Rescans
    on every call — no cache. A dropped-in file shows up on the next
    request, no restart needed. Cost is one directory walk per icon
    fetch; icons are hit once per node card and the whole tree is ~250
    files so this stays well under a millisecond.
    """
    slug = slug.lower()
    for ext in _EXTS:
        # Colocated icon (`nodes/<any>/<slug>.<ext>`) — rglob covers folders
        # that nest 2+ levels deep (`nodes/db/mysql/mysql.svg`).
        for hit in (_NODE_SYSTEM / "nodes").rglob(f"{slug}{ext}"):
            return str(hit)
        # Shared drop folder (`node_system/icons/<slug>.<ext>`).
        shared = _NODE_SYSTEM / "icons" / f"{slug}{ext}"
        if shared.is_file():
            return str(shared)
    return None
