"""API-key credential provider for instantly.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="instantly_api_key",
    name="Instantly",
    icon_slug="instantly",
    color="#ffffff",
    description="Instantly.ai — cold-email outreach + lead management.",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
