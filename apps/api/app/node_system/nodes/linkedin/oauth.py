from __future__ import annotations

from apps.api.app.credential_manager.oauth.base import (
    _SimpleOAuthProvider,
)


class LinkedInOAuthProvider(_SimpleOAuthProvider):
    id = "linkedin_oauth"
    name = "LinkedIn"
    icon_slug = "linkedin"
    color = "#1c1c1c"
    description = "Connect LinkedIn to read your profile + post updates as your member account."
    scopes = [
        "Read your basic profile + email",
        "Post updates on your behalf",
    ]
    _AUTH_URL = "https://www.linkedin.com/oauth/v2/authorization"
    _TOKEN_URL = "https://www.linkedin.com/oauth/v2/accessToken"
    # OpenID Connect scopes cover profile + email; `w_member_social`
    # is the current scope for posting on the member's behalf.
    _SCOPE_STR = "openid profile email w_member_social"
    _CLIENT_ID_ATTR = "LINKEDIN_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "LINKEDIN_CLIENT_SECRET"
    _REDIRECT_SERVICE = "linkedin"


PROVIDER = LinkedInOAuthProvider()
