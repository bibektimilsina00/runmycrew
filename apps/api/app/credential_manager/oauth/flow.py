from datetime import UTC, datetime, timedelta
from typing import Any

from apps.api.app.core.config import settings
from apps.api.app.core.logger import get_logger

logger = get_logger(__name__)

REDIRECT_URI = f"{settings.BASE_URL}/api/v1/credentials/oauth/{{service}}/callback"


def with_expiry_metadata(token_data: dict) -> dict:
    """Attach absolute expiry timestamps when OAuth responses include lifetimes."""
    now = datetime.now(UTC)
    enriched = dict(token_data)
    expires_in = enriched.get("expires_in")
    if isinstance(expires_in, int):
        enriched["expires_at"] = (now + timedelta(seconds=expires_in)).isoformat()
    refresh_expires_in = enriched.get("refresh_token_expires_in")
    if isinstance(refresh_expires_in, int):
        enriched["refresh_token_expires_at"] = (
            now + timedelta(seconds=refresh_expires_in)
        ).isoformat()
    return enriched


class SlackOAuthProvider:
    id = "slack_oauth"
    name = "Slack"
    icon_slug = "slack"
    color = "#1c1c1c"
    type = "oauth"
    description = "Connect to your Slack workspace using OAuth 2.0"
    scopes = [
        "Send messages to channels",
        "Read public and private channels",
        "View users and email addresses",
        "Manage reactions",
        "Read and upload files",
    ]

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.SLACK_CLIENT_ID,
            "scope": "chat:write,channels:read,groups:read,im:read,mpim:read,users:read,users:read.email,reactions:read,reactions:write,files:read,files:write",
            "redirect_uri": REDIRECT_URI.format(service="slack"),
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"https://slack.com/oauth/v2/authorize?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        data = {
            "client_id": settings.SLACK_CLIENT_ID,
            "client_secret": settings.SLACK_CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI.format(service="slack"),
        }
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data=data,
            )
        data = response.json()
        if not data.get("ok"):
            raise ValueError(f"Slack OAuth failed: {data.get('error')}")

        # Slack v2 can return token at root (bot token) or in authed_user (user token)
        access_token = data.get("access_token") or data.get("authed_user", {}).get("access_token")

        if not access_token:
            raise ValueError("Slack response missing access_token")

        return with_expiry_metadata(
            {
                "access_token": access_token,
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "team_id": data.get("team", {}).get("id"),
                "team_name": data.get("team", {}).get("name"),
            }
        )

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://slack.com/api/oauth.v2.access",
                data={
                    "client_id": settings.SLACK_CLIENT_ID,
                    "client_secret": settings.SLACK_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
        data = response.json()
        if not data.get("ok"):
            raise ValueError(f"Slack token refresh failed: {data.get('error')}")
        return with_expiry_metadata(data)


class GitHubOAuthProvider:
    id = "github_oauth"
    name = "GitHub"
    icon_slug = "github"
    color = "#ffffff"
    type = "oauth"
    description = "Connect to GitHub using OAuth 2.0"
    scopes = [
        "Full access to public and private repositories",
        "Read-only access to user profile information",
        "Manage organization memberships",
    ]

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "scope": "repo,user",
            "redirect_uri": REDIRECT_URI.format(service="github"),
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"

        return f"https://github.com/login/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        data = {
            "client_id": settings.GITHUB_CLIENT_ID,
            "client_secret": settings.GITHUB_CLIENT_SECRET,
            "code": code,
            "redirect_uri": REDIRECT_URI.format(service="github"),
        }
        # GitHub also supports PKCE, though we aren't using it yet
        if code_verifier:
            data["code_verifier"] = code_verifier

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data=data,
            )
        data = response.json()
        if "error" in data:
            raise ValueError(f"GitHub OAuth failed: {data.get('error_description')}")

        return with_expiry_metadata(
            {
                "access_token": data["access_token"],
                "refresh_token": data.get("refresh_token"),
                "expires_in": data.get("expires_in"),
                "refresh_token_expires_in": data.get("refresh_token_expires_in"),
                "token_type": data["token_type"],
                "scope": data["scope"],
            }
        )

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://github.com/login/oauth/access_token",
                headers={"Accept": "application/json"},
                data={
                    "client_id": settings.GITHUB_CLIENT_ID,
                    "client_secret": settings.GITHUB_CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                },
            )
        data = response.json()
        if "error" in data:
            raise ValueError(f"GitHub token refresh failed: {data.get('error_description')}")
        return with_expiry_metadata(data)


