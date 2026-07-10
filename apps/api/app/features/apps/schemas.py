import uuid
from datetime import datetime
from typing import Any

from sqlmodel import Field, SQLModel


class PublicAppOut(SQLModel):
    """Safe subset a visitor may fetch.

    Assembled from the workflow + trigger.chat_app node props at
    request time — no PublishedApp row exists.
    """

    workflow_id: uuid.UUID
    workspace_slug: str
    app_slug: str
    title: str
    description: str | None
    mode: str
    auth_mode: str
    config: dict[str, Any]
    public_url: str | None = None


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
    # One of the two is set — the session's chat-app source.
    workflow_id: uuid.UUID | None = None
    crew_id: uuid.UUID | None = None
    cookie_id: str
    user_id: uuid.UUID | None
    first_seen_at: datetime
    last_seen_at: datetime
    message_count: int
    total_cost_usd: float
    total_tokens: int
    is_blocked: bool


class SessionEnvelope(SQLModel):
    session: SessionOut
    messages: list[MessageOut]


class SendMessageOut(SQLModel):
    message_id: uuid.UUID
    execution_id: str
    stream_url: str


class ApiKeyOut(SQLModel):
    api_key: str  # plain — shown ONCE at generation


class AppPasswordIn(SQLModel):
    password: str | None = None  # None to clear


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
