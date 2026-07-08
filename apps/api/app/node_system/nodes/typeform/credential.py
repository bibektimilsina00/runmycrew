"""API-key credential provider for typeform.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="typeform_api_key",
    name="Typeform",
    icon_slug="typeform",
    color="#ffffff",
    description="Typeform — forms, responses, webhooks.",
    hint="Personal Access Token",
    fields=[
        CredentialField(id="api_key", label="Access Token", type="password", placeholder="Token")
    ],
)
