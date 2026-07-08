"""API-key credential provider for twilio.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="twilio_api_key",
    name="Twilio",
    icon_slug="twilio",
    color="#ffffff",
    description="Twilio — SMS, WhatsApp, voice. Auth Token + Account SID.",
    hint="Account SID + Auth Token",
    fields=[
        CredentialField(
            id="account_sid",
            label="Account SID",
            type="string",
            placeholder="AC...",
        ),
        CredentialField(
            id="auth_token",
            label="Auth Token",
            type="password",
            placeholder="Auth Token",
        ),
    ],
)
