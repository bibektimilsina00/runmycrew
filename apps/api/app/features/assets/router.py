import uuid

from fastapi import APIRouter, Depends, File, Response, UploadFile, status
from fastapi.responses import FileResponse

from apps.api.app.features.assets.models import Asset
from apps.api.app.features.assets.schemas import AssetOut, AssetStats, AssetUpdate
from apps.api.app.features.assets.service import AssetService, get_asset_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

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
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: AssetService = Depends(get_asset_service),
):
    assets = await service.list_assets(workspace)
    return [_asset_out(asset) for asset in assets]


@router.get("/stats", response_model=AssetStats)
async def get_asset_stats(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: AssetService = Depends(get_asset_service),
):
    return await service.get_stats(workspace)


@router.post("/upload", response_model=AssetOut, status_code=status.HTTP_201_CREATED)
async def upload_asset(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: AssetService = Depends(get_asset_service),
):
    asset = await service.upload_asset(file, current_user, workspace)
    return _asset_out(asset)


@router.patch("/{asset_id}", response_model=AssetOut)
async def update_asset(
    asset_id: uuid.UUID,
    data: AssetUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: AssetService = Depends(get_asset_service),
):
    asset = await service.update_asset(asset_id, workspace, data)
    return _asset_out(asset)


@router.delete("/{asset_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: AssetService = Depends(get_asset_service),
):
    await service.delete_asset(asset_id, workspace)


@router.get("/{asset_id}/view")
async def view_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: AssetService = Depends(get_asset_service),
):
    asset = await service.get_asset(asset_id, workspace)
    return FileResponse(asset.file_path, media_type=asset.file_type, filename=asset.name)


@router.get("/{asset_id}/download")
async def download_asset(
    asset_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: AssetService = Depends(get_asset_service),
):
    asset = await service.get_asset(asset_id, workspace)
    return FileResponse(
        asset.file_path,
        media_type=asset.file_type,
        filename=asset.name,
        headers={"Content-Disposition": f'attachment; filename="{asset.name}"'},
    )
