"""API-key credential provider for resend.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="resend_api_key",
    name="Resend",
    icon_slug="resend",
    color="#1c1c1c",
    description="Resend — transactional email API.",
    hint="re_...",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="re_...")],
)
