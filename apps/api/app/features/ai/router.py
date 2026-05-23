from fastapi import APIRouter, Depends, Query

from apps.api.app.features.ai.schemas import (
    AIModelResponse,
    AIProviderData,
    AIProviderResponse,
    AIStatusResponse,
)
from apps.api.app.features.ai.service import AIService, get_ai_service
from apps.api.app.features.credentials.manager.api_keys import (
    get_ai_provider_ids,
    get_ai_providers,
)
from apps.api.app.features.users.models import User
from apps.api.app.shared.dependencies import get_current_user

router = APIRouter()


@router.get("/", response_model=AIStatusResponse)
async def ai_status():
    return AIStatusResponse(status="ok")


@router.get("/providers", response_model=AIProviderResponse)
async def list_ai_providers():
    providers = []
    for provider in get_ai_providers():
        providers.append(
            AIProviderData(
                label=provider.name,
                value=provider.ai_provider_id,
                credentialType=provider.id,
                defaultModel=provider.default_model,
                supportsTools=provider.supports_tools,
                supportsResponseFormat=provider.supports_response_format,
                apiType=provider.ai_api_type,
            )
        )
    return AIProviderResponse(ok=True, data=providers)


@router.get("/models", response_model=AIModelResponse)
async def list_ai_models(
    provider: str = Query("openai"),
    credential: str | None = Query(None),
    current_user: User = Depends(get_current_user),
    service: AIService = Depends(get_ai_service),
):
    provider_id = provider if provider in get_ai_provider_ids() else "openai"

    ok, options, error = await service.get_models(
        provider_id=provider_id,
        current_user=current_user,
        credential=credential,
    )

    return AIModelResponse(ok=ok, data=options, error=error)
