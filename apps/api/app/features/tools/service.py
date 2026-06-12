"""Service layer for the tool catalog HTTP endpoints.

Reads from the runtime `tool_registry` and serialises into the HTTP schemas
defined in :mod:`schemas`. The categorisation lives here (not in the
registry) so changing the category-derivation rule never touches the tool
definitions themselves.
"""

from __future__ import annotations

from dataclasses import asdict

# Trigger registration side-effects so every built-in tool is in the
# registry when the service starts handling requests.
import apps.api.app.node_system.tools.loader  # noqa: F401  (re-export side effect)
from apps.api.app.features.tools.schemas import (
    ToolCategorySchema,
    ToolListResponse,
    ToolOAuthSchema,
    ToolParamSchema,
    ToolRetrySchema,
    ToolSchema,
)
from apps.api.app.node_system.tools.base import ToolDefinition
from apps.api.app.node_system.tools.registry import tool_registry

# Pretty labels for known categories. Unknown categories fall back to
# title-casing the derived id.
_CATEGORY_LABELS: dict[str, str] = {
    "slack": "Slack",
    "http": "HTTP",
    "workflow": "Workflow",
    "mcp": "MCP",
}


def derive_category(tool_id: str) -> str:
    """Return the lowercased category bucket for a tool id.

    Uses the first underscore-separated segment of the id (`slack_send_message`
    → `slack`). When the id has no underscore the whole id becomes the
    category — keeps single-name tools like `http` working without a special
    case.
    """
    head, _, _ = tool_id.partition("_")
    return head or tool_id


def label_for_category(category: str) -> str:
    return _CATEGORY_LABELS.get(category, category.replace("_", " ").title())


def _serialize_tool(definition: ToolDefinition) -> ToolSchema:
    category = derive_category(definition.id)
    return ToolSchema(
        id=definition.id,
        name=definition.name,
        description=definition.description,
        category=category,
        category_label=label_for_category(category),
        params={
            name: ToolParamSchema(
                type=param.type,
                required=param.required,
                visibility=param.visibility,
                description=param.description,
            )
            for name, param in definition.params.items()
        },
        oauth=ToolOAuthSchema(**asdict(definition.oauth)) if definition.oauth else None,
        retry=ToolRetrySchema(**asdict(definition.retry)) if definition.retry else None,
        requires_auth=bool(definition.oauth and definition.oauth.required),
    )


def _matches_filters(
    tool: ToolSchema,
    q: str | None,
    category: str | None,
    requires_auth: bool | None,
) -> bool:
    if category and tool.category != category:
        return False
    if requires_auth is not None and tool.requires_auth != requires_auth:
        return False
    if q:
        needle = q.lower().strip()
        if needle and not (
            needle in tool.id.lower()
            or needle in tool.name.lower()
            or needle in tool.description.lower()
        ):
            return False
    return True


class ToolCatalogService:
    """Stateless serialiser over the global tool registry.

    Constructed per-request via the FastAPI dependency to keep the class
    cheap to instantiate; the registry singleton is what owns the data.
    """

    def list_tools(
        self,
        q: str | None = None,
        category: str | None = None,
        requires_auth: bool | None = None,
    ) -> ToolListResponse:
        all_serialized = [_serialize_tool(d) for d in tool_registry.list_definitions()]
        all_serialized.sort(key=lambda t: (t.category, t.name.lower()))

        matched = [t for t in all_serialized if _matches_filters(t, q, category, requires_auth)]

        # Categories are derived from the **matched** set so the frontend
        # picker can render group headers without round-tripping.
        counts: dict[str, int] = {}
        for tool in matched:
            counts[tool.category] = counts.get(tool.category, 0) + 1
        categories = [
            ToolCategorySchema(id=cat, label=label_for_category(cat), count=count)
            for cat, count in sorted(counts.items())
        ]

        return ToolListResponse(tools=matched, total=len(matched), categories=categories)

    def get_tool(self, tool_id: str) -> ToolSchema | None:
        definition = tool_registry.get_definition(tool_registry.resolve_tool_id(tool_id))
        if definition is None:
            return None
        return _serialize_tool(definition)

    def list_categories(self) -> list[ToolCategorySchema]:
        counts: dict[str, int] = {}
        for definition in tool_registry.list_definitions():
            cat = derive_category(definition.id)
            counts[cat] = counts.get(cat, 0) + 1
        return [
            ToolCategorySchema(id=cat, label=label_for_category(cat), count=count)
            for cat, count in sorted(counts.items())
        ]


def get_tool_catalog_service() -> ToolCatalogService:
    return ToolCatalogService()
