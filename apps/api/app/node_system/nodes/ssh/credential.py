"""API-key credential provider for ssh.

Auto-discovered by `credential_manager/api_keys.py`. Drop this file
into a node folder — provider registers on next reload.
"""

from apps.api.app.credential_manager.api_keys import APIKeyProvider, CredentialField

PROVIDER = APIKeyProvider(
    id="ssh_credentials",
    name="SSH / SFTP",
    icon_slug="ssh",
    color="#ffffff",
    description="Remote shell + file transfer over SSH (asyncssh).",
    hint="Password or PEM private key",
    fields=[
        CredentialField(
            id="host", label="Host", type="string", placeholder="1.2.3.4 or host.example.com"
        ),
        CredentialField(id="port", label="Port", type="number", placeholder="22"),
        CredentialField(id="username", label="Username", type="string", placeholder="ubuntu"),
        CredentialField(
            id="password",
            label="Password (or leave blank if using key, placeholder=)",
            type="password",
        ),
        CredentialField(
            id="private_key",
            label="Private Key (PEM, placeholder=)",
            type="password",
            placeholder="-----BEGIN OPENSSH PRIVATE KEY-----...",
        ),
        CredentialField(
            id="passphrase", label="Key Passphrase (optional, placeholder=)", type="password"
        ),
        CredentialField(
            id="known_hosts_policy",
            label="Known Hosts Policy (strict|accept_new|ignore, placeholder=)",
            type="string",
            placeholder="strict",
        ),
    ],
)
