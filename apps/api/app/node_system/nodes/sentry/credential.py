"""API-key credential provider for sentry.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="sentry_api_key",
    name="Sentry",
    icon_slug="sentry",
    color="#ffffff",
    description="Sentry — error tracking + release management.",
    hint="Auth Token",
    fields=[
        CredentialField(id="api_key", label="Auth Token", type="password", placeholder="sntrys_...")
    ],
)
