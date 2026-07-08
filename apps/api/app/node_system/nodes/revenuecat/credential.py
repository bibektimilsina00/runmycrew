"""API-key credential provider for revenuecat.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="revenuecat_api_key",
    name="RevenueCat",
    icon_slug="revenuecat",
    color="#ffffff",
    description="RevenueCat — subscribers, entitlements, offerings.",
    hint="RevenueCat API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="RevenueCat API key"
        ),
    ],
)
