"""API-key credential provider for mailerlite.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mailerlite_api_key",
    name="MailerLite",
    icon_slug="mailerlite",
    color="#ffffff",
    description="MailerLite — subscribers, campaigns, automations.",
    hint="API Token",
    fields=[CredentialField(id="api_key", label="API Token", type="password", placeholder="Token")],
)
