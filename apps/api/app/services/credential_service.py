import json
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any

from fastapi import HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.credential_manager.encryption.aes import encryption_service
from apps.api.app.credential_manager.oauth.flow import get_oauth_provider
from apps.api.app.models.credential import Credential
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.repositories.credential_repository import CredentialRepository

REFRESH_SKEW = timedelta(minutes=5)


class CredentialService:
    def __init__(self, db: AsyncSession):
        self.repo = CredentialRepository(db)

    async def list_credentials(self, user: User, workspace: Workspace) -> list[Credential]:
        return await self.repo.list_by_workspace(workspace.id)

    async def store_credential(
        self,
        name: str,
        type: str,
        data: dict,
        user: User,
        workspace: Workspace,
        meta: dict | None = None,
    ) -> Credential:
        encrypted_data = encryption_service.encrypt(json.dumps(data))
        credential = Credential(
            user_id=user.id,
            workspace_id=workspace.id,
            name=name,
            type=type,
            encrypted_data=encrypted_data,
            meta=meta,
        )
        return await self.repo.create(credential)

    async def get_decrypted(self, credential_id: uuid.UUID, user: User, workspace: Workspace) -> dict:
        credential = await self.repo.get_by_id_and_workspace(credential_id, workspace.id)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found",
            )
        return await self.get_decrypted_credential(credential)

    async def get_decrypted_credential(self, credential: Credential) -> dict[str, Any]:
        data = self._decrypt_credential(credential)
        return await self._refresh_if_needed(credential, data)

    async def get_decrypted_by_type(self, credential_type: str, user_id: uuid.UUID) -> dict | None:
        """Used by execution engine to inject credentials into NodeContext."""
        # For execution engine, we might need a fresh session or use the one provided
        # Here we assume the service is initialized with a session
        credential = await self.repo.get_by_type_and_user(credential_type, user_id)
        if not credential:
            return None
        return await self.get_decrypted_credential(credential)

    async def list_decrypted_for_user(self, user_id: uuid.UUID) -> list[dict[str, Any]]:
        credentials = await self.repo.list_by_user(user_id)
        return await self._decrypt_credentials(credentials)

    async def list_decrypted_for_workspace(self, workspace_id: uuid.UUID) -> list[dict[str, Any]]:
        credentials = await self.repo.list_by_workspace(workspace_id)
        return await self._decrypt_credentials(credentials)

    async def _decrypt_credentials(self, credentials: list[Credential]) -> list[dict[str, Any]]:
        decrypted: list[dict[str, Any]] = []
        for credential in credentials:
            data = await self.get_decrypted_credential(credential)
            decrypted.append({"id": str(credential.id), "type": credential.type, "data": data})
        return decrypted

    async def delete_credential(self, credential_id: uuid.UUID, user: User, workspace: Workspace) -> None:
        credential = await self.repo.get_by_id_and_workspace(credential_id, workspace.id)
        if not credential:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Credential not found",
            )
        await self.repo.delete(credential)

    def _decrypt_credential(self, credential: Credential) -> dict[str, Any]:
        decrypted_json = encryption_service.decrypt(credential.encrypted_data)
        return json.loads(decrypted_json)

    def _oauth_provider_name(self, credential_type: str) -> str | None:
        if not credential_type.endswith("_oauth"):
            return None
        return credential_type.removesuffix("_oauth")

    def _parse_expires_at(self, value: Any) -> datetime | None:
        if not isinstance(value, str) or not value:
            return None
        try:
            parsed = datetime.fromisoformat(value)
        except ValueError:
            return None
        if parsed.tzinfo is None:
            return parsed.replace(tzinfo=UTC)
        return parsed.astimezone(UTC)

    def _should_refresh(self, data: dict[str, Any]) -> bool:
        if not data.get("refresh_token"):
            return False
        expires_at = self._parse_expires_at(data.get("expires_at"))
        if expires_at is None:
            return False
        return expires_at <= datetime.now(UTC) + REFRESH_SKEW

    async def _refresh_if_needed(
        self,
        credential: Credential,
        data: dict[str, Any],
    ) -> dict[str, Any]:
        if not self._should_refresh(data):
            return data

        provider_name = self._oauth_provider_name(credential.type)
        provider = get_oauth_provider(provider_name) if provider_name else None
        if not provider or not hasattr(provider, "refresh_access_token"):
            return data

        refreshed = await provider.refresh_access_token(data["refresh_token"])
        merged = {
            **data,
            **{key: value for key, value in refreshed.items() if value is not None},
        }
        credential.encrypted_data = encryption_service.encrypt(json.dumps(merged))
        credential.meta = {
            **(credential.meta or {}),
            "expires_at": merged.get("expires_at"),
            "refresh_token_expires_at": merged.get("refresh_token_expires_at"),
        }
        await self.repo.update(credential)
        return merged