class NotionOAuthProvider:
    id = "notion_oauth"
    name = "Notion"
    icon_slug = "notion"
    color = "#ffffff"
    type = "oauth"
    description = "Connect to Notion using OAuth 2.0 (requires a public integration)"
    scopes = [
        "Read and create pages and databases",
        "Access workspace content shared with the integration",
    ]

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.NOTION_CLIENT_ID,
            "redirect_uri": REDIRECT_URI.format(service="notion"),
            "response_type": "code",
            "state": state,
            "owner": "user",
        }
        return f"https://api.notion.com/v1/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import base64

        import httpx

        credentials = base64.b64encode(
            f"{settings.NOTION_CLIENT_ID}:{settings.NOTION_CLIENT_SECRET}".encode()
        ).decode()

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.notion.com/v1/oauth/token",
                headers={
                    "Authorization": f"Basic {credentials}",
                    "Content-Type": "application/json",
                },
                json={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": REDIRECT_URI.format(service="notion"),
                },
            )
        data = response.json()
        if "error" in data:
            raise ValueError(
                f"Notion OAuth failed: {data.get('error_description') or data['error']}"
            )

        return {
            "access_token": data["access_token"],
            "workspace_id": data.get("workspace_id"),
            "workspace_name": data.get("workspace_name"),
            "workspace_icon": data.get("workspace_icon"),
            "bot_id": data.get("bot_id"),
            "owner": data.get("owner"),
        }

    async def refresh_access_token(self, refresh_token: str):
        raise ValueError("Notion OAuth tokens do not expire and cannot be refreshed.")


