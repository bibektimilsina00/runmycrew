import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.integrations.notion.service import NotionService
from apps.api.app.models.user import User
from apps.api.app.repositories.credential_repository import CredentialRepository
from apps.api.app.services.credential_service import CredentialService

logger = get_logger(__name__)
router = APIRouter()


async def get_notion_service(
    credential: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotionService:
    if not credential:
        raise HTTPException(status_code=400, detail="credential is required")

    repo = CredentialRepository(db)
    cred = await repo.get_by_id_and_user(uuid.UUID(credential), current_user.id)
    if not cred or cred.type not in ("notion_api_key", "notion_oauth"):
        raise HTTPException(status_code=404, detail="Notion credential not found")

    credential_service = CredentialService(db)
    decrypted = await credential_service.get_decrypted_credential(cred)
    api_key = decrypted.get("access_token") or decrypted.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Access token missing in credential")

    return NotionService(api_key=api_key)


@router.get("/databases")
async def list_notion_databases(
    credential: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service = await get_notion_service(credential, db, current_user)
        databases = await service.list_databases()

        data = []
        for db_item in databases:
            title_parts = db_item.get("title", [])
            name = "".join(t.get("plain_text", "") for t in title_parts) or "Untitled"
            data.append({"label": name, "value": db_item["id"].replace("-", "")})

        return {"ok": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list Notion databases: {e}")
        return {"ok": False, "error": str(e)}
