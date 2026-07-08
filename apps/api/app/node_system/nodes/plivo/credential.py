"""API-key credential provider for plivo.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="plivo_api_key",
    name="Plivo",
    icon_slug="plivo",
    color="#1c1c1c",
    description="Plivo — SMS and voice. Auth ID + Auth Token.",
    hint="Auth ID + Auth Token",
    fields=[
        CredentialField(id="auth_id", label="Auth ID", type="string", placeholder="MA..."),
        CredentialField(
            id="auth_token", label="Auth Token", type="password", placeholder="Auth Token"
        ),
    ],
)
