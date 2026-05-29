import pytest

from apps.api.app.credential_manager.api_keys import get_ai_provider_ids
from apps.api.app.features.ai.router import (
    list_ai_models,
    list_ai_providers,
)
from apps.api.app.features.ai.service import AIService


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_ai_model_providers_cover_supported_agent_providers():
    assert {
        "openai",
        "anthropic",
        "google",
        "groq",
        "openrouter",
        "deepseek",
        "mistral",
        "xai",
        "together",
        "fireworks",
    } == get_ai_provider_ids()


@pytest.mark.anyio
async def test_list_ai_providers_uses_api_key_catalog():
    response = await list_ai_providers()
    result = response.model_dump()

    assert result["ok"] is True
    assert {provider["value"] for provider in result["data"]} == {
        "openai",
        "anthropic",
        "google",
        "groq",
        "openrouter",
        "deepseek",
        "mistral",
        "xai",
        "together",
        "fireworks",
    }
    assert {provider["value"]: provider["credentialType"] for provider in result["data"]} == {
        "openai": "openai_api_key",
        "anthropic": "anthropic_api_key",
        "google": "google_api_key",
        "groq": "groq_api_key",
        "openrouter": "openrouter_api_key",
        "deepseek": "deepseek_api_key",
        "mistral": "mistral_api_key",
        "xai": "xai_api_key",
        "together": "together_api_key",
        "fireworks": "fireworks_api_key",
    }


def test_openai_compatible_model_options_are_sorted_and_labeled_by_id():
    ai_service = AIService(None)
    options = ai_service._model_options_from_items(
        [
            {"id": "z-model"},
            {"id": "a-model", "display_name": "A Model"},
            {"name": "ignored"},
        ]
    )

    assert options == [
        {"label": "A Model", "value": "a-model"},
        {"label": "z-model", "value": "z-model"},
    ]


def test_google_model_options_remove_models_prefix():
    ai_service = AIService(None)
    options = ai_service._google_model_options(
        [
            {"name": "models/gemini-1.5-flash", "displayName": "Gemini 1.5 Flash"},
            {"name": "models/gemini-1.5-pro"},
        ]
    )

    assert options == [
        {"label": "Gemini 1.5 Flash", "value": "gemini-1.5-flash"},
        {"label": "gemini-1.5-pro", "value": "gemini-1.5-pro"},
    ]


def test_model_options_can_be_empty_without_static_fallback():
    ai_service = AIService(None)
    assert ai_service._model_options_from_items([]) == []
    assert ai_service._google_model_options([]) == []


@pytest.mark.anyio
async def test_list_ai_models_requires_selected_credential_for_dynamic_fetch():
    response = await list_ai_models(
        provider="openai",
        credential=None,
        current_user=None,
        service=AIService(None),
    )
    result = response.model_dump()

    assert result == {
        "ok": False,
        "data": [],
        "error": "Select a provider credential to load models.",
    }
