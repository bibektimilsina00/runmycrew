from pathlib import Path

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "RunMyCrew"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "development_secret_key_change_me"
    ENCRYPTION_KEY: str = "ZqprL7EBBN63_Nk0a_MoJyMTTrqf06xWY_3oTibUXAY="
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    BASE_URL: str = "http://localhost:8000"
    # Externally-reachable origin used when minting signed URLs handed off
    # to third-party services (Meta's content-publishing endpoint pulls
    # uploaded assets through this). When unset, BASE_URL is used — fine
    # for local-only flows, but Meta won't be able to fetch from
    # `http://localhost:8000`, so production deployments MUST set this to
    # the Cloudflare tunnel / public hostname.
    PUBLIC_BASE_URL: str = ""
    FRONTEND_URL: str = "http://localhost:3001"
    # Public origin the hosted-app pages live on (used to mint share URLs
    # returned by /workflows/{id}/publish). Defaults to FRONTEND_URL when
    # unset. In production, set to https://apps.myco.com or similar.
    PUBLIC_APP_BASE_URL: str = ""
    # Default origins match the actual ports each frontend listens on in dev:
    # - web (apps/web Vite)  → :3001  (see apps/web/vite.config.ts)
    # - site (apps/site Next) → :3100 (see apps/site/package.json)
    # :5173 stays for the legacy Vite default port so a customised config
    # doesn't get blocked.
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:3001",
            "http://127.0.0.1:3001",
            "http://localhost:3100",
            "http://127.0.0.1:3100",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "runmycrew"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    # Microsoft (Azure AD / Entra ID) — sign-in only. `common` tenant
    # accepts both personal Microsoft accounts and work/school Entra
    # accounts. Use a tenant id to lock to one org.
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT: str = "common"

    NOTION_CLIENT_ID: str = ""
    NOTION_CLIENT_SECRET: str = ""

    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_BOT_TOKEN: str = ""

    LINEAR_CLIENT_ID: str = ""
    LINEAR_CLIENT_SECRET: str = ""

    GOOGLE_CLIENT_ID: str = ""
    GOOGLE_CLIENT_SECRET: str = ""

    # Microsoft 365 OAuth (Outlook, Teams, OneDrive, SharePoint, Excel,
    # Planner). `MICROSOFT_TENANT_ID` defaults to `common` (multi-tenant
    # + personal accounts). Deployments that need single-tenant lock
    # override it with the tenant guid.
    MICROSOFT_CLIENT_ID: str = ""
    MICROSOFT_CLIENT_SECRET: str = ""
    MICROSOFT_TENANT_ID: str = "common"

    # Phase 2.2 OAuth providers (driven by _SimpleOAuthProvider in
    # credential_manager/oauth/flow.py — vanilla code-grant flows).
    ASANA_CLIENT_ID: str = ""
    ASANA_CLIENT_SECRET: str = ""
    HUBSPOT_CLIENT_ID: str = ""
    HUBSPOT_CLIENT_SECRET: str = ""
    CALENDLY_CLIENT_ID: str = ""
    CALENDLY_CLIENT_SECRET: str = ""
    ZOOM_CLIENT_ID: str = ""
    ZOOM_CLIENT_SECRET: str = ""
    BOX_CLIENT_ID: str = ""
    BOX_CLIENT_SECRET: str = ""
    DROPBOX_CLIENT_ID: str = ""
    DROPBOX_CLIENT_SECRET: str = ""
    DOCUSIGN_CLIENT_ID: str = ""
    DOCUSIGN_CLIENT_SECRET: str = ""
    # DocuSign auth host — `account-d.docusign.com` on the demo/dev
    # tier, `account.docusign.com` in production. Default is prod.
    DOCUSIGN_AUTH_HOST: str = "account.docusign.com"
    LINKEDIN_CLIENT_ID: str = ""
    LINKEDIN_CLIENT_SECRET: str = ""

    # Google Picker SDK keys (separate from OAuth client). The
    # `developer key` is a browser-restricted API key for the Picker
    # library; the `app id` is the numeric Cloud-project number used by
    # Picker to bind the session to the verified consent screen. Both
    # are returned by the picker-token endpoint so the editor doesn't
    # bake project ids into the frontend bundle.
    GOOGLE_API_KEY: str = ""
    GOOGLE_APP_ID: str = ""
    # Drive trigger scope tier. False (default) → request only
    # `drive.file` — Drive trigger sees uploads done via the platform's action
    # node, but NOT external uploads (Drive web UI, mobile app, other
    # apps). True → also request `drive.readonly` so the trigger can
    # watch a Picker-selected folder for ALL uploads regardless of
    # source. `drive.readonly` is a Restricted Scope that requires
    # Google's CASA security assessment before shipping to general
    # users in production. Safe defaults stay off.
    GOOGLE_DRIVE_WATCH_EXTERNAL: bool = False

    # Meta (Facebook + Instagram + WhatsApp + Messenger). One developer app
    # backs every Meta product. The verify token is the shared secret used
    # for the webhook subscription handshake (Meta calls our endpoint with
    # `hub.verify_token` — we echo `hub.challenge` only if it matches).
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_WEBHOOK_VERIFY_TOKEN: str = ""
    META_GRAPH_API_VERSION: str = "v20.0"
    # Facebook Login for Business Configuration ID. Defines the permission
    # set and asset picker shown during OAuth. Create one in Meta App
    # Dashboard → Facebook Login for Business → Configurations, then paste
    # the numeric id here. Required for the Meta OAuth flow to work.
    META_FB_LOGIN_CONFIG_ID: str = ""

    # Instagram API with Instagram Login — standalone OAuth path for users
    # who only have an Instagram Business account and don't want to link a
    # Facebook Page. App-level credentials come from Meta App Dashboard →
    # Instagram → API setup with Instagram login. Different app id/secret
    # than META_APP_ID — Meta provisions a sibling app for the IG flow.
    META_INSTAGRAM_APP_ID: str = ""
    META_INSTAGRAM_APP_SECRET: str = ""
    # Loose webhook → listen-slot matching for dev environments. When the
    # cred-aware id fallback (see MetaService._claim_slots_with_id_fallback)
    # also misses — e.g. Meta delivers a messaging-scoped id we never saw
    # during OAuth — set this to "true" to claim any open slot for the
    # same (object_type, field) tuple. Off in production: it can let one
    # workspace's webhook fire another workspace's listen slot if the two
    # are sitting on the same field at the same instant.
    META_WEBHOOK_LOOSE_LISTEN_MATCH: bool = False

    # Environment & CORS
    ENVIRONMENT: str = "development"  # "production" in prod
    CORS_ORIGINS: str = ""  # Comma-separated origins; overrides defaults when set

    # Rate limits (slowapi format: "N/period")
    RATE_LIMIT_AUTH: str = "5/minute"
    RATE_LIMIT_EXECUTION: str = "20/minute"
    RATE_LIMIT_UPLOAD: str = "10/minute"
    RATE_LIMIT_DEFAULT: str = "100/minute"

    # Code-node sandbox: "auto" (container when Docker is reachable, else
    # in-process hardening), "container" (require the container boundary), or
    # "process" (in-process hardening only).
    CODE_SANDBOX: str = "auto"
    CODE_SANDBOX_PYTHON_IMAGE: str = "python:3.13-slim"
    CODE_SANDBOX_NODE_IMAGE: str = "node:22-alpine"
    CODE_SANDBOX_MEMORY_MB: int = 512

    # Copilot fallback API keys — used by /copilot/{id}/chat ONLY, when the user
    # has no stored credential for that provider. Lets the Copilot run against a
    # shared/dev key without provisioning per-user credentials. All optional.
    GEMINI_API_KEY: str = ""
    OPENAI_API_KEY: str = ""
    ANTHROPIC_API_KEY: str = ""
    GROQ_API_KEY: str = ""

    # Observability — error tracking is off unless SENTRY_DSN is set.
    SENTRY_DSN: str = ""
    SENTRY_TRACES_SAMPLE_RATE: float = 0.0

    # Email — Resend HTTP API is preferred (port 443, no provider port-block
    # risk like DigitalOcean blocking 25/465/587). Falls back to SMTP for
    # self-hosters using Gmail, SES relay, Mailgun, etc.
    RESEND_API_KEY: str = ""
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@runmycrew.com"
    SMTP_FROM_NAME: str = "RunMyCrew"
    SMTP_TLS: bool = True

    # RapidAPI passthrough — used by the YouTube node's transcript op
    # because direct scraping of youtube.com gets blocked from cloud
    # IPs (DigitalOcean, AWS, GCP). Set the key + the host of whichever
    # RapidAPI YouTube-transcript provider you subscribed to; if either
    # is blank the node falls back to the direct-scrape library, which
    # works locally but typically fails in production.
    RAPIDAPI_KEY: str = ""
    RAPIDAPI_YOUTUBE_TRANSCRIPT_HOST: str = "youtube-transcriptor.p.rapidapi.com"

    model_config = SettingsConfigDict(
        env_file=str(Path(__file__).resolve().parents[4] / ".env"),
        case_sensitive=True,
        extra="ignore",
    )

    @model_validator(mode="after")
    def _require_strong_secrets_in_production(self) -> "Settings":
        """Refuse to boot in production with the shipped default/empty secrets —
        otherwise JWTs are forgeable and every stored credential is decryptable
        with a publicly-known key."""
        if self.ENVIRONMENT == "production":
            fields = type(self).model_fields
            weak = [
                name
                for name in ("SECRET_KEY", "ENCRYPTION_KEY")
                if not getattr(self, name) or getattr(self, name) == fields[name].default
            ]
            if weak:
                raise ValueError(
                    f"Refusing to start in production with default/empty {', '.join(weak)}. "
                    "Set strong unique values (e.g. `openssl rand -hex 32`)."
                )
        return self

    @computed_field  # type: ignore[prop-decorator]
    @property
    def resolved_cors_origins(self) -> list[str]:
        if self.CORS_ORIGINS.strip():
            return [o.strip() for o in self.CORS_ORIGINS.split(",") if o.strip()]
        return self.BACKEND_CORS_ORIGINS

    @computed_field  # type: ignore[prop-decorator]
    @property
    def async_sqlalchemy_database_uri(self) -> str:
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}/{self.POSTGRES_DB}"
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_broker_url(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/0"

    @computed_field  # type: ignore[prop-decorator]
    @property
    def celery_result_backend(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"


settings = Settings()
