from __future__ import annotations

import httpx

from apps.api.app.core.config import settings
from apps.api.app.credential_manager.oauth.base import (
    REDIRECT_URI,
    with_expiry_metadata,
)


class GoogleOAuthProvider:
    id = "google_oauth"
    name = "Google"
    icon_slug = "google"
    color = "#ffffff"
    type = "oauth"
    brand = "google"
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
        # Phase 4.26/4.27 extras — Ads, BigQuery, Meet, Vault, Books,
        # PageSpeed, and Admin Directory (Groups). All feature-flagged
        # to avoid tripping Google's Restricted-Scope verification
        # (adwords/ediscovery/admin.directory.group are sensitive/
        # restricted and need CASA review before general production
        # rollout — keep off by default).
        if getattr(settings, "GOOGLE_ADS_ENABLED", False):
            base.append("https://www.googleapis.com/auth/adwords")
        if getattr(settings, "GOOGLE_BIGQUERY_ENABLED", False):
            base.append("https://www.googleapis.com/auth/bigquery")
        if getattr(settings, "GOOGLE_MEET_ENABLED", False):
            base.append("https://www.googleapis.com/auth/meetings.space.created")
            base.append("https://www.googleapis.com/auth/meetings.space.readonly")
        if getattr(settings, "GOOGLE_VAULT_ENABLED", False):
            base.append("https://www.googleapis.com/auth/ediscovery")
        if getattr(settings, "GOOGLE_ADMIN_DIRECTORY_ENABLED", False):
            base.append("https://www.googleapis.com/auth/admin.directory.group")
            base.append("https://www.googleapis.com/auth/admin.directory.group.member")
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


PROVIDER = GoogleOAuthProvider()
