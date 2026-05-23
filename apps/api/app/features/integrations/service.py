import uuid

from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.features.credentials.repository import CredentialRepository
from apps.api.app.features.credentials.service import CredentialService
from apps.api.app.features.integrations.schemas import IntegrationOption, IntegrationResponse
from apps.api.app.features.users.models import User
from apps.api.app.integrations.github.service import GitHubService
from apps.api.app.integrations.notion.service import NotionService
from apps.api.app.integrations.slack.service import SlackService

logger = get_logger(__name__)


class IntegrationService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_github_service(self, credential: str | None, current_user: User) -> GitHubService:
        if not credential:
            raise HTTPException(status_code=400, detail="credential is required")

        repo = CredentialRepository(self.db)
        cred = await repo.get_by_id_and_user(uuid.UUID(credential), current_user.id)
        if not cred or cred.type != "github_oauth":
            raise HTTPException(status_code=404, detail="GitHub credential not found")

        credential_service = CredentialService(self.db)
        decrypted = await credential_service.get_decrypted_credential(cred)
        token = decrypted.get("access_token")
        if not token:
            raise HTTPException(status_code=400, detail="Access token missing in credential")

        return GitHubService(access_token=token)

    async def get_notion_service(self, credential: str | None, current_user: User) -> NotionService:
        if not credential:
            raise HTTPException(status_code=400, detail="credential is required")

        repo = CredentialRepository(self.db)
        cred = await repo.get_by_id_and_user(uuid.UUID(credential), current_user.id)
        if not cred or cred.type not in ("notion_api_key", "notion_oauth"):
            raise HTTPException(status_code=404, detail="Notion credential not found")

        credential_service = CredentialService(self.db)
        decrypted = await credential_service.get_decrypted_credential(cred)
        api_key = decrypted.get("access_token") or decrypted.get("api_key")
        if not api_key:
            raise HTTPException(status_code=400, detail="Access token missing in credential")

        return NotionService(api_key=api_key)

    async def get_slack_service(
        self, credential: str | None, bot_token: str | None, current_user: User
    ) -> SlackService:
        if bot_token:
            return SlackService(access_token=bot_token)

        if credential:
            repo = CredentialRepository(self.db)
            cred = await repo.get_by_id_and_user(uuid.UUID(credential), current_user.id)
            if not cred or cred.type != "slack_oauth":
                raise HTTPException(status_code=404, detail="Slack credential not found")

            credential_service = CredentialService(self.db)
            decrypted_data = await credential_service.get_decrypted_credential(cred)
            token = decrypted_data.get("access_token")
            if not token:
                raise HTTPException(status_code=400, detail="Access token missing in credential")

            return SlackService(access_token=token)

        raise HTTPException(
            status_code=400, detail="Either credential_id or bot_token must be provided"
        )

    async def list_slack_channels(
        self, credential: str | None, bot_token: str | None, current_user: User
    ) -> IntegrationResponse:
        try:
            service = await self.get_slack_service(credential, bot_token, current_user)
            data = await service.list_channels(limit=1000)
            if not data.get("ok"):
                return IntegrationResponse(ok=False, error=data.get("error"))

            channels = [
                IntegrationOption(label=f"#{c['name']}", value=c["id"])
                for c in data.get("channels", [])
            ]
            return IntegrationResponse(ok=True, data=channels)
        except Exception as e:
            logger.error(f"Failed to list slack channels: {e}")
            return IntegrationResponse(ok=False, error=str(e))

    async def list_slack_users(
        self, credential: str | None, bot_token: str | None, current_user: User
    ) -> IntegrationResponse:
        try:
            service = await self.get_slack_service(credential, bot_token, current_user)
            data = await service.list_users(limit=1000)
            if not data.get("ok"):
                return IntegrationResponse(ok=False, error=data.get("error"))

            users = [
                IntegrationOption(label=f"@{u.get('real_name') or u['name']}", value=u["id"])
                for u in data.get("members", [])
                if not u.get("deleted") and not u.get("is_bot")
            ]
            return IntegrationResponse(ok=True, data=users)
        except Exception as e:
            logger.error(f"Failed to list slack users: {e}")
            return IntegrationResponse(ok=False, error=str(e))

    async def list_github_repos(
        self, credential: str | None, owner: str | None, current_user: User
    ) -> IntegrationResponse:
        try:
            service = await self.get_github_service(credential, current_user)

            if owner:
                try:
                    repos = await service._client.get(
                        f"/users/{owner}/repos",
                        params={"per_page": 100, "sort": "updated"},
                    )
                except Exception:
                    repos = await service.list_repos(per_page=100)
            else:
                repos = await service.list_repos(per_page=100)

            data = [IntegrationOption(label=r["name"], value=r["name"]) for r in repos]
            return IntegrationResponse(ok=True, data=data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to list GitHub repos: {e}")
            return IntegrationResponse(ok=False, error=str(e))

    async def list_notion_databases(
        self, credential: str | None, current_user: User
    ) -> IntegrationResponse:
        try:
            service = await self.get_notion_service(credential, current_user)
            databases = await service.list_databases()

            data = []
            for db_item in databases:
                title_parts = db_item.get("title", [])
                name = "".join(t.get("plain_text", "") for t in title_parts) or "Untitled"
                data.append(IntegrationOption(label=name, value=db_item["id"].replace("-", "")))

            return IntegrationResponse(ok=True, data=data)
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Failed to list Notion databases: {e}")
            return IntegrationResponse(ok=False, error=str(e))


def get_integration_service(db: AsyncSession = Depends(get_db)) -> IntegrationService:
    return IntegrationService(db)
