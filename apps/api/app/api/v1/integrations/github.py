import uuid

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.integrations.github.service import GitHubService
from apps.api.app.models.user import User
from apps.api.app.repositories.credential_repository import CredentialRepository
from apps.api.app.services.credential_service import CredentialService

logger = get_logger(__name__)
router = APIRouter()


async def get_github_service(
    credential: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> GitHubService:
    if not credential:
        raise HTTPException(status_code=400, detail="credential is required")

    repo = CredentialRepository(db)
    cred = await repo.get_by_id_and_user(uuid.UUID(credential), current_user.id)
    if not cred or cred.type != "github_oauth":
        raise HTTPException(status_code=404, detail="GitHub credential not found")

    credential_service = CredentialService(db)
    decrypted = await credential_service.get_decrypted_credential(cred)
    token = decrypted.get("access_token")
    if not token:
        raise HTTPException(status_code=400, detail="Access token missing in credential")

    return GitHubService(access_token=token)


@router.get("/repos")
async def list_github_repos(
    credential: str | None = Query(None),
    owner: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    try:
        service = await get_github_service(credential, db, current_user)

        if owner:
            # If owner provided, try to list repos for that org/user
            try:
                repos = await service._client.get(
                    f"/users/{owner}/repos",
                    params={"per_page": 100, "sort": "updated"},
                )
            except Exception:
                repos = await service.list_repos(per_page=100)
        else:
            repos = await service.list_repos(per_page=100)

        data = [{"label": r["name"], "value": r["name"]} for r in repos]
        return {"ok": True, "data": data}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to list GitHub repos: {e}")
        return {"ok": False, "error": str(e)}
