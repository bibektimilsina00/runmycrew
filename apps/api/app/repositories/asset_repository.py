import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.models.asset import Asset


class AssetRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_by_workspace(self, workspace_id: uuid.UUID) -> list[Asset]:
        result = await self.db.execute(
            select(Asset)
            .where(Asset.workspace_id == workspace_id)
            .order_by(Asset.created_at.desc())
        )
        return list(result.scalars().all())

    async def get_by_id_and_workspace(
        self, asset_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> Asset | None:
        result = await self.db.execute(
            select(Asset).where(Asset.id == asset_id, Asset.workspace_id == workspace_id)
        )
        return result.scalar_one_or_none()

    async def stats_by_workspace(self, workspace_id: uuid.UUID) -> tuple[int, int]:
        result = await self.db.execute(
            select(func.count(Asset.id), func.coalesce(func.sum(Asset.file_size), 0)).where(
                Asset.workspace_id == workspace_id
            )
        )
        count, total_size = result.one()
        return int(count), int(total_size)

    async def create(self, asset: Asset) -> Asset:
        self.db.add(asset)
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def update_name(self, asset: Asset, name: str) -> Asset:
        asset.name = name
        await self.db.commit()
        await self.db.refresh(asset)
        return asset

    async def delete(self, asset: Asset) -> None:
        await self.db.delete(asset)
        await self.db.commit()
