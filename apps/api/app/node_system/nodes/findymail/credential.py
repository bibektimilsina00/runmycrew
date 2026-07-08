"""API-key credential provider for findymail.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="findymail_api_key",
    name="Findymail",
    icon_slug="findymail",
    color="#ffffff",
    description="Findymail — verified B2B emails from name / LinkedIn.",
    hint="Bearer token from Findymail settings",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key",
            type="password",
            placeholder="Findymail API key",
        ),
    ],
)
