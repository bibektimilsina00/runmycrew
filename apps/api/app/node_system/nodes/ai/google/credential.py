"""API-key credential provider for google.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="google_api_key",
    name="Google Gemini",
    icon_slug="google-gemini",
    color="#1c1c1c",
    description="Gemini 1.5 Pro, Gemini 1.5 Flash",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
    ai_provider_id="google",
    default_model="gemini-1.5-flash",
    supports_tools=True,
    supports_response_format=True,
    ai_api_type="google",
    chat_completions_url="https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
    models_url="https://generativelanguage.googleapis.com/v1beta/models",
)
