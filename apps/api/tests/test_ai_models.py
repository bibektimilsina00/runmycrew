import pytest

from apps.api.app.api.v1.ai.router import (
    MODEL_PROVIDERS,
    _google_model_options,
    _model_options_from_items,
    list_ai_models,
)


@pytest.fixture
def anyio_backend() -> str:
    return "asyncio"


def test_ai_model_providers_cover_supported_agent_providers():
    assert {"openai", "anthropic", "google", "groq"} == MODEL_PROVIDERS


def test_openai_compatible_model_options_are_sorted_and_labeled_by_id():
    options = _model_options_from_items(
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
    options = _google_model_options(
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
    assert _model_options_from_items([]) == []
    assert _google_model_options([]) == []


@pytest.mark.anyio
async def test_list_ai_models_requires_selected_credential_for_dynamic_fetch():
    result = await list_ai_models(
        provider="openai",
        credential=None,
        openaiCredential=None,
        anthropicCredential=None,
        googleCredential=None,
        groqCredential=None,
    )

    assert result == {
        "ok": False,
        "data": [],
        "error": "Select a provider credential to load models.",
    }
