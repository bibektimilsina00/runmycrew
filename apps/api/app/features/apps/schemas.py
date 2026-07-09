import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel


class PublishAppRequest(SQLModel):
    """Owner-side payload sent when publishing / re-publishing a workflow.

    All fields except ``workflow_id`` (path arg) are optional — when a knob
    is omitted, the trigger's stored value wins. This lets a "quick publish"
    with defaults still work.
    """

    app_slug: str | None = Field(default=None, max_length=128)
    title: str | None = Field(default=None, max_length=255)
    description: str | None = None
    mode: str | None = None
    config: dict[str, Any] | None = None
    auth_mode: str | None = None
    password: str | None = None  # write-only; hashed server-side
    expires_at: datetime | None = None


class PublishedAppOut(SQLModel):
    id: uuid.UUID
    workspace_id: uuid.UUID
    workflow_id: uuid.UUID
    published_by: uuid.UUID
    app_slug: str
    title: str
    description: str | None
    mode: str
    version_num: int
    config: dict[str, Any]
    auth_mode: str
    is_active: bool
    published_at: datetime
    updated_at: datetime
    expires_at: datetime | None
    # Owner-only convenience — the full public URL for the app.
    public_url: str | None = None


class PublicAppOut(SQLModel):
    """The safe subset a public visitor may fetch.

    Notably excludes ``graph_snapshot``, ``password_hash``, ``api_key_hash``,
    and workflow/workspace ids — only what the chat page needs to render.
    """

    id: uuid.UUID
    app_slug: str
    title: str
    description: str | None
    mode: str
    version_num: int
    config: dict[str, Any]
    auth_mode: str
    published_at: datetime
    expires_at: datetime | None


class MessageIn(SQLModel):
    message: str = ""
    form_data: dict[str, Any] = Field(default_factory=dict)
    file_ids: list[uuid.UUID] = Field(default_factory=list)


class MessageOut(SQLModel):
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    artifacts: list[dict[str, Any]]
    execution_id: str | None
    tokens: int
    cost_usd: float
    latency_ms: int
    is_error: bool
    created_at: datetime


class SessionOut(SQLModel):
    id: uuid.UUID
    app_id: uuid.UUID
    cookie_id: str
    user_id: uuid.UUID | None
    first_seen_at: datetime
    last_seen_at: datetime
    message_count: int
    total_cost_usd: float
    total_tokens: int
    is_blocked: bool


class SessionEnvelope(SQLModel):
    """Session bundle returned by GET /session — session row + last N msgs."""

    session: SessionOut
    messages: list[MessageOut]


class SendMessageOut(SQLModel):
    message_id: uuid.UUID
    execution_id: str
    stream_url: str


class RollbackRequest(SQLModel):
    version_num: int


class ApiKeyOut(SQLModel):
    api_key: str  # plain — shown ONCE at generation


class AnalyticsOverview(SQLModel):
    total_sessions: int
    total_messages: int
    total_cost_usd: float
    active_today: int
    messages_today: int
    cost_today: float
    top_prompts: list[dict[str, Any]]
    session_cost_p50: float
    session_cost_p95: float
