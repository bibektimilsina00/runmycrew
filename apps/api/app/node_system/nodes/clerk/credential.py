"""API-key credential provider for clerk.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="clerk_api_key",
    name="Clerk",
    icon_slug="clerk",
    color="#ffffff",
    description="Clerk — user + org management (dev-first auth).",
    hint="Clerk API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Clerk API key"
        ),
    ],
)
