"""API-key credential provider for sendgrid.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="sendgrid_api_key",
    name="SendGrid",
    icon_slug="sendgrid",
    color="#ffffff",
    description="SendGrid — transactional + marketing email.",
    hint="SG....",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="SG....")],
)
