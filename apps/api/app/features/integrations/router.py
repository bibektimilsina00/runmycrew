from fastapi import APIRouter, Depends, Query

from apps.api.app.features.integrations.schemas import IntegrationResponse
from apps.api.app.features.integrations.service import IntegrationService, get_integration_service
from apps.api.app.features.users.models import User
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()


@router.get("/")
async def list_integrations():
    return []


@router.get("/slack/channels", response_model=IntegrationResponse)
async def list_slack_channels(
    credential: str | None = Query(None),
    bot_token: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    return await service.list_slack_channels(credential, bot_token, current_user)


@router.get("/slack/users", response_model=IntegrationResponse)
async def list_slack_users(
    credential: str | None = Query(None),
    bot_token: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    return await service.list_slack_users(credential, bot_token, current_user)


@router.get("/github/repos", response_model=IntegrationResponse)
async def list_github_repos(
    credential: str | None = Query(None),
    owner: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    return await service.list_github_repos(credential, owner, current_user)


@router.get("/notion/databases", response_model=IntegrationResponse)
async def list_notion_databases(
    credential: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: IntegrationService = Depends(get_integration_service),
):
    return await service.list_notion_databases(credential, current_user)
