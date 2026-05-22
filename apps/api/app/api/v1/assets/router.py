import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.models.asset import Asset
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.schemas.asset import AssetOut, AssetStats, AssetUpdate
from apps.api.app.services.asset_service import AssetService

router = APIRouter()


def _asset_out(asset: Asset) -> AssetOut:
    return AssetOut(
        id=asset.id,
        workspace_id=asset.workspace_id,
        user_id=asset.user_id,
        name=asset.name,
        file_type=asset.file_type,
        file_size=asset.file_size,
        source_type=asset.source_type,
        created_at=asset.created_at,
        updated_at=asset.updated_at,
        url=f"/api/v1/assets/{asset.id}/view",
        download_url=f"/api/v1/assets/{asset.id}/download",
    )


@router.get("/", response_model=list[AssetOut])
async def list_assets(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    assets = await AssetService(db).list_assets(workspace)
    return [_asset_out(asset) for asset in assets]


@router.get("/stats", response_model=AssetStats)
async def get_asset_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    return await AssetService(db).get_stats(workspace)


@router.post("/upload", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    asset = await AssetService(db).upload_asset(file, current_user, workspace)
    return _asset_out(asset)


@router.patch("/{asset_id}", response_model=AssetOut)
async def update_asset(
    asset_id: uuid.UUID,
    data: AssetUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    asset = await AssetService(db).update_asset(asset_id, workspace, data)
    return _asset_out(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    await AssetService(db).delete_asset(asset_id, workspace)


@router.get("/{asset_id}/view")
async def view_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    asset = await AssetService(db).get_asset(asset_id, workspace)
    return FileResponse(asset.file_path, media_type=asset.file_type, filename=asset.name)


@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
):
    asset = await AssetService(db).get_asset(asset_id, workspace)
    return FileResponse(
        asset.file_path,
        media_type=asset.file_type,
        filename=asset.name,
        headers={"Content-Disposition": f'attachment; filename="{asset.name}"'},
    )
