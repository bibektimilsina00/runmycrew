import shutil
import uuid
from pathlib import Path

from fastapi import Depends, HTTPException, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import logger
from apps.api.app.features.assets.models import Asset
from apps.api.app.features.assets.repository import AssetRepository
from apps.api.app.features.assets.schemas import AssetStats, AssetUpdate
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace

UPLOAD_DIR = Path("uploads/assets")


class AssetService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = AssetRepository(db)

    async def list_assets(self, workspace: Workspace) -> list[Asset]:
        return await self.repo.list_by_workspace(workspace.id)

    async def get_asset(self, asset_id: uuid.UUID, workspace: Workspace) -> Asset:
        asset = await self.repo.get_by_id_and_workspace(asset_id, workspace.id)
        if asset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        return asset

    async def get_asset_unscoped(self, asset_id: uuid.UUID) -> Asset:
        """Fetch an asset by id without a workspace check.

        ONLY callable from the signed public URL handler — the HMAC over
        `(asset_id, exp)` is the authorization that takes the place of the
        workspace filter. Don't expose this from other surfaces.
        """
        asset = await self.repo.get_by_id(asset_id)
        if asset is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Asset not found")
        return asset

    async def get_stats(self, workspace: Workspace) -> AssetStats:
        count, total_size = await self.repo.stats_by_workspace(workspace.id)
        return AssetStats(count=count, total_size=total_size)

    async def upload_asset(self, file: UploadFile, user: User, workspace: Workspace) -> Asset:
        asset_id = uuid.uuid4()
        original_name = Path(file.filename or "upload").name
        extension = Path(original_name).suffix
        workspace_dir = UPLOAD_DIR / str(workspace.id)
        workspace_dir.mkdir(parents=True, exist_ok=True)
        file_path = workspace_dir / f"{asset_id}{extension}"

        try:
            with file_path.open("wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except OSError as exc:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Could not save file.",
            ) from exc

        asset = Asset(
            id=asset_id,
            workspace_id=workspace.id,
            user_id=user.id,
            name=original_name,
            file_path=str(file_path),
            file_type=file.content_type or "application/octet-stream",
            file_size=file_path.stat().st_size,
            source_type="uploaded",
        )
        return await self.repo.create(asset)

    async def update_asset(
        self, asset_id: uuid.UUID, workspace: Workspace, data: AssetUpdate
    ) -> Asset:
        asset = await self.get_asset(asset_id, workspace)
        return await self.repo.update_name(asset, data.name)

    async def delete_asset(self, asset_id: uuid.UUID, workspace: Workspace) -> None:
        asset = await self.get_asset(asset_id, workspace)
        path = Path(asset.file_path)
        await self.repo.delete(asset)
        try:
            path.unlink(missing_ok=True)
        except OSError as exc:
            logger.warning("Failed to remove asset file %s: %s", path, exc)


def get_asset_service(db: AsyncSession = Depends(get_db)) -> AssetService:
    return AssetService(db)
