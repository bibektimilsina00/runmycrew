"""API-key credential provider for dspy.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="dspy_api_key",
    name="DSPy Cloud",
    icon_slug="dspy",
    color="#ffffff",
    description="DSPy Cloud — prompt-program hosting + evaluation.",
    hint="API key from DSPy Cloud dashboard",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="DSPy Cloud API key"
        ),
    ],
)