class GoogleOAuthProvider:
    id = "google_oauth"
    name = "Google"
    icon_slug = "google"
    color = "#ffffff"
    type = "oauth"
    description = "Connect Google account for Gmail, Calendar, Drive, Sheets, Docs, and more"
    scopes = [
        "Read, send, modify, label, and delete Gmail messages",
        "Read and write Google Calendar events",
        "Create and manage Google Drive files (only files RunMyCrew creates)",
        "Read and write Google Sheets",
        "Read and write Google Docs",
        "Manage Google Tasks",
        "Read and write Google Forms (questions and settings)",
        "Read Google Forms responses",
        "Read and write Google Contacts",
        "Manage YouTube (videos, comments, playlists, subscriptions)",
        "Upload videos to YouTube",
        "Read and write Google Slides",
        "Send and manage messages in Google Chat spaces",
        "Read Google Chat space metadata and memberships",
        "Read Google Analytics reports and configuration",
        "Manage Search Console sites, sitemaps, and queries",
        "Read and write Google Cloud Storage buckets and objects",
        "Read your Google profile",
    ]

    # Phase 1 scope set. Trimmed deliberately:
    # - `gmail.modify` is the *one* Gmail scope that covers send + read +
    #   label + thread + trash without needing the broader `gmail` scope
    #   (which triggers Google's Restricted Scope Verification / CASA).
    # - `drive.file` only grants access to files RunMyCrew itself creates;
    #   safer default than the full `drive` scope which is restricted.
    # - Future surfaces (YouTube / Ads / Cloud APIs / Admin) get their
    #   own sibling provider — keeping this provider's consent screen
    #   short keeps the OAuth UX honest about what the user is granting.
    @classmethod
    def _scope_str(cls) -> str:
        """Build the scope list — appends the full Drive scope when the
        deployment has opted into folder-watch via the
        `GOOGLE_DRIVE_WATCH_EXTERNAL` env flag.

        The full `drive` scope (vs the narrower `drive.readonly`) is
        what unlocks **write** access to externally-uploaded files —
        without it, action nodes can't rename / share / delete a file
        the user uploaded via Drive web UI (only read it). `drive` is
        a Restricted Scope and needs CASA review before shipping to
        general production users; keep off by default."""
        base = [
            "https://www.googleapis.com/auth/gmail.modify",
            "https://www.googleapis.com/auth/calendar",
            "https://www.googleapis.com/auth/drive.file",
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/documents",
            "https://www.googleapis.com/auth/tasks",
            "https://www.googleapis.com/auth/forms.body",
            "https://www.googleapis.com/auth/forms.responses.readonly",
            "https://www.googleapis.com/auth/contacts",
            "https://www.googleapis.com/auth/youtube.force-ssl",
            "https://www.googleapis.com/auth/youtube.upload",
            "https://www.googleapis.com/auth/presentations",
            "https://www.googleapis.com/auth/chat.messages",
            "https://www.googleapis.com/auth/chat.messages.reactions",
            "https://www.googleapis.com/auth/chat.spaces.readonly",
            "https://www.googleapis.com/auth/chat.memberships.readonly",
            "https://www.googleapis.com/auth/analytics.readonly",
            "https://www.googleapis.com/auth/webmasters",
            "https://www.googleapis.com/auth/devstorage.read_write",
            "openid",
            "email",
            "profile",
        ]
        if getattr(settings, "GOOGLE_DRIVE_WATCH_EXTERNAL", False):
            base.insert(3, "https://www.googleapis.com/auth/drive")
        return " ".join(base)

    _SCOPE_STR = ""  # populated dynamically — kept for back-compat readers

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": settings.GOOGLE_CLIENT_ID if hasattr(settings, "GOOGLE_CLIENT_ID") else "",
            "redirect_uri": REDIRECT_URI.format(service="google"),
            "response_type": "code",
            "scope": self._scope_str(),
            "access_type": "offline",
            "state": state,
            "prompt": "consent",
            "include_granted_scopes": "true",
        }
        return f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID
                    if hasattr(settings, "GOOGLE_CLIENT_ID")
                    else "",
                    "client_secret": settings.GOOGLE_CLIENT_SECRET
                    if hasattr(settings, "GOOGLE_CLIENT_SECRET")
                    else "",
                    "code": code,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI.format(service="google"),
                },
            )
        data = response.json()
        if "error" in data:
            raise ValueError(f"Google OAuth failed: {data.get('error_description', data['error'])}")
        return with_expiry_metadata(data)

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://oauth2.googleapis.com/token",
                data={
                    "client_id": settings.GOOGLE_CLIENT_ID
                    if hasattr(settings, "GOOGLE_CLIENT_ID")
                    else "",
                    "client_secret": settings.GOOGLE_CLIENT_SECRET
                    if hasattr(settings, "GOOGLE_CLIENT_SECRET")
                    else "",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        data = response.json()
        if "error" in data:
            raise ValueError(
                f"Google token refresh failed: {data.get('error_description', data['error'])}"
            )
        return with_expiry_metadata(data)


class MetaOAuthProvider:
    """OAuth provider for the entire Meta (Facebook / Instagram / WhatsApp /
    Messenger) product family.

    All five surfaces sit behind one Meta developer app and one Graph API
    endpoint. We request the union of permissions upfront so the same
    `meta_oauth` credential can power FB Page, IG comment/DM, WhatsApp, and
    Lead Ads nodes — the user picks the *resource* (Page / IG user / WABA /
    form) per node via a `meta-resource` field type, not per credential.

    Token shape after `exchange_code`:
      access_token: long-lived user token (~60 days)
      token_type:   'bearer'
      expires_in:   seconds (Meta returns int)
      user_id:      Facebook user id
      pages:        list of {id, name, access_token, category} — page tokens
                    derived in the same exchange so node code never has to
                    re-fetch them. Page tokens don't expire unless the user
                    revokes the app.
    """

    id = "meta_oauth"
    name = "Meta (Facebook, Instagram, WhatsApp)"
    icon_slug = "meta"
    color = "#ffffff"
    type = "oauth"
    description = (
        "Connect Facebook Pages, Instagram Business, WhatsApp Business, and "
        "Lead Ads in one credential."
    )
    scopes = [
        "Manage Facebook Pages + post on your behalf",
        "Read + reply to Page comments and mentions",
        "Send and receive Messenger and Instagram DMs",
        "Read + reply to Instagram comments; publish posts and stories",
        "Read insights for Pages and Instagram posts",
        "Read + reply to WhatsApp Business messages and templates",
        "Retrieve Lead Ads form submissions",
    ]

    def _graph_url(self, path: str) -> str:
        return f"https://graph.facebook.com/{settings.META_GRAPH_API_VERSION}{path}"

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        if not settings.META_FB_LOGIN_CONFIG_ID:
            raise ValueError(
                "META_FB_LOGIN_CONFIG_ID is not set. Create a Configuration in "
                "Meta App Dashboard → Facebook Login for Business → Configurations, "
                "then paste the id into the env var."
            )

        # Facebook Login for Business drives the permission set and asset
        # picker from the Configuration referenced by `config_id`. Meta's
        # web dialog ignores any `scope` query param when `config_id` is
        # present, so we never send one.
        # Meta's OAuth dialog supports PKCE only on the mobile SDK — the
        # web flow ignores `code_challenge`, so skip it here to keep parity
        # with what their docs actually accept.
        params: dict[str, str] = {
            "client_id": settings.META_APP_ID,
            "redirect_uri": REDIRECT_URI.format(service="meta"),
            "state": state,
            "response_type": "code",
            "config_id": settings.META_FB_LOGIN_CONFIG_ID,
        }
        return f"https://www.facebook.com/{settings.META_GRAPH_API_VERSION}/dialog/oauth?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Step 1 — short-lived user token (1-2 hours).
            short = await client.get(
                self._graph_url("/oauth/access_token"),
                params={
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "redirect_uri": REDIRECT_URI.format(service="meta"),
                    "code": code,
                },
            )
            short_data = short.json()
            if "access_token" not in short_data:
                err = short_data.get("error", {})
                raise ValueError(f"Meta OAuth failed: {err.get('message') or short_data}")

            # Step 2 — exchange for a long-lived user token (~60 days).
            long_resp = await client.get(
                self._graph_url("/oauth/access_token"),
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "fb_exchange_token": short_data["access_token"],
                },
            )
            long_data = long_resp.json()
            if "access_token" not in long_data:
                err = long_data.get("error", {})
                raise ValueError(
                    f"Meta long-lived token exchange failed: {err.get('message') or long_data}"
                )
            user_token = long_data["access_token"]

            # Step 3 — fetch the FB user id (used as display + logging key).
            me = await client.get(
                self._graph_url("/me"),
                params={"access_token": user_token, "fields": "id,name"},
            )
            me_data = me.json()
            if "id" not in me_data:
                raise ValueError("Meta /me lookup missing id")

            # Step 4 — fetch every Page the user manages plus the
            # corresponding (non-expiring) page tokens. Includes IG business
            # account id when one is linked to the Page.
            pages_resp = await client.get(
                self._graph_url(f"/{me_data['id']}/accounts"),
                params={
                    "access_token": user_token,
                    "fields": "id,name,category,access_token,instagram_business_account{id,username}",
                    "limit": 100,
                },
            )
            pages_data = pages_resp.json()
            pages = pages_data.get("data", [])

            # Step 5 — fetch every WhatsApp Business Account (WABA) the user
            # owns plus the registered phone numbers underneath each one.
            # Mirrors the page-enrichment hop above: nodes can read WABA +
            # phone metadata straight from credential storage instead of
            # round-tripping the Graph API on every send. Failures here are
            # non-fatal — Pages-only setups still work; only WhatsApp nodes
            # would surface "no WABAs" later.
            waba_accounts: list[dict[str, Any]] = []
            try:
                biz_resp = await client.get(
                    self._graph_url(f"/{me_data['id']}/businesses"),
                    params={
                        "access_token": user_token,
                        "fields": (
                            "id,name,"
                            "owned_whatsapp_business_accounts"
                            "{id,name,phone_numbers"
                            "{id,display_phone_number,verified_name,quality_rating}}"
                        ),
                        "limit": 50,
                    },
                )
                biz_data = biz_resp.json()
                for biz in biz_data.get("data", []) or []:
                    owned = (biz.get("owned_whatsapp_business_accounts") or {}).get("data") or []
                    for waba in owned:
                        # Inline business id so the resource picker can
                        # display "WABA · Business" without another hop.
                        waba["business_id"] = biz.get("id")
                        waba["business_name"] = biz.get("name")
                        waba_accounts.append(waba)
            except Exception:  # noqa: BLE001 — enrichment is best-effort
                waba_accounts = []

        return with_expiry_metadata(
            {
                "access_token": user_token,
                "token_type": "bearer",
                "expires_in": long_data.get("expires_in"),
                "user_id": me_data["id"],
                "user_name": me_data.get("name"),
                "pages": pages,
                "whatsapp_business_accounts": waba_accounts,
            }
        )

    async def refresh_access_token(self, refresh_token: str):
        # Meta long-lived user tokens are refreshed by exchanging the *current*
        # long-lived token (passed in as `refresh_token` here) for a new
        # 60-day token via the same `fb_exchange_token` endpoint. There is
        # no separate refresh token in Meta's flow.
        import httpx

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                self._graph_url("/oauth/access_token"),
                params={
                    "grant_type": "fb_exchange_token",
                    "client_id": settings.META_APP_ID,
                    "client_secret": settings.META_APP_SECRET,
                    "fb_exchange_token": refresh_token,
                },
            )
            data = resp.json()
        if "access_token" not in data:
            err = data.get("error", {})
            raise ValueError(f"Meta token refresh failed: {err.get('message') or data}")
        return with_expiry_metadata(data)


