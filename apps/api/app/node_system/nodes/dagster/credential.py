"""API-key credential provider for dagster.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="dagster_api_key",
    name="Dagster Cloud",
    icon_slug="dagster",
    color="#ffffff",
    description="Dagster Cloud — asset pipelines, jobs, runs.",
    hint="Dagster Cloud API access",
    fields=[
        CredentialField(
            id="api_key",
            label="Cloud API Token",
            type="password",
            placeholder="Dagster Cloud token",
        ),
        CredentialField(
            id="deployment", label="Deployment Slug", type="string", placeholder="prod"
        ),
    ],
)
