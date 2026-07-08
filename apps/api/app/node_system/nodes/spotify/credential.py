"""API-key credential provider for spotify.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="spotify_api_key",
    name="Spotify",
    icon_slug="spotify",
    color="#ffffff",
    description="Spotify — playback, playlists, tracks, artist metadata.",
    hint="Spotify API access",
    fields=[
        CredentialField(
            id="api_key",
            label="API Key / Bearer Token",
            type="password",
            placeholder="Spotify API key",
        ),
    ],
)
