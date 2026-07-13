import json
import uuid
from typing import Any

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.api_keys import get_ai_providers
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
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
from apps.api.app.features.credentials.repository import CredentialRepository
from apps.api.app.features.crews.repository import CrewRepository
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.repository import WorkflowRepository

logger = get_logger(__name__)

_PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
    "google": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
}

# Per-provider Settings field checked when the user has no stored credential —
# Settings loads these from the root .env (see core/config.py). Lets the Copilot
# run against a shared/dev key without provisioning credentials per user.
_PROVIDER_SETTINGS_KEYS: dict[str, str] = {
    "openai": "OPENAI_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "google": "GEMINI_API_KEY",
    "groq": "GROQ_API_KEY",
}

_COPILOT_SETTINGS_KEY = "__copilot_settings__"


class CopilotService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.workflow_repo = WorkflowRepository(db)
        self.crew_repo = CrewRepository(db)
        self.session_repo = CopilotSessionRepository(db)
        self.cred_repo = CredentialRepository(db)

    async def get_workflow_or_404(self, workflow_id: str, user: User):
        """Back-compat: workflow-only resolution."""
        entity, kind = await self.resolve_target(workflow_id, user)
        if kind != "workflow":
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
        return entity

    async def resolve_target(self, target_id: str, user: User) -> tuple[Any, str]:
        """Resolve a copilot target that may be a workflow OR a crew the user
        owns. Returns (entity, kind) where kind is "workflow" | "crew".
        Copilot builds crews with the same graph tools it uses for workflows —
        crews are just graphs of a different `kind`."""
        try:
            tid = uuid.UUID(target_id)
        except ValueError as err:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid id"
            ) from err
        wf = await self.workflow_repo.get_by_id_and_user(tid, user.id)
        if wf:
            return wf, "workflow"
        crew = await self.crew_repo.get_by_id(tid)
        if crew and crew.user_id == user.id:
            return crew, "crew"
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Not found")

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
                except Exception:  # noqa: BLE001
                    logger.debug("copilot: pinned credential unusable, falling back", exc_info=True)

        # Fall back to any credential of the right type
        cred = await self.cred_repo.get_by_type_and_user(credential_type, user.id)
        if cred:
            try:
                data = json.loads(encryption.decrypt(cred.encrypted_data))
                return data.get("api_key") or None
            except Exception:  # noqa: BLE001
                logger.debug(
                    "copilot: type-matched credential unusable, falling back", exc_info=True
                )

        # Final fallback: a shared key from Settings (loaded from the root .env).
        settings_key = _PROVIDER_SETTINGS_KEYS.get(provider)
        if settings_key:
            fallback = getattr(settings, settings_key, "") or ""
            if fallback:
                return fallback

        return None

    async def get_settings(self, workflow_id: str, user: User) -> CopilotSettingsBody:
        entity, kind = await self.resolve_target(workflow_id, user)
        # Crews have no `env` column to store copilot prefs — serve defaults.
        if kind != "workflow":
            return CopilotSettingsBody()
        env = entity.env or {}
        raw = env.get(_COPILOT_SETTINGS_KEY)
        if raw:
            try:
                return CopilotSettingsBody(**json.loads(raw))
            except Exception:  # noqa: BLE001
                logger.warning(
                    "copilot: stored settings unreadable, serving defaults", exc_info=True
                )
        return CopilotSettingsBody()

    async def update_settings(
        self, workflow_id: str, body: CopilotSettingsBody, user: User
    ) -> CopilotSettingsBody:
        entity, kind = await self.resolve_target(workflow_id, user)
        # No env on crews — accept the settings but don't persist (the AI
        # build works on the default model regardless).
        if kind == "workflow":
            env = dict(entity.env or {})
            env[_COPILOT_SETTINGS_KEY] = json.dumps(body.model_dump())
            await self.workflow_repo.update(entity, {"env": env})
        return body

    async def list_sessions(self, workflow_id: str, user: User) -> SessionListResponse:
        entity, kind = await self.resolve_target(workflow_id, user)
        sessions = await self.session_repo.list_by_target_and_user(
            workflow_id=entity.id if kind == "workflow" else None,
            crew_id=entity.id if kind == "crew" else None,
            user_id=user.id,
        )
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
        await self.resolve_target(workflow_id, user)  # authorize workflow OR crew
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
        await self.resolve_target(workflow_id, user)  # authorize workflow OR crew
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
