"""API-key credential provider for similarweb.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="similarweb_api_key",
    name="SimilarWeb",
    icon_slug="similarweb",
    color="#ffffff",
    description="SimilarWeb — website + market intelligence.",
    hint="API key from SimilarWeb dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="SimilarWeb API key"
        ),
    ],
)
