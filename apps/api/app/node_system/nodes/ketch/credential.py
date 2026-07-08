"""API-key credential provider for ketch.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="ketch_api_key",
    name="Ketch",
    icon_slug="ketch",
    color="#ffffff",
    description="Ketch — privacy consent, DSAR (data subject access requests).",
    hint="Ketch API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Ketch API key"
        ),
    ],
)
