"""API-key credential provider for vercel.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="vercel_api_key",
    name="Vercel",
    icon_slug="vercel",
    color="#1c1c1c",
    description="Vercel — deployments, projects, env vars, domains.",
    hint="Personal Access Token",
    fields=[
        CredentialField(id="api_key", label="Access Token", type="password", placeholder="Token")
    ],
)