class InstagramOAuthProvider:
    """OAuth provider for the standalone Instagram API (Instagram Login).

    Use this when the user has an Instagram Business / Creator account but
    no Facebook Page (or doesn't want to link one). It uses Meta's
    *Instagram Login* path — a sibling Meta app under the same Meta App
    Dashboard, with its own app id / secret and OAuth dialog hosted at
    `api.instagram.com`.

    Token shape after `exchange_code`:
      access_token: long-lived IG user token (~60 days, refreshable
                    indefinitely as long as it's used ≥ once / 60 days)
      token_type:   'bearer'
      expires_in:   seconds
      user_id:      IG numeric user id (same value Meta calls `user_id`
                    inside the IG OAuth response)
      ig_accounts:  list of {id, username, account_type} — always a single
                    entry today (IG Login authorises one IG account at a
                    time). Stored as a list so the resource picker code
                    can share shape with `pages` from MetaOAuthProvider.
    """

    id = "instagram_oauth"
    name = "Instagram (standalone)"
    icon_slug = "instagram"
    color = "#ffffff"
    type = "oauth"
    description = (
        "Connect an Instagram Business / Creator account directly, without a "
        "Facebook Page. Powers IG comment / DM / mention nodes."
    )
    scopes = [
        "Read your Instagram Business profile + media",
        "Read + reply to comments on your posts and reels",
        "Send and receive Instagram Direct Messages",
        "Read Instagram insights",
        "Publish posts and stories",
    ]

    # Scopes accepted by api.instagram.com/oauth/authorize. These are the
    # *new* (2024+) Instagram API scope names — note the `business_` prefix.
    _scopes = ",".join(
        [
            "instagram_business_basic",
            "instagram_business_manage_comments",
            "instagram_business_manage_messages",
            "instagram_business_content_publish",
            "instagram_business_manage_insights",
        ]
    )

    def _graph_url(self, path: str) -> str:
        # Instagram Login uses graph.instagram.com (NOT graph.facebook.com).
        return f"https://graph.instagram.com/{settings.META_GRAPH_API_VERSION}{path}"

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        if not settings.META_INSTAGRAM_APP_ID:
            raise ValueError(
                "META_INSTAGRAM_APP_ID is not set. Capture it from Meta App "
                "Dashboard → Instagram → API setup with Instagram login."
            )

        params: dict[str, str] = {
            "client_id": settings.META_INSTAGRAM_APP_ID,
            "redirect_uri": REDIRECT_URI.format(service="instagram"),
            "scope": self._scopes,
            "response_type": "code",
            "state": state,
        }
        return f"https://api.instagram.com/oauth/authorize?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        async with httpx.AsyncClient(timeout=20.0) as client:
            # Step 1 — short-lived IG user token (1 hour).
            short = await client.post(
                "https://api.instagram.com/oauth/access_token",
                data={
                    "client_id": settings.META_INSTAGRAM_APP_ID,
                    "client_secret": settings.META_INSTAGRAM_APP_SECRET,
                    "grant_type": "authorization_code",
                    "redirect_uri": REDIRECT_URI.format(service="instagram"),
                    "code": code,
                },
            )
            short_data = short.json()
            if "access_token" not in short_data:
                err = short_data.get("error_message") or short_data.get("error") or short_data
                raise ValueError(f"Instagram OAuth failed: {err}")
            short_token = short_data["access_token"]
            ig_user_id = str(short_data.get("user_id") or "")

            # Step 2 — exchange for a long-lived token (~60 days).
            long_resp = await client.get(
                self._graph_url("/access_token"),
                params={
                    "grant_type": "ig_exchange_token",
                    "client_secret": settings.META_INSTAGRAM_APP_SECRET,
                    "access_token": short_token,
                },
            )
            long_data = long_resp.json()
            if "access_token" not in long_data:
                err = long_data.get("error", {})
                raise ValueError(
                    f"Instagram long-lived token exchange failed: {err.get('message') or long_data}"
                )
            user_token = long_data["access_token"]

            # Step 3 — fetch IG profile metadata (id, username, account type).
            me = await client.get(
                self._graph_url("/me"),
                params={
                    "access_token": user_token,
                    "fields": "id,user_id,username,account_type,name,profile_picture_url",
                },
            )
            me_data = me.json()
            if "id" not in me_data:
                err = me_data.get("error", {})
                raise ValueError(f"Instagram /me lookup failed: {err.get('message') or me_data}")

        ig_account = {
            "id": str(me_data["id"]),
            # `user_id` is the IG business account numeric id used by some
            # downstream endpoints (e.g. webhook subscription); `id` is the
            # Instagram Graph API user node id used for /messages etc.
            "user_id": str(me_data.get("user_id") or ig_user_id or me_data["id"]),
            "username": me_data.get("username"),
            "account_type": me_data.get("account_type"),
            "name": me_data.get("name"),
            "profile_picture_url": me_data.get("profile_picture_url"),
            "access_token": user_token,
        }

        return with_expiry_metadata(
            {
                "access_token": user_token,
                "token_type": "bearer",
                "expires_in": long_data.get("expires_in"),
                "user_id": ig_account["id"],
                "user_name": ig_account.get("username"),
                # Mirrors MetaOAuthProvider's `pages` shape so list_resources
                # can iterate one structure regardless of credential type.
                "ig_accounts": [ig_account],
            }
        )

    async def refresh_access_token(self, refresh_token: str):
        # Instagram long-lived tokens are refreshed by passing the *current*
        # long-lived token to ig_refresh_token. No separate refresh token.
        import httpx

        async with httpx.AsyncClient(timeout=20.0) as client:
            resp = await client.get(
                self._graph_url("/refresh_access_token"),
                params={
                    "grant_type": "ig_refresh_token",
                    "access_token": refresh_token,
                },
            )
            data = resp.json()
        if "access_token" not in data:
            err = data.get("error", {})
            raise ValueError(f"Instagram token refresh failed: {err.get('message') or data}")
        return with_expiry_metadata(data)


