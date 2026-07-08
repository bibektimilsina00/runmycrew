"""API-key credential provider for loops.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="loops_api_key",
    name="Loops",
    icon_slug="loops",
    color="#1c1c1c",
    description="Loops.so — product email + audience automation.",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
