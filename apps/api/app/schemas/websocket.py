from typing import Any, Literal

from pydantic import BaseModel, Field

ClientCollaborationEventType = Literal[
    "cursor.moved",
    "selection.changed",
    "typing.changed",
    "graph.patch",
    "graph.saved",
    "heartbeat",
]

ServerCollaborationEventType = Literal[
    "session.ready",
    "presence.snapshot",
    "presence.joined",
    "presence.left",
    "cursor.moved",
    "selection.changed",
    "typing.changed",
    "graph.patch",
    "graph.saved",
    "error",
]


class CollaborationClientEvent(BaseModel):
    type: ClientCollaborationEventType
    payload: dict[str, Any] = Field(default_factory=dict)
    patch_id: str | None = None


class CollaborationSession(BaseModel):
    session_id: str
    user_id: str
    user_name: str
    avatar_url: str | None = None
    color: str
    connected_at: str  # ISO 8601 UTC timestamp


class CollaborationServerEvent(BaseModel):
    type: ServerCollaborationEventType
    session: CollaborationSession | None = None
    sessions: list[CollaborationSession] | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    patch_id: str | None = None
