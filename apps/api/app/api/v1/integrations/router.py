from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.integrations.github import router as github_router
from apps.api.app.api.v1.integrations.notion import router as notion_router
from apps.api.app.api.v1.integrations.slack import router as slack_router
from apps.api.app.core.database import get_db

router = APIRouter()

router.include_router(slack_router, prefix="/slack", tags=["integrations"])
router.include_router(github_router, prefix="/github", tags=["integrations"])
router.include_router(notion_router, prefix="/notion", tags=["integrations"])


@router.get("/")
async def list_integrations(db: AsyncSession = Depends(get_db)):
    return []
