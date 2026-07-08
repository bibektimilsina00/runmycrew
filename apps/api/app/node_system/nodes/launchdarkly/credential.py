"""API-key credential provider for launchdarkly.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="launchdarkly_api_key",
    name="LaunchDarkly",
    icon_slug="launchdarkly",
    color="#ffffff",
    description="LaunchDarkly — feature flags + segments.",
    hint="LaunchDarkly API access",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="LaunchDarkly API key"
        ),
    ],
)
