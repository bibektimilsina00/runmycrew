import json
import uuid
from typing import Any

import httpx
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
from apps.api.app.models.user import User
from apps.api.app.repositories.credential_repository import CredentialRepository

router = APIRouter()
logger = get_logger(__name__)

MODEL_PROVIDERS = {"openai", "anthropic", "google", "groq"}

PROVIDER_CREDENTIAL_TYPES = {
    "openai": "openai_api_key",
    "anthropic": "anthropic_api_key",
    "google": "google_api_key",
    "groq": "groq_api_key",
}


@router.get("/")
async def ai_status():
    return {"status": "ok"}


@router.get("/models")
async def list_ai_models(
    provider: str = Query("openai"),
    credential: str | None = Query(None),
    openaiCredential: str | None = Query(None),
    anthropicCredential: str | None = Query(None),
    googleCredential: str | None = Query(None),
    groqCredential: str | None = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    provider_id = provider if provider in MODEL_PROVIDERS else "openai"
    selected_credential = credential or {
        "openai": openaiCredential,
        "anthropic": anthropicCredential,
        "google": googleCredential,
        "groq": groqCredential,
    }[provider_id]

    if not selected_credential:
        return {
            "ok": False,
            "data": [],
            "error": "Select a provider credential to load models.",
        }

    try:
        api_key = await _get_api_key_for_credential(db, current_user, selected_credential, provider_id)
        if not api_key:
            return {
                "ok": False,
                "data": [],
                "error": "Selected credential does not contain an API key.",
            }

        fetched_options = await _fetch_provider_models(provider_id, api_key)
        return {"ok": True, "data": fetched_options}
    except Exception as e:
        logger.warning(f"Failed to fetch {provider_id} models: {e}")
        return {"ok": False, "data": [], "error": str(e)}


async def _get_api_key_for_credential(
    db: AsyncSession, current_user: User, credential: str, provider: str
) -> str | None:
    credential_type = PROVIDER_CREDENTIAL_TYPES[provider]
    repo = CredentialRepository(db)
    cred = await repo.get_by_id_and_user(uuid.UUID(credential), current_user.id)
    if not cred or cred.type != credential_type:
        return None

    encryption_service = AESEncryptionService()
    decrypted_data = json.loads(encryption_service.decrypt(cred.encrypted_data))
    api_key = decrypted_data.get("api_key")
    return api_key if isinstance(api_key, str) and api_key.strip() else None


async def _fetch_provider_models(provider: str, api_key: str) -> list[dict[str, str]]:
    async with httpx.AsyncClient(timeout=10.0) as client:
        if provider == "openai":
            response = await client.get(
                "https://api.openai.com/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            return _model_options_from_items(response.json().get("data", []))

        if provider == "groq":
            response = await client.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
            )
            response.raise_for_status()
            return _model_options_from_items(response.json().get("data", []))

        if provider == "anthropic":
            response = await client.get(
                "https://api.anthropic.com/v1/models",
                headers={
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01",
                },
            )
            response.raise_for_status()
            return _model_options_from_items(response.json().get("data", []))

        if provider == "google":
            response = await client.get(
                "https://generativelanguage.googleapis.com/v1beta/models",
                params={"key": api_key},
            )
            response.raise_for_status()
            return _google_model_options(response.json().get("models", []))

    return []


def _model_options_from_items(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    options = []
    for item in items:
        model_id = item.get("id")
        if isinstance(model_id, str):
            display_name = item.get("display_name") or item.get("displayName")
            label = display_name if isinstance(display_name, str) and display_name else model_id
            options.append({"label": label, "value": model_id})
    return sorted(options, key=lambda option: option["label"])


def _google_model_options(items: list[dict[str, Any]]) -> list[dict[str, str]]:
    options = []
    for item in items:
        model_name = item.get("name")
        if not isinstance(model_name, str):
            continue
        model_id = model_name.removeprefix("models/")
        display_name = item.get("displayName")
        label = display_name if isinstance(display_name, str) and display_name else model_id
        options.append({"label": label, "value": model_id})
    return sorted(options, key=lambda option: option["label"])
