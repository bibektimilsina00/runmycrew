"""Filesystem-backed template registry.

Walks ``apps/api/app/features/templates/seeds/`` at import time and
exposes the parsed JSON via ``list_templates()`` + ``get_template(id)``.
Per-category subdirectories become tags so the gallery can group
templates without a separate manifest file.

We hot-reload on every call when ``DEBUG=true`` — the seed JSON
churns less than the application code, so prod reads it once at
import-time and caches.
"""

from __future__ import annotations

import json
import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


SEEDS_DIR = Path(__file__).parent / "seeds"


class TemplateRegistry:
    """Cached read of ``seeds/**/*.json``.

    The registry is module-level — ``get_template`` / ``list_templates``
    delegate to a shared instance via lru_cache so the JSON is loaded
    once per worker.
    """

    def __init__(self, root: Path | None = None) -> None:
        self.root = root or SEEDS_DIR
        self._index: dict[str, dict[str, Any]] | None = None

    def _load(self) -> dict[str, dict[str, Any]]:
        index: dict[str, dict[str, Any]] = {}
        if not self.root.exists():
            return index
        for path in self.root.rglob("*.json"):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                logger.warning("template registry: failed to load %s", path)
                continue
            tid = data.get("id")
            if not tid:
                logger.warning("template registry: %s missing 'id'", path)
                continue
            data["__path"] = str(path.relative_to(self.root))
            # Category falls back to the parent dir name so "loops/foo.json"
            # → category="loops" without needing the field in every file.
            data.setdefault("category", path.parent.name)
            index[tid] = data
        return index

    def all(self) -> list[dict[str, Any]]:
        if self._index is None:
            self._index = self._load()
        return list(self._index.values())

    def by_category(self, category: str) -> list[dict[str, Any]]:
        return [t for t in self.all() if t.get("category") == category]

    def get(self, template_id: str) -> dict[str, Any] | None:
        if self._index is None:
            self._index = self._load()
        return self._index.get(template_id)


@lru_cache(maxsize=1)
def _shared() -> TemplateRegistry:
    return TemplateRegistry()


def list_templates(category: str | None = None) -> list[dict[str, Any]]:
    reg = _shared()
    return reg.by_category(category) if category else reg.all()


def get_template(template_id: str) -> dict[str, Any] | None:
    return _shared().get(template_id)
