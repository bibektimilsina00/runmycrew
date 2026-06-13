from pathlib import Path

from pydantic import Field, computed_field, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    PROJECT_NAME: str = "Fuse"
    API_V1_STR: str = "/api/v1"
    SECRET_KEY: str = "development_secret_key_change_me"
    ENCRYPTION_KEY: str = "ZqprL7EBBN63_Nk0a_MoJyMTTrqf06xWY_3oTibUXAY="
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    ALGORITHM: str = "HS256"
    BASE_URL: str = "http://localhost:8000"
    FRONTEND_URL: str = "http://localhost:5173"
    BACKEND_CORS_ORIGINS: list[str] = Field(
        default_factory=lambda: [
            "http://localhost:5173",
            "http://127.0.0.1:5173",
        ]
    )

    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "fuse"

    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379

    SLACK_CLIENT_ID: str = ""
    SLACK_CLIENT_SECRET: str = ""

    GITHUB_CLIENT_ID: str = ""
    GITHUB_CLIENT_SECRET: str = ""

    NOTION_CLIENT_ID: str = ""
    NOTION_CLIENT_SECRET: str = ""

    DISCORD_CLIENT_ID: str = ""
    DISCORD_CLIENT_SECRET: str = ""
    DISCORD_BOT_TOKEN: str = ""

    LINEAR_CLIENT_ID: str = ""
    LINEAR_CLIENT_SECRET: str = ""

    # Meta (Facebook + Instagram + WhatsApp + Messenger). One developer app
    # backs every Meta product. The verify token is the shared secret used
    # for the webhook subscription handshake (Meta calls our endpoint with
    # `hub.verify_token` — we echo `hub.challenge` only if it matches).
    META_APP_ID: str = ""
    META_APP_SECRET: str = ""
    META_WEBHOOK_VERIFY_TOKEN: str = ""
    META_GRAPH_API_VERSION: str = "v20.0"

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

    # Email (SMTP) — works with Gmail, SendGrid, Mailgun, SES, etc.
    SMTP_HOST: str = ""
    SMTP_PORT: int = 587
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM: str = "noreply@fuse.app"
    SMTP_FROM_NAME: str = "Fuse"
    SMTP_TLS: bool = True

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
