"""Template + TemplatePurchase repository.

DB access only — all business rules (creator-only update, premium gate,
graph scrubbing) live in `service.py`.
"""

from __future__ import annotations

from typing import Literal
from uuid import UUID

from sqlalchemy import func, or_, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.users.models import User

from .models import Template, TemplatePurchase

SortKey = Literal["newest", "popular", "price-low", "price-high"]


class TemplateRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    # ── Reads ────────────────────────────────────────────────────────

    async def get_by_id(self, template_id: UUID) -> Template | None:
        return (
            await self.db.execute(select(Template).where(Template.id == template_id))
        ).scalar_one_or_none()

    async def get_by_slug(self, slug: str) -> Template | None:
        return (
            await self.db.execute(select(Template).where(Template.slug == slug))
        ).scalar_one_or_none()

    async def fetch_creators(self, templates: list[Template]) -> dict[UUID, User]:
        """Batched lookup of creators for a result set."""
        ids = {t.creator_id for t in templates if t.creator_id is not None}
        if not ids:
            return {}
        stmt = select(User).where(User.id.in_(ids))
        rows = (await self.db.execute(stmt)).scalars().all()
        return {u.id: u for u in rows}

    async def fetch_creator(self, template: Template) -> User | None:
        if template.creator_id is None:
            return None
        return await self.db.get(User, template.creator_id)

    async def list_published(
        self,
        *,
        category: str | None = None,
        kind: str | None = None,
        q: str | None = None,
        sort: SortKey = "newest",
        limit: int = 24,
        offset: int = 0,
        official_only: bool = False,
    ) -> tuple[list[Template], int]:
        """Paginated marketplace list.

        Always filters to ``is_published=True`` — drafts only show up via
        ``list_by_creator``. ``official_only=True`` further restricts to
        rows seeded from disk (used by the anonymous marketing endpoint
        so user-published rows don't surface there before moderation).
        The total count is computed in a separate scalar query so the
        caller can render "Showing X of N" without a second round trip.
        """
        base = select(Template).where(Template.is_published.is_(True))
        if official_only:
            base = base.where(Template.is_official.is_(True))
        if category:
            base = base.where(Template.category == category)
        if kind:
            base = base.where(Template.kind == kind)
        if q:
            needle = f"%{q.lower().strip()}%"
            base = base.where(
                or_(
                    func.lower(Template.title).like(needle),
                    func.lower(Template.summary).like(needle),
                    func.lower(Template.description).like(needle),
                )
            )

        # Stable sort: primary key tie-break by id keeps pagination
        # deterministic when two rows share a sort value (e.g. equal
        # download_count).
        if sort == "popular":
            base = base.order_by(Template.download_count.desc(), Template.id)
        elif sort == "price-low":
            base = base.order_by(Template.price_cents.asc(), Template.id)
        elif sort == "price-high":
            base = base.order_by(Template.price_cents.desc(), Template.id)
        else:
            base = base.order_by(Template.created_at.desc(), Template.id)

        count_stmt = select(func.count()).select_from(base.subquery())
        total = (await self.db.execute(count_stmt)).scalar_one()

        rows_stmt = base.limit(limit).offset(offset)
        rows = list((await self.db.execute(rows_stmt)).scalars().all())
        return rows, total

    async def list_by_creator(self, creator_id: UUID) -> list[Template]:
        stmt = (
            select(Template)
            .where(Template.creator_id == creator_id)
            .order_by(Template.created_at.desc())
        )
        return list((await self.db.execute(stmt)).scalars().all())

    async def category_counts(self) -> dict[str, int]:
        stmt = (
            select(Template.category, func.count(Template.id))
            .where(Template.is_published.is_(True))
            .group_by(Template.category)
        )
        rows = (await self.db.execute(stmt)).all()
        return {row[0]: row[1] for row in rows}

    async def slug_exists(self, slug: str) -> bool:
        stmt = select(Template.id).where(Template.slug == slug).limit(1)
        return (await self.db.execute(stmt)).scalar_one_or_none() is not None

    # ── Writes ───────────────────────────────────────────────────────

    async def create(self, template: Template) -> Template:
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def update(self, template: Template) -> Template:
        self.db.add(template)
        await self.db.commit()
        await self.db.refresh(template)
        return template

    async def delete(self, template: Template) -> None:
        await self.db.delete(template)
        await self.db.commit()

    async def increment_download(self, template_id: UUID) -> None:
        """Atomic UPDATE … SET download_count = download_count + 1.

        SQL-level increment avoids the read-modify-write race that would
        let two concurrent installs both observe the pre-increment value.
        """
        await self.db.execute(
            update(Template)
            .where(Template.id == template_id)
            .values(download_count=Template.download_count + 1)
        )
        await self.db.commit()


class TemplatePurchaseRepository:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db

    async def is_owned_by(self, template_id: UUID, user_id: UUID) -> bool:
        stmt = (
            select(TemplatePurchase.id)
            .where(TemplatePurchase.template_id == template_id)
            .where(TemplatePurchase.user_id == user_id)
            .limit(1)
        )
        return (await self.db.execute(stmt)).scalar_one_or_none() is not None

    async def record(self, purchase: TemplatePurchase) -> TemplatePurchase:
        self.db.add(purchase)
        await self.db.commit()
        await self.db.refresh(purchase)
        return purchase
