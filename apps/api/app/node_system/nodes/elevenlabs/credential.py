"""API-key credential provider for elevenlabs.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="elevenlabs_api_key",
    name="ElevenLabs",
    icon_slug="elevenlabs",
    color="#ffffff",
    description="High-quality text-to-speech with voice cloning",
    hint="API Key",
    fields=[CredentialField(id="api_key", label="API Key", type="password", placeholder="API Key")],
)
