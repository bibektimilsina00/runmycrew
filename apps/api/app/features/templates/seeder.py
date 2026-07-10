"""Import the on-disk seed JSON templates into the marketplace DB table.

Runs on every app startup; idempotent — upserts by slug. Marks every
imported row `is_official=True` with `creator_id=NULL` so the
marketplace UI can show them under an "Official" badge alongside
community-published templates.
"""

from __future__ import annotations

import logging
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .models import Template
from .registry import TemplateRegistry
from .service import _prepare_graph_snapshot, _slugify

logger = logging.getLogger(__name__)


# Rotates over the existing inspo-bg-N CSS classes so the seeded
# templates inherit varied card backgrounds without us having to
# annotate each JSON file. Cycle order is deterministic, keyed by id.
_BG_VARIANTS = ["inspo-bg-1", "inspo-bg-2", "inspo-bg-3"]


async def seed_official_templates(db: AsyncSession) -> int:
    """Sync `seeds/**/*.json` into the `template` table.

    Insert new seeds, resync existing official rows, AND delete official
    rows whose seed JSON was removed from disk (so a renamed/dropped
    seed file doesn't leave an orphan in the marketplace). Returns the
    insert count on this run.
    """
    registry = TemplateRegistry()
    inserted = 0
    seen_slugs: set[str] = set()

    for idx, raw in enumerate(registry.all()):
        slug = _slug_for(raw)
        seen_slugs.add(slug)
        result = await db.execute(select(Template).where(Template.slug == slug))
        existing = result.scalar_one_or_none()
        graph = _extract_graph(raw)
        creds_required = list(raw.get("credentials_required") or [])
        # Same derivation the publish flow uses — one source of truth
        # for what counts as an integration. Scrub is a no-op on
        # hand-authored seeds (no credential ids in them).
        _, _, tools_required = _prepare_graph_snapshot(graph)

        if existing is not None:
            # Keep authoring-time fields (graph, summary, description,
            # credentials, tools, pricing, featured) in sync with the seed
            # JSON so edits to the source file take effect on next boot
            # without manual DB ops. Only touches `is_official` rows so a
            # community-published template that happens to share a slug
            # wouldn't be silently overwritten.
            if existing.is_official:
                existing.title = str(raw.get("name") or existing.title)
                existing.summary = str(raw.get("summary") or existing.summary)
                existing.description = str(
                    raw.get("description") or raw.get("summary") or existing.description
                )
                existing.category = str(raw.get("category") or existing.category)
                existing.kind = str(raw.get("kind") or existing.kind)
                existing.graph = graph
                existing.credentials_required = creds_required
                existing.tools_required = tools_required
                existing.is_premium = bool(raw.get("is_premium", False))
                existing.price_cents = int(raw.get("price_cents", 0) or 0)
                existing.featured = bool(raw.get("featured", False))
            continue

        db.add(
            Template(
                creator_id=None,
                workspace_id=None,
                slug=slug,
                title=str(raw.get("name") or slug),
                summary=str(raw.get("summary") or ""),
                description=str(raw.get("description") or raw.get("summary") or ""),
                category=str(raw.get("category") or "loops"),
                kind=str(raw.get("kind") or "agent"),
                graph=graph,
                credentials_required=creds_required,
                tools_required=tools_required,
                bg_variant=_BG_VARIANTS[idx % len(_BG_VARIANTS)],
                is_published=True,
                is_official=True,
                is_premium=bool(raw.get("is_premium", False)),
                price_cents=int(raw.get("price_cents", 0) or 0),
                featured=bool(raw.get("featured", False)),
            )
        )
        inserted += 1

    # Drop official rows whose seed JSON is gone from disk — keeps the
    # marketplace mirror of seeds/ exact. Community-published rows
    # (is_official=False) are never touched.
    stale = await db.execute(
        select(Template).where(Template.is_official.is_(True))  # type: ignore[union-attr]
    )
    removed = 0
    for row in stale.scalars().all():
        if row.slug not in seen_slugs:
            await db.delete(row)
            removed += 1

    await db.commit()
    if inserted:
        logger.info("template seeder: imported %d official template(s)", inserted)
    if removed:
        logger.info("template seeder: pruned %d orphan official row(s)", removed)
    return inserted


def _slug_for(raw: dict[str, Any]) -> str:
    """Prefer the JSON's explicit id (already slug-ish), fall back to the
    sluggified name. Keeps the seeded ids stable across reboots."""
    raw_id = str(raw.get("id") or "").strip()
    if raw_id:
        return _slugify(raw_id)
    return _slugify(str(raw.get("name") or "template"))


def _extract_graph(raw: dict[str, Any]) -> dict[str, Any]:
    workflow = raw.get("workflow") or {}
    graph = workflow.get("graph") if isinstance(workflow, dict) else None
    if isinstance(graph, dict):
        return graph
    # Older seed format: graph directly at the top level.
    if isinstance(raw.get("graph"), dict):
        return raw["graph"]
    return {"nodes": [], "edges": []}
