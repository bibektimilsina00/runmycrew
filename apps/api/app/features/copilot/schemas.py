from typing import Any

from sqlmodel import Field, SQLModel


class CopilotSettingsBody(SQLModel):
    provider: str = "anthropic"
    model: str = ""
    credential_id: str | None = None
    model_mode: str = "dynamic"  # "manual" | "dynamic"


class ChatMessage(SQLModel):
    role: str
    content: str


class CopilotChatRequest(SQLModel):
    messages: list[ChatMessage]
    graph: dict[str, Any] | None = None  # if None, load from DB
    provider: str = "anthropic"
    model: str | None = None
    credential_id: str | None = None
    session_id: str | None = None


class SessionItem(SQLModel):
    id: str
    title: str
    created_at: str | None = None
    updated_at: str | None = None


class SessionListResponse(SQLModel):
    sessions: list[SessionItem]


class SessionDetailResponse(SessionItem):
    messages: list[dict[str, Any]] = Field(default_factory=list)


class CopilotCredential(SQLModel):
    id: str
    name: str


class CopilotProvider(SQLModel):
    id: str
    name: str
    credentialType: str
    defaultModel: str
    hasCredential: bool
    credentials: list[CopilotCredential] = Field(default_factory=list)


class CopilotProvidersResponse(SQLModel):
    providers: list[CopilotProvider]
