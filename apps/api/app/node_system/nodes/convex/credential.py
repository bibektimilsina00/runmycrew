"""API-key credential provider for convex.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="convex_api_key",
    name="Convex",
    icon_slug="convex",
    color="#ffffff",
    description="Convex — reactive backend / DB.",
    hint="Convex credentials",
    fields=[
        CredentialField(
            id="api_key", label="Deploy Key", type="password", placeholder="Deploy key"
        ),
        CredentialField(
            id="deployment_url",
            label="Deployment URL",
            type="string",
            placeholder="https://xxx.convex.cloud",
        ),
    ],
)
