from __future__ import annotations

from apps.api.app.credential_manager.oauth.base import (
    _SimpleOAuthProvider,
)


class BoxOAuthProvider(_SimpleOAuthProvider):
    id = "box_oauth"
    name = "Box"
    icon_slug = "box"
    color = "#ffffff"
    description = "Connect Box for cloud file storage, folders, and sharing."
    scopes = [
        "Read and write Box files and folders",
        "Create and manage share links",
        "Read your Box user profile",
    ]
    _AUTH_URL = "https://account.box.com/api/oauth2/authorize"
    _TOKEN_URL = "https://api.box.com/oauth2/token"
    # Box treats empty scope as "all scopes the developer app was
    # configured with" — explicit scopes here would narrow that grant.
    _SCOPE_STR = ""
    _CLIENT_ID_ATTR = "BOX_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "BOX_CLIENT_SECRET"
    _REDIRECT_SERVICE = "box"


PROVIDER = BoxOAuthProvider()
