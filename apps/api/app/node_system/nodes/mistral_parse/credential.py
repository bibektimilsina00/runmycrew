"""API-key credential provider for mistral_parse.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mistral_api_key",
    name="Mistral OCR",
    icon_slug="mistral_parse",
    color="#ffffff",
    description="Mistral OCR — document parsing to markdown / structured data.",
    hint="API key from Mistral OCR dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Mistral OCR API key"
        ),
    ],
)