class MicrosoftOAuthProvider:
    """Microsoft Graph OAuth — shared by Outlook, Teams, OneDrive,
    SharePoint, Excel, and Planner. Single grant covers all five Phase
    2.1 surfaces so the user only consents once per workspace.

    Tenant `common` accepts both Microsoft account (personal) tokens
    and any AAD-joined work account. Deployments that need to lock to
    a single tenant override `MICROSOFT_TENANT_ID`.
    """

    id = "microsoft_oauth"
    name = "Microsoft"
    icon_slug = "microsoft"
    color = "#ffffff"
    type = "oauth"
    description = (
        "Connect Microsoft 365 for Outlook mail, Teams chat, OneDrive + "
        "SharePoint files, Excel workbooks, and Planner."
    )
    scopes = [
        "Read, send, and organize Outlook mail",
        "Read and send Teams chat messages + channel messages",
        "Read and write your OneDrive + SharePoint files",
        "Read and write Excel workbook ranges + tables",
        "Read and write Planner tasks",
        "Read your profile",
        "Keep the connection alive (offline access)",
    ]

    _SCOPE_STR = " ".join(
        [
            "Mail.ReadWrite",
            "Mail.Send",
            "Chat.ReadWrite",
            "ChannelMessage.Send",
            "ChannelMessage.Read.All",
            "Team.ReadBasic.All",
            "Files.ReadWrite.All",
            "Sites.ReadWrite.All",
            "Tasks.ReadWrite",
            "User.Read",
            "offline_access",
        ]
    )

    @classmethod
    def _tenant(cls) -> str:
        return getattr(settings, "MICROSOFT_TENANT_ID", None) or "common"

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": getattr(settings, "MICROSOFT_CLIENT_ID", "") or "",
            "redirect_uri": REDIRECT_URI.format(service="microsoft"),
            "response_type": "code",
            "scope": self._SCOPE_STR,
            "response_mode": "query",
            "state": state,
            "prompt": "select_account",
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return (
            f"https://login.microsoftonline.com/{self._tenant()}"
            f"/oauth2/v2.0/authorize?{urlencode(params)}"
        )

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        data: dict = {
            "client_id": getattr(settings, "MICROSOFT_CLIENT_ID", "") or "",
            "client_secret": getattr(settings, "MICROSOFT_CLIENT_SECRET", "") or "",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI.format(service="microsoft"),
            "scope": self._SCOPE_STR,
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{self._tenant()}/oauth2/v2.0/token",
                data=data,
            )
        body = response.json()
        if "error" in body:
            raise ValueError(
                f"Microsoft OAuth failed: {body.get('error_description', body['error'])}"
            )
        return with_expiry_metadata(body)

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://login.microsoftonline.com/{self._tenant()}/oauth2/v2.0/token",
                data={
                    "client_id": getattr(settings, "MICROSOFT_CLIENT_ID", "") or "",
                    "client_secret": getattr(settings, "MICROSOFT_CLIENT_SECRET", "") or "",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                    "scope": self._SCOPE_STR,
                },
            )
        body = response.json()
        if "access_token" not in body:
            err = body.get("error_description") or body.get("error") or body
            raise ValueError(f"Microsoft token refresh failed: {err}")
        return with_expiry_metadata(body)


