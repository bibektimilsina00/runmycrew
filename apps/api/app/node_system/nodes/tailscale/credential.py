"""API-key credential provider for tailscale.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="tailscale_api_key",
    name="Tailscale",
    icon_slug="tailscale",
    color="#ffffff",
    description="Tailscale — devices, tags, ACLs for tailnets.",
    hint="Tailscale API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Tailscale API key"
        ),
    ],
)
