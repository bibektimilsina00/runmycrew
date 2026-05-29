import json
import uuid
from typing import Any

import httpx
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.credential_manager.api_keys import get_ai_provider
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
from apps.api.app.features.credentials.repository import CredentialRepository
from apps.api.app.features.users.models import User

logger = get_logger(__name__)


class AIService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_models(
        self,
        provider_id: str,
        current_user: User,
        credential: str | None = None,
    ) -> tuple[bool, list[dict[str, str]], str | None]:
        selected_credential = credential

        if not selected_credential:
            return False, [], "Select a provider credential to load models."

        try:
            api_key = await self._get_api_key_for_credential(
                current_user, selected_credential, provider_id
            )
            if not api_key:
                return False, [], "Selected credential does not contain an API key."

            fetched_options = await self._fetch_provider_models(provider_id, api_key)
            return True, fetched_options, None
        except Exception as e:
            logger.warning(f"Failed to fetch {provider_id} models: {e}")
            return False, [], str(e)

    async def _get_api_key_for_credential(
        self, current_user: User, credential: str, provider: str
    ) -> str | None:
        ai_provider = get_ai_provider(provider)
        if not ai_provider:
            return None

        credential_type = ai_provider.id
        repo = CredentialRepository(self.db)
        cred = await repo.get_by_id_and_user(uuid.UUID(credential), current_user.id)
        if not cred or cred.type != credential_type:
            return None

        encryption_service = AESEncryptionService()
        decrypted_data = json.loads(encryption_service.decrypt(cred.encrypted_data))
        api_key = decrypted_data.get("api_key")
        return api_key if isinstance(api_key, str) and api_key.strip() else None

    async def _fetch_provider_models(self, provider: str, api_key: str) -> list[dict[str, str]]:
        ai_provider = get_ai_provider(provider)
        if not ai_provider or not ai_provider.models_url:
            return []

        async with httpx.AsyncClient(timeout=10.0) as client:
            if ai_provider.ai_api_type == "openai_compatible":
                response = await client.get(
                    ai_provider.models_url,
                    headers={"Authorization": f"Bearer {api_key}"},
                )
                response.raise_for_status()
                return self._model_options_from_items(response.json().get("data", []))

            if ai_provider.ai_api_type == "anthropic":
                response = await client.get(
                    ai_provider.models_url,
                    headers={
                        "x-api-key": api_key,
                        "anthropic-version": "2023-06-01",
                    },
                )
                response.raise_for_status()
                return self._model_options_from_items(response.json().get("data", []))

            if ai_provider.ai_api_type == "google":
                response = await client.get(
                    ai_provider.models_url,
                    params={"key": api_key},
                )
                response.raise_for_status()
                return self._google_model_options(response.json().get("models", []))

        return []

    def _model_options_from_items(self, items: list[dict[str, Any]]) -> list[dict[str, str]]:
        options = []
        for item in items:
            model_id = item.get("id")
            if isinstance(model_id, str):
                display_name = item.get("display_name") or item.get("displayName")
                label = display_name if isinstance(display_name, str) and display_name else model_id
                options.append({"label": label, "value": model_id})
        return sorted(options, key=lambda option: option["label"])

    def _google_model_options(self, items: list[dict[str, Any]]) -> list[dict[str, str]]:
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


def get_ai_service(db: AsyncSession = Depends(get_db)) -> AIService:
    return AIService(db)
