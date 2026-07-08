"""API-key credential provider for google_maps.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="google_maps_api_key",
    name="Google Maps",
    icon_slug="google_maps",
    color="#ffffff",
    description="Google Maps — geocoding, places, distance matrix.",
    hint="Google Maps API key",
    fields=[
        CredentialField(
            id="api_key", label="API Key", type="password", placeholder="Google Maps API key"
        ),
    ],
)
