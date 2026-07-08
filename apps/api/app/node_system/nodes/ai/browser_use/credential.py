"""API-key credential provider for browser_use.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="browser_use_api_key",
    name="Browser Use",
    icon_slug=None,
    color="#ffffff",
    description="Browser Use — AI-powered browser automation via browser-use.com",
    hint="bu-...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="bu-...")],
)