class _SimpleOAuthProvider:
    """Boilerplate-light OAuth2 provider for vanilla Bearer-token flows.

    Subclasses set the five identity attributes (id, name, icon_slug,
    color, description, scopes), the two endpoints (`_AUTH_URL`,
    `_TOKEN_URL`), the scope string (`_SCOPE_STR`), and the env-var
    names + redirect service. Everything else (auth URL build, token
    exchange, refresh) is shared.

    Used for providers whose OAuth dance is the textbook flow: a code
    grant to a token endpoint, refresh-token rotation, no audience /
    PKCE-required / multi-tenant complications. Five Phase 2.2
    providers (Asana, HubSpot, Calendly, Zoom, Box) all fit this shape.
    """

    type = "oauth"
    # Subclass overrides — empty defaults keep the class instantiable
    # for type-checking but every real subclass replaces them.
    id: str = ""
    name: str = ""
    icon_slug: str | None = None
    color: str = "#1c1c1c"
    description: str = ""
    scopes: list[str] = []
    _AUTH_URL: str = ""
    _TOKEN_URL: str = ""
    _SCOPE_STR: str = ""
    _CLIENT_ID_ATTR: str = ""
    _CLIENT_SECRET_ATTR: str = ""
    _REDIRECT_SERVICE: str = ""

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params: dict = {
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "redirect_uri": REDIRECT_URI.format(service=self._REDIRECT_SERVICE),
            "response_type": "code",
            "state": state,
        }
        if self._SCOPE_STR:
            params["scope"] = self._SCOPE_STR
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return f"{self._AUTH_URL}?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        data: dict = {
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "client_secret": getattr(settings, self._CLIENT_SECRET_ATTR, "") or "",
            "code": code,
            "grant_type": "authorization_code",
            "redirect_uri": REDIRECT_URI.format(service=self._REDIRECT_SERVICE),
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        async with httpx.AsyncClient() as client:
            response = await client.post(self._TOKEN_URL, data=data)
        body = response.json()
        if "error" in body:
            raise ValueError(
                f"{self.name} OAuth failed: {body.get('error_description', body['error'])}"
            )
        return with_expiry_metadata(body)

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self._TOKEN_URL,
                data={
                    "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
                    "client_secret": getattr(settings, self._CLIENT_SECRET_ATTR, "") or "",
                    "refresh_token": refresh_token,
                    "grant_type": "refresh_token",
                },
            )
        body = response.json()
        if "access_token" not in body:
            err = body.get("error_description") or body.get("error") or body
            raise ValueError(f"{self.name} token refresh failed: {err}")
        return with_expiry_metadata(body)


