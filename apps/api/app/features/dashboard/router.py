from __future__ import annotations

from fastapi import APIRouter, Depends

from apps.api.app.features.dashboard.schemas import DashboardStatsResponse
from apps.api.app.features.dashboard.service import DashboardService, get_dashboard_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


@router.get("/stats", response_model=DashboardStatsResponse)
async def get_dashboard_stats(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: DashboardService = Depends(get_dashboard_service),
):
    return await service.get_dashboard_stats(current_user, workspace)
