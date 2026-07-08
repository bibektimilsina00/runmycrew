"""API-key credential provider for mixpanel.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mixpanel_api_key",
    name="Mixpanel",
    icon_slug="mixpanel",
    color="#ffffff",
    description="Mixpanel — event tracking + engagement queries.",
    hint="Service account username + secret (project token for ingestion)",
    fields=[
        CredentialField(
            id="username",
            label="Service Account Username",
            type="string",
            placeholder="serviceaccount.user",
        ),
        CredentialField(
            id="api_secret",
            label="Service Account Secret",
            type="password",
            placeholder="Secret",
        ),
    ],
)
