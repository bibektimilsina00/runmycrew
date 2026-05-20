from __future__ import annotations

import json
import uuid
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.copilot.engine import run_copilot
from apps.api.app.core.database import get_db
from apps.api.app.credential_manager.api_keys import get_ai_provider, get_ai_providers
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
from apps.api.app.models.user import User
from apps.api.app.node_system.registry.registry import node_registry
from apps.api.app.repositories.copilot_session_repository import CopilotSessionRepository
from apps.api.app.repositories.credential_repository import CredentialRepository
from apps.api.app.repositories.workflow_repository import WorkflowRepository

router = APIRouter()

_PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
    "google": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
}

_COPILOT_SETTINGS_KEY = "__copilot_settings__"


class CopilotSettingsBody(BaseModel):
    provider: str = "anthropic"
    model: str = ""
    credential_id: str | None = None
    model_mode: str = "dynamic"  # "manual" | "dynamic"


class ChatMessage(BaseModel):
    role: str
    content: str


class CopilotChatRequest(BaseModel):
    messages: list[ChatMessage]
    graph: dict[str, Any] | None = None  # if None, load from DB
    provider: str = "anthropic"
    model: str | None = None
    credential_id: str | None = None
    session_id: str | None = None


@router.post("/{workflow_id}/chat")
async def copilot_chat(
    workflow_id: str,
    request: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> StreamingResponse:
    wf = await _get_workflow_or_404(workflow_id, current_user, db)

    # Resolve AI provider
    ai_provider = get_ai_provider(request.provider)
    if not ai_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported AI provider: '{request.provider}'. "
                   f"Supported: {[p.ai_provider_id for p in get_ai_providers() if p.ai_provider_id]}",
        )

    # Resolve API key
    api_key = await _resolve_api_key(
        provider=request.provider,
        credential_id=request.credential_id,
        credential_type=ai_provider.id,
        user=current_user,
        db=db,
    )
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"No credential found for provider '{request.provider}'. "
                   "Please add one in Settings → Credentials.",
        )

    model = request.model or _PROVIDER_DEFAULT_MODELS.get(request.provider, "")
    graph = request.graph if request.graph is not None else wf.graph
    messages = [{"role": m.role, "content": m.content} for m in request.messages]
    node_metadata = node_registry.list_nodes()

    async def generate():
        async for chunk in run_copilot(
            messages=messages,
            graph=graph,
            workflow_id=str(wf.id),
            api_key=api_key,
            ai_api_type=ai_provider.ai_api_type,
            chat_completions_url=ai_provider.chat_completions_url or "",
            model=model,
            node_metadata=node_metadata,
            db=db,
            session_id=request.session_id,
            user_id=str(current_user.id),
        ):
            yield chunk

    return StreamingResponse(
        generate(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",
            "Connection": "keep-alive",
        },
    )


@router.get("/{workflow_id}/settings")
async def get_copilot_settings(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopilotSettingsBody:
    wf = await _get_workflow_or_404(workflow_id, current_user, db)
    env = wf.env or {}
    raw = env.get(_COPILOT_SETTINGS_KEY)
    if raw:
        try:
            return CopilotSettingsBody(**json.loads(raw))
        except Exception:
            pass
    return CopilotSettingsBody()


@router.put("/{workflow_id}/settings")
async def update_copilot_settings(
    workflow_id: str,
    body: CopilotSettingsBody,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> CopilotSettingsBody:
    wf = await _get_workflow_or_404(workflow_id, current_user, db)
    env = dict(wf.env or {})
    env[_COPILOT_SETTINGS_KEY] = json.dumps(body.model_dump())
    repo = WorkflowRepository(db)
    await repo.update(wf, {"env": env})
    return body


@router.get("/{workflow_id}/sessions")
async def list_sessions(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    wf = await _get_workflow_or_404(workflow_id, current_user, db)
    session_repo = CopilotSessionRepository(db)
    sessions = await session_repo.list_by_workflow_and_user(wf.id, current_user.id)
    return {
        "sessions": [
            {
                "id": str(s.id),
                "title": s.title,
                "created_at": s.created_at.isoformat() if s.created_at else None,
                "updated_at": s.updated_at.isoformat() if s.updated_at else None,
            }
            for s in sessions
        ]
    }


@router.get("/{workflow_id}/sessions/{session_id}")
async def get_session(
    workflow_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    await _get_workflow_or_404(workflow_id, current_user, db)
    session_repo = CopilotSessionRepository(db)
    try:
        s = await session_repo.get_by_id_and_user(uuid.UUID(session_id), current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID")
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    return {
        "id": str(s.id),
        "title": s.title,
        "messages": s.messages or [],
        "created_at": s.created_at.isoformat() if s.created_at else None,
        "updated_at": s.updated_at.isoformat() if s.updated_at else None,
    }


@router.delete("/{workflow_id}/sessions/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(
    workflow_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    await _get_workflow_or_404(workflow_id, current_user, db)
    session_repo = CopilotSessionRepository(db)
    try:
        s = await session_repo.get_by_id_and_user(uuid.UUID(session_id), current_user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session ID")
    if not s:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found")
    await session_repo.delete(s)


@router.get("/providers")
async def list_copilot_providers(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """Return AI providers that have a stored credential for the current user."""
    cred_repo = CredentialRepository(db)
    user_creds = await cred_repo.list_by_user(current_user.id)
    user_cred_types = {c.type for c in user_creds}

    available = []
    for provider in get_ai_providers():
        if not provider.ai_provider_id:
            continue
        creds_for_provider = [
            {"id": str(c.id), "name": c.name}
            for c in user_creds
            if c.type == provider.id
        ]
        available.append({
            "id": provider.ai_provider_id,
            "name": provider.name,
            "credentialType": provider.id,
            "defaultModel": provider.default_model or _PROVIDER_DEFAULT_MODELS.get(provider.ai_provider_id, ""),
            "hasCredential": provider.id in user_cred_types,
            "credentials": creds_for_provider,
        })

    return {"providers": available}


# ── Helpers ──────────────────────────────────────────────────────────────────

async def _get_workflow_or_404(workflow_id: str, user: User, db: AsyncSession):
    repo = WorkflowRepository(db)
    try:
        wf = await repo.get_by_id_and_user(uuid.UUID(workflow_id), user.id)
    except ValueError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid workflow ID")
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return wf


async def _resolve_api_key(
    *,
    provider: str,
    credential_id: str | None,
    credential_type: str,
    user: User,
    db: AsyncSession,
) -> str | None:
    cred_repo = CredentialRepository(db)
    encryption = AESEncryptionService()

    # Prefer explicit credential ID
    if credential_id:
        try:
            cred = await cred_repo.get_by_id_and_user(uuid.UUID(credential_id), user.id)
        except ValueError:
            cred = None
        if cred:
            try:
                data = json.loads(encryption.decrypt(cred.encrypted_data))
                return data.get("api_key") or None
            except Exception:
                pass

    # Fall back to any credential of the right type
    cred = await cred_repo.get_by_type_and_user(credential_type, user.id)
    if cred:
        try:
            data = json.loads(encryption.decrypt(cred.encrypted_data))
            return data.get("api_key") or None
        except Exception:
            pass

    return None
