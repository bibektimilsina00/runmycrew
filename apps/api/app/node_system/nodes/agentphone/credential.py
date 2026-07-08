"""API-key credential provider for agentphone.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="agentphone_api_key",
    name="AgentPhone",
    icon_slug="agentphone",
    color="#ffffff",
    description="AgentPhone — AI voice agent (make/receive calls).",
    hint="API key from AgentPhone dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="AgentPhone API key"
        ),
    ],
)
