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
    # Phase 4 (loop hardening): free-form tags + dangerous flag let the
    # agent inspector surface "this tool can write" without parsing names,
    # and `tags` powers the search bar across registered tools.
    tags: list[str] = []
    dangerous: bool = False


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


# ──────────────────────────────────────────────────────────────────────────
#  MCP probe
# ──────────────────────────────────────────────────────────────────────────


class McpProbeRequest(SQLModel):
    """Payload for `POST /tools/mcp/probe` — validates an MCP server and
    returns its discovered tool list without saving anything."""

    url: str
    api_key: str | None = None


class McpProbeTool(SQLModel):
    """One discovered MCP tool — id is namespaced by server, so the agent
    runtime can route calls when this server gets saved."""

    id: str
    name: str
    description: str


class McpProbeResponse(SQLModel):
    success: bool
    tools: list[McpProbeTool]
    # Server-reported error string when reachable but failing; transport
    # errors come through as HTTP-level errors and never reach this body.
    error: str | None = None


# Used by the service as a generic "anything" type alias for clarity.
ToolParamsDict = dict[str, Any]
