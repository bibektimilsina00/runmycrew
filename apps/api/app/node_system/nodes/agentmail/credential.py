"""API-key credential provider for agentmail.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="agentmail_api_key",
    name="AgentMail",
    icon_slug="agentmail",
    color="#ffffff",
    description="AgentMail — AI email agent (send, receive, thread).",
    hint="API key from AgentMail dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="AgentMail API key"
        ),
    ],
)
