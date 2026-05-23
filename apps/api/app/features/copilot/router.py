from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import StreamingResponse

from apps.api.app.features.copilot.engine_core.engine import run_copilot
from apps.api.app.features.copilot.schemas import (
    CopilotChatRequest,
    CopilotProvidersResponse,
    CopilotSettingsBody,
    SessionDetailResponse,
    SessionListResponse,
)
from apps.api.app.features.copilot.service import CopilotService, get_copilot_service
from apps.api.app.features.credentials.manager.api_keys import get_ai_provider, get_ai_providers
from apps.api.app.features.users.models import User
from apps.api.app.node_system.registry.registry import node_registry
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()

_PROVIDER_DEFAULT_MODELS: dict[str, str] = {
    "openai": "gpt-4o-mini",
    "anthropic": "claude-haiku-4-5-20251001",
    "google": "gemini-2.5-flash",
    "groq": "llama-3.3-70b-versatile",
}


@router.post("/{workflow_id}/chat")
async def copilot_chat(
    workflow_id: str,
    request: CopilotChatRequest,
    current_user: User = Depends(get_current_user),
    service: CopilotService = Depends(get_copilot_service),
) -> StreamingResponse:
    wf = await service.get_workflow_or_404(workflow_id, current_user)

    # Resolve AI provider
    ai_provider = get_ai_provider(request.provider)
    if not ai_provider:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported AI provider: '{request.provider}'. "
            f"Supported: {[p.ai_provider_id for p in get_ai_providers() if p.ai_provider_id]}",
        )

    # Resolve API key
    api_key = await service.resolve_api_key(
        provider=request.provider,
        credential_id=request.credential_id,
        credential_type=ai_provider.id,
        user=current_user,
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
            db=service.db,
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


@router.get("/{workflow_id}/settings", response_model=CopilotSettingsBody)
async def get_copilot_settings(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    service: CopilotService = Depends(get_copilot_service),
) -> CopilotSettingsBody:
    return await service.get_settings(workflow_id, current_user)


@router.put("/{workflow_id}/settings", response_model=CopilotSettingsBody)
async def update_copilot_settings(
    workflow_id: str,
    body: CopilotSettingsBody,
    current_user: User = Depends(get_current_user),
    service: CopilotService = Depends(get_copilot_service),
) -> CopilotSettingsBody:
    return await service.update_settings(workflow_id, body, current_user)


@router.get("/{workflow_id}/sessions", response_model=SessionListResponse)
async def list_sessions(
    workflow_id: str,
    current_user: User = Depends(get_current_user),
    service: CopilotService = Depends(get_copilot_service),
) -> SessionListResponse:
    return await service.list_sessions(workflow_id, current_user)


@router.get("/{workflow_id}/sessions/{session_id}", response_model=SessionDetailResponse)
async def get_session(
    workflow_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: CopilotService = Depends(get_copilot_service),
) -> SessionDetailResponse:
    return await service.get_session(workflow_id, session_id, current_user)


@router.delete(
    "/{workflow_id}/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def delete_session(
    workflow_id: str,
    session_id: str,
    current_user: User = Depends(get_current_user),
    service: CopilotService = Depends(get_copilot_service),
) -> None:
    await service.delete_session(workflow_id, session_id, current_user)


@router.get("/providers", response_model=CopilotProvidersResponse)
async def list_copilot_providers(
    current_user: User = Depends(get_current_user),
    service: CopilotService = Depends(get_copilot_service),
) -> CopilotProvidersResponse:
    return await service.list_providers(current_user)
