from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

ToolParamVisibility = Literal["user-or-llm", "user-only", "llm-only", "hidden"]


@dataclass
class ToolParam:
    type: str  # 'string', 'number', 'boolean', 'json'
    required: bool = False
    visibility: ToolParamVisibility = "user-or-llm"
    description: str = ""


@dataclass
class ToolResult:
    success: bool
    output: dict[str, Any] = field(default_factory=dict)
    error: str | None = None


@dataclass
class ToolOAuth:
    required: bool
    credential_type: str


@dataclass
class ToolRetryConfig:
    enabled: bool = False
    max_retries: int = 3
    initial_delay_ms: int = 1000
    max_delay_ms: int = 10000


@dataclass
class ToolDefinition:
    id: str
    name: str
    description: str
    params: dict[str, ToolParam]
    oauth: ToolOAuth | None = None
    retry: ToolRetryConfig | None = None
