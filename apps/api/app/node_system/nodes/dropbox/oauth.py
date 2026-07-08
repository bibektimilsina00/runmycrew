from __future__ import annotations

from apps.api.app.core.config import settings
from apps.api.app.credential_manager.oauth.base import (
    REDIRECT_URI,
    _SimpleOAuthProvider,
)


class DropboxOAuthProvider(_SimpleOAuthProvider):
    id = "dropbox_oauth"
    name = "Dropbox"
    icon_slug = "dropbox"
    color = "#1c1c1c"
    description = "Connect Dropbox for cloud file storage, folders, and sharing."
    scopes = [
        "Read and write Dropbox files + folders",
        "Manage share links",
        "Read your Dropbox account profile",
    ]
    _AUTH_URL = "https://www.dropbox.com/oauth2/authorize"
    _TOKEN_URL = "https://api.dropboxapi.com/oauth2/token"
    _SCOPE_STR = (
        "files.metadata.read files.content.read files.content.write sharing.write account_info.read"
    )
    _CLIENT_ID_ATTR = "DROPBOX_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "DROPBOX_CLIENT_SECRET"
    _REDIRECT_SERVICE = "dropbox"

    def get_authorization_url(self, state, code_challenge=None):
        """Dropbox needs `token_access_type=offline` to issue refresh
        tokens — without it the connection expires in a few hours."""
        from urllib.parse import urlencode

        params = {
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "redirect_uri": REDIRECT_URI.format(service=self._REDIRECT_SERVICE),
            "response_type": "code",
            "scope": self._SCOPE_STR,
            "state": state,
            "token_access_type": "offline",
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return f"{self._AUTH_URL}?{urlencode(params)}"


PROVIDER = DropboxOAuthProvider()
