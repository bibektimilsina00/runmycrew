"""API-key credential provider for google_translate.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="google_translate_api_key",
    name="Google Translate",
    icon_slug="google_translate",
    color="#ffffff",
    description="Google Translate — translate text between languages.",
    hint="Google Translate API key",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Google Translate API key",
        ),
    ],
)
