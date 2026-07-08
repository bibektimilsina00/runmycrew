"""API-key credential provider for cloudflare.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="cloudflare_api_key",
    name="Cloudflare",
    icon_slug="cloudflare",
    color="#ffffff",
    description="Cloudflare — zones, DNS, cache, workers via scoped API token.",
    hint="API Token (scoped, not the global key)",
    fields=[CredentialField(id="api_key", label="API Token", type="password", placeholder="Token")],
)
