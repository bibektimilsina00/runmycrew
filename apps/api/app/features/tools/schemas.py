"""Pydantic schemas for the tool catalog HTTP surface.

These mirror the dataclasses in `node_system.tools.base` but live here so
the HTTP layer can evolve (versioning, additional metadata, etc.) without
touching the runtime tool model.
"""

from __future__ import annotations

from typing import Any

from sqlmodel import SQLModel


class ToolParamSchema(SQLModel):
    type: str
    required: bool
    visibility: str  # "user-or-llm" | "user-only" | "llm-only" | "hidden"
    description: str


class ToolOAuthSchema(SQLModel):
    required: bool
    credential_type: str


class ToolRetrySchema(SQLModel):
    enabled: bool
    max_retries: int
    initial_delay_ms: int
    max_delay_ms: int


class ToolSchema(SQLModel):
    id: str
    name: str
    description: str
    # Derived from the tool id prefix today (see `service.derive_category`)
    # so older tool definitions need no migration. A future PR can move this
    # into the `ToolDefinition` dataclass itself if registrations want to
    # override the derived value.
    category: str
    category_label: str
    params: dict[str, ToolParamSchema]
    oauth: ToolOAuthSchema | None = None
    retry: ToolRetrySchema | None = None
    requires_auth: bool  # convenience: oauth.required when oauth is set


class ToolCategorySchema(SQLModel):
    id: str
    label: str
    count: int


class ToolListResponse(SQLModel):
    tools: list[ToolSchema]
    # Total count of matched tools (== len(tools) — `limit` not exposed yet
    # but the field keeps the response shape stable for later pagination).
    total: int
    # Categories present in the response so the frontend can group without
    # a second round-trip. Includes counts so the picker can show empties.
    categories: list[ToolCategorySchema]


class ToolCategoryListResponse(SQLModel):
    categories: list[ToolCategorySchema]


# Used by the service as a generic "anything" type alias for clarity.
ToolParamsDict = dict[str, Any]