class AsanaOAuthProvider(_SimpleOAuthProvider):
    id = "asana_oauth"
    name = "Asana"
    icon_slug = "asana"
    color = "#1c1c1c"
    description = "Connect Asana for projects, tasks, and team workflows."
    scopes = [
        "Read and write tasks, projects, sections, and comments",
        "Read your workspace and team metadata",
    ]
    _AUTH_URL = "https://app.asana.com/-/oauth_authorize"
    _TOKEN_URL = "https://app.asana.com/-/oauth_token"
    _SCOPE_STR = "default"
    _CLIENT_ID_ATTR = "ASANA_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "ASANA_CLIENT_SECRET"
    _REDIRECT_SERVICE = "asana"


class HubSpotOAuthProvider(_SimpleOAuthProvider):
    id = "hubspot_oauth"
    name = "HubSpot (OAuth)"
    icon_slug = "hubspot"
    color = "#1c1c1c"
    description = "Connect HubSpot CRM via OAuth — contacts, deals, companies, tickets."
    scopes = [
        "Read and write CRM contacts, companies, deals, and tickets",
        "Send transactional emails and manage marketing assets",
        "Read your HubSpot account profile",
    ]
    _AUTH_URL = "https://app.hubspot.com/oauth/authorize"
    _TOKEN_URL = "https://api.hubapi.com/oauth/v1/token"
    _SCOPE_STR = (
        "crm.objects.contacts.read crm.objects.contacts.write "
        "crm.objects.companies.read crm.objects.companies.write "
        "crm.objects.deals.read crm.objects.deals.write tickets oauth"
    )
    _CLIENT_ID_ATTR = "HUBSPOT_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "HUBSPOT_CLIENT_SECRET"
    _REDIRECT_SERVICE = "hubspot"


class CalendlyOAuthProvider(_SimpleOAuthProvider):
    id = "calendly_oauth"
    name = "Calendly"
    icon_slug = "calendly"
    color = "#1c1c1c"
    description = "Connect Calendly for scheduled events, invitees, and webhooks."
    scopes = [
        "Read your scheduled events and invitee details",
        "Manage webhook subscriptions for new bookings",
        "Read your Calendly user profile",
    ]
    _AUTH_URL = "https://auth.calendly.com/oauth/authorize"
    _TOKEN_URL = "https://auth.calendly.com/oauth/token"
    _SCOPE_STR = "default"
    _CLIENT_ID_ATTR = "CALENDLY_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "CALENDLY_CLIENT_SECRET"
    _REDIRECT_SERVICE = "calendly"


