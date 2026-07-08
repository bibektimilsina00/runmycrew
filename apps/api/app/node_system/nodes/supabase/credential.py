"""API-key credential provider for supabase.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="supabase_api_key",
    name="Supabase",
    icon_slug="supabase",
    color="#ffffff",
    description="Supabase — read/write Postgres tables via PostgREST.",
    hint="Service role or anon key + project URL",
    fields=[
        CredentialField(
            id="project_url",
            label="Project URL",
            type="string",
            placeholder="https://abc.supabase.co",
        ),
        CredentialField(id="api_key", label="API Key", type="password", placeholder="eyJ..."),
    ],
)
