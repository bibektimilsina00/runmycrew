import json
import uuid

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.copilot.repository import CopilotSessionRepository
from apps.api.app.features.copilot.schemas import (
    CopilotCredential,
    CopilotProvider,
    CopilotProvidersResponse,
    CopilotSettingsBody,
    SessionDetailResponse,
    SessionItem,
    SessionListResponse,
)
from apps.api.app.features.credentials.manager.api_keys import get_ai_providers
from apps.api.app.features.credentials.manager.encryption.aes import AESEncryptionService
from apps.api.app.features.credentials.repository import CredentialRepository
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.repository import WorkflowRepository

_PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
    "google": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
}

_COPILOT_SETTINGS_KEY = "__copilot_settings__"


class CopilotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.workflow_repo = WorkflowRepository(db)
        self.session_repo = CopilotSessionRepository(db)
        self.cred_repo = CredentialRepository(db)

    async def get_workflow_or_404(self, workflow_id: str, user: User):
        try:
            wf = await self.workflow_repo.get_by_id_and_user(uuid.UUID(workflow_id), user.id)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID"
            ) from err
        if not wf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        return wf

    async def resolve_api_key(
        self,
        *,
        provider: str,
        credential_id: str | None,
        credential_type: str,
        user: User,
    ) -> str | None:
        encryption = AESEncryptionService()

        # Prefer explicit credential ID
        if credential_id:
            try:
                cred = await self.cred_repo.get_by_id_and_user(uuid.UUID(credential_id), user.id)
            except ValueError:
                cred = None
            if cred:
                try:
                    data = json.loads(encryption.decrypt(cred.encrypted_data))
                    return data.get("api_key") or None
                except Exception:
                    pass

        # Fall back to any credential of the right type
        cred = await self.cred_repo.get_by_type_and_user(credential_type, user.id)
        if cred:
            try:
                data = json.loads(encryption.decrypt(cred.encrypted_data))
                return data.get("api_key") or None
            except Exception:
                pass

        return None

    async def get_settings(self, workflow_id: str, user: User) -> CopilotSettingsBody:
        wf = await self.get_workflow_or_404(workflow_id, user)
        env = wf.env or {}
        raw = env.get(_COPILOT_SETTINGS_KEY)
        if raw:
            try:
                return CopilotSettingsBody(**json.loads(raw))
            except Exception:
                pass
        return CopilotSettingsBody()

    async def update_settings(
        self, workflow_id: str, body: CopilotSettingsBody, user: User
    ) -> CopilotSettingsBody:
        wf = await self.get_workflow_or_404(workflow_id, user)
        env = dict(wf.env or {})
        env[_COPILOT_SETTINGS_KEY] = json.dumps(body.model_dump())
        await self.workflow_repo.update(wf, {"env": env})
        return body

    async def list_sessions(self, workflow_id: str, user: User) -> SessionListResponse:
        wf = await self.get_workflow_or_404(workflow_id, user)
        sessions = await self.session_repo.list_by_workflow_and_user(wf.id, user.id)
        return SessionListResponse(
            sessions=[
                SessionItem(
                    id=str(s.id),
                    title=s.title,
                    created_at=s.created_at.isoformat() if s.created_at else None,
                    updated_at=s.updated_at.isoformat() if s.updated_at else None,
                )
                for s in sessions
            ]
        )

    async def get_session(
        self, workflow_id: str, session_id: str, user: User
    ) -> SessionDetailResponse:
        await self.get_workflow_or_404(workflow_id, user)
        try:
            s = await self.session_repo.get_by_id_and_user(uuid.UUID(session_id), user.id)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
            ) from err
        if not s:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        return SessionDetailResponse(
            id=str(s.id),
            title=s.title,
            messages=s.messages or [],
            created_at=s.created_at.isoformat() if s.created_at else None,
            updated_at=s.updated_at.isoformat() if s.updated_at else None,
        )

    async def delete_session(self, workflow_id: str, session_id: str, user: User) -> None:
        await self.get_workflow_or_404(workflow_id, user)
        try:
            s = await self.session_repo.get_by_id_and_user(uuid.UUID(session_id), user.id)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID"
            ) from err
        if not s:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
        await self.session_repo.delete(s)

    async def list_providers(self, user: User) -> CopilotProvidersResponse:
        user_creds = await self.cred_repo.list_by_user(user.id)
        user_cred_types = {c.type for c in user_creds}

        available = []
        for provider in get_ai_providers():
            if not provider.ai_provider_id:
                continue
            creds_for_provider = [
                CopilotCredential(id=str(c.id), name=c.name)
                for c in user_creds
                if c.type == provider.id
            ]
            available.append(
                CopilotProvider(
                    id=provider.ai_provider_id,
                    name=provider.name,
                    credentialType=provider.id,
                    defaultModel=provider.default_model
                    or _PROVIDER_DEFAULT_MODELS.get(provider.ai_provider_id, ""),
                    hasCredential=provider.id in user_cred_types,
                    credentials=creds_for_provider,
                )
            )

        return CopilotProvidersResponse(providers=available)


def get_copilot_service(db: AsyncSession = Depends(get_db)) -> CopilotService:
    return CopilotService(db)
