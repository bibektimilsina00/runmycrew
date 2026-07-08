"""API-key credential provider for video_generator.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="video_generator_api_key",
    name="Video Generator (Runway/HeyGen)",
    icon_slug="video_generator",
    color="#1c1c1c",
    description="Runway Gen-3 video generation — text/image → video.",
    hint="Video Generator (Runway/HeyGen) API access",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key / Bearer Token",
            type="password",
            placeholder="Video Generator (Runway/HeyGen) API key",
        ),
    ],
)