class ZoomOAuthProvider(_SimpleOAuthProvider):
    id = "zoom_oauth"
    name = "Zoom"
    icon_slug = "zoom"
    color = "#ffffff"
    description = "Connect Zoom for meeting management, users, and recordings."
    scopes = [
        "Read and write meetings on your account",
        "Read your Zoom user profile",
        "Read meeting recordings and transcripts",
    ]
    _AUTH_URL = "https://zoom.us/oauth/authorize"
    _TOKEN_URL = "https://zoom.us/oauth/token"
    _SCOPE_STR = "meeting:read meeting:write user:read recording:read"
    _CLIENT_ID_ATTR = "ZOOM_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "ZOOM_CLIENT_SECRET"
    _REDIRECT_SERVICE = "zoom"


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
        "files.metadata.read files.content.read files.content.write "
        "sharing.write account_info.read"
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


class DocuSignOAuthProvider(_SimpleOAuthProvider):
    """DocuSign OAuth. Uses `account.docusign.com` for prod OAuth
    authorization; deployments testing on the demo tenant override
    `DOCUSIGN_AUTH_HOST` to `account-d.docusign.com`.

    The API host itself is *per-account* (returned from userinfo after
    OAuth). The manifest resolves that URL via the credential's
    `account_url` field — same pattern as Shopify + Supabase.
    """

    id = "docusign_oauth"
    name = "DocuSign"
    icon_slug = "docusign"
    color = "#1c1c1c"
    description = "Connect DocuSign to send envelopes, manage templates, and pull signatures."
    scopes = [
        "Send and manage envelopes",
        "Read your DocuSign account + user info",
        "Sign requests on your behalf",
    ]
    _AUTH_URL = ""  # overridden per-instance via env
    _TOKEN_URL = ""
    _SCOPE_STR = "signature impersonation"
    _CLIENT_ID_ATTR = "DOCUSIGN_CLIENT_ID"
    _CLIENT_SECRET_ATTR = "DOCUSIGN_CLIENT_SECRET"
    _REDIRECT_SERVICE = "docusign"

    @classmethod
    def _host(cls) -> str:
        # `account-d.docusign.com` for demo/dev; `account.docusign.com`
        # for prod. Env-driven so a single deployment can pick a tier.
        return getattr(settings, "DOCUSIGN_AUTH_HOST", None) or "account.docusign.com"

    def get_authorization_url(self, state, code_challenge=None):
        from urllib.parse import urlencode

        params = {
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "redirect_uri": REDIRECT_URI.format(service=self._REDIRECT_SERVICE),
            "response_type": "code",
            "scope": self._SCOPE_STR,
            "state": state,
        }
        if code_challenge:
            params["code_challenge"] = code_challenge
            params["code_challenge_method"] = "S256"
        return f"https://{self._host()}/oauth/auth?{urlencode(params)}"

    async def exchange_code(self, code, code_verifier=None):
        import httpx

        data: dict = {
            "grant_type": "authorization_code",
            "code": code,
            "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
            "client_secret": getattr(settings, self._CLIENT_SECRET_ATTR, "") or "",
        }
        if code_verifier:
            data["code_verifier"] = code_verifier
        async with httpx.AsyncClient() as client:
            response = await client.post(f"https://{self._host()}/oauth/token", data=data)
        body = response.json()
        if "error" in body:
            raise ValueError(
                f"DocuSign OAuth failed: {body.get('error_description', body['error'])}"
            )
        return with_expiry_metadata(body)

    async def refresh_access_token(self, refresh_token: str):
        import httpx

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"https://{self._host()}/oauth/token",
                data={
                    "grant_type": "refresh_token",
                    "refresh_token": refresh_token,
                    "client_id": getattr(settings, self._CLIENT_ID_ATTR, "") or "",
                    "client_secret": getattr(settings, self._CLIENT_SECRET_ATTR, "") or "",
                },
            )
        body = response.json()
        if "access_token" not in body:
            err = body.get("error_description") or body.get("error") or body
            raise ValueError(f"DocuSign token refresh failed: {err}")
        return with_expiry_metadata(body)


class BoxOAuthProvider(_SimpleOAuthProvider):
    id = "box_oauth"
    name = "Box"
    icon_slug = "box"
    color = "#1c1c1c"
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


PROVIDERS = {
    "slack": SlackOAuthProvider(),
    "github": GitHubOAuthProvider(),
    "notion": NotionOAuthProvider(),
    "google": GoogleOAuthProvider(),
    "meta": MetaOAuthProvider(),
    "instagram": InstagramOAuthProvider(),
    "microsoft": MicrosoftOAuthProvider(),
    "asana": AsanaOAuthProvider(),
    "hubspot": HubSpotOAuthProvider(),
    "calendly": CalendlyOAuthProvider(),
    "zoom": ZoomOAuthProvider(),
    "box": BoxOAuthProvider(),
    "dropbox": DropboxOAuthProvider(),
    "docusign": DocuSignOAuthProvider(),
}


def get_oauth_provider(service_name: str):
    return PROVIDERS.get(service_name)
