"""API-key credential provider for mcp.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="mcp_credentials",
    name="MCP Server",
    icon_slug="mcp",
    color="#1c1c1c",
    description="Call a Model Context Protocol tool via HTTP transport.",
    hint="MCP HTTP endpoint + optional bearer",
    fields=[
        CredentialField(
            id="endpoint",
            label="MCP Endpoint URL",
            type="string",
            placeholder="https://mcp.example.com/mcp",
        ),
        CredentialField(
            id="bearer_token", label="Bearer Token (optional, placeholder=)", type="password"
        ),
    ],
)
