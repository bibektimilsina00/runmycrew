"""API-key credential provider for posthog.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="posthog_api_key",
    name="PostHog",
    icon_slug="posthog",
    color="#ffffff",
    description="PostHog — product analytics + feature flags.",
    hint="phx_...",
    fields=[
        CredentialField(
            id="api_key", label="Personal API Key", type="password", placeholder="phx_..."
        )
    ],
)
