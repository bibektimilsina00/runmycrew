"""API-key credential provider for reducto.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="reducto_api_key",
    name="Reducto",
    icon_slug="reducto",
    color="#ffffff",
    description="Reducto — high-fidelity document parsing.",
    hint="API key from Reducto dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Reducto API key"
        ),
    ],
)
