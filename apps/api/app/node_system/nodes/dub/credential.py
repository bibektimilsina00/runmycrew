"""API-key credential provider for dub.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="dub_api_key",
    name="Dub",
    icon_slug="dub",
    color="#1c1c1c",
    description="Dub.co — short links + click analytics.",
    hint="dub_...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="dub_...")],
)
