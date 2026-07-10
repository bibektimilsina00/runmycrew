"""Service layer for the tool catalog HTTP endpoints.

Reads from the runtime `tool_registry` and serialises into the HTTP schemas
defined in :mod:`schemas`. The categorisation lives here (not in the
registry) so changing the category-derivation rule never touches the tool
definitions themselves.
"""

from __future__ import annotations

from dataclasses import asdict
from typing import Any

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

# Trigger registration side-effects so every built-in tool is in the
# registry when the service starts handling requests.
import apps.api.app.node_system.tools.loader  # noqa: F401  (re-export side effect)
from apps.api.app.core.database import get_db
from apps.api.app.features.tools.schemas import (
    McpProbeResponse,
    McpProbeTool,
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
    # Explicit category on the definition wins; otherwise we fall back to
    # the historical "first id segment" derivation so older tool entries
    # still bucket correctly.
    category = definition.category or derive_category(definition.id)
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
        tags=list(definition.tags),
        dangerous=definition.dangerous,
    )


def _matches_filters(
    tool: ToolSchema,
    q: str | None,
    category: str | None,
    requires_auth: bool | None,
    tag: str | None = None,
    dangerous: bool | None = None,
) -> bool:
    if category and tool.category != category:
        return False
    if requires_auth is not None and tool.requires_auth != requires_auth:
        return False
    if tag and tag not in tool.tags:
        return False
    if dangerous is not None and tool.dangerous != dangerous:
        return False
    if q:
        needle = q.lower().strip()
        if needle and not (
            needle in tool.id.lower()
            or needle in tool.name.lower()
            or needle in tool.description.lower()
            or any(needle in t.lower() for t in tool.tags)
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
        tag: str | None = None,
        dangerous: bool | None = None,
    ) -> ToolListResponse:
        all_serialized = [_serialize_tool(d) for d in tool_registry.list_definitions()]
        all_serialized.sort(key=lambda t: (t.category, t.name.lower()))

        matched = [
            t
            for t in all_serialized
            if _matches_filters(t, q, category, requires_auth, tag=tag, dangerous=dangerous)
        ]

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


# ──────────────────────────────────────────────────────────────────────────
#  Workflow-as-tool catalog
# ──────────────────────────────────────────────────────────────────────────


class WorkflowToolsService:
    """Serialises a workspace's saved workflows into ToolSchemas.

    Each workflow becomes one selectable tool — id ``workflow:<uuid>``,
    params lifted from the trigger node's ``input_schema``. The agent's
    tool-execution loop strips the ``workflow:`` prefix and routes to the
    generic ``workflow_executor`` with the resolved id pre-bound.
    """

    def __init__(self, db: Any) -> None:
        # Local import to keep the module light-weight at import time.
        from apps.api.app.features.workflows.repository import WorkflowRepository

        self._repository = WorkflowRepository(db)

    async def list_for_user(self, current_user: Any, workspace: Any) -> ToolListResponse:
        workflows = await self._repository.list_by_workspace(workspace.id)
        tools: list[ToolSchema] = []
        for workflow in workflows:
            tool = self._serialize_workflow(workflow)
            if tool is not None:
                tools.append(tool)
        tools.sort(key=lambda t: t.name.lower())

        # Always one category; the picker still groups under "Workflow"
        # alongside the built-in catalog so the user sees both in one panel.
        categories: list[ToolCategorySchema] = (
            [ToolCategorySchema(id="workflow", label="Workflow", count=len(tools))] if tools else []
        )
        return ToolListResponse(tools=tools, total=len(tools), categories=categories)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _serialize_workflow(workflow: Any) -> ToolSchema | None:
        params = WorkflowToolsService._extract_params(workflow)
        name = workflow.name or "Untitled workflow"
        description = workflow.description or f"Run the workflow “{name}” as a tool."
        return ToolSchema(
            id=f"workflow:{workflow.id}",
            name=name,
            description=description,
            category="workflow",
            category_label="Workflow",
            params=params,
            oauth=None,
            retry=None,
            requires_auth=False,
        )

    @staticmethod
    def _extract_params(workflow: Any) -> dict[str, ToolParamSchema]:
        """Pull the trigger node's input_schema and shape it as tool params.

        Every input becomes a `user-or-llm` param so the LLM can fill it from
        what the agent's reasoning produces, but the inspector still lets the
        user pin a preset value (which wins via the merge in
        ``agent.py _resolve_tools``).
        """
        graph = workflow.graph or {}
        nodes = graph.get("nodes") or []
        params: dict[str, ToolParamSchema] = {}
        for node in nodes:
            if not isinstance(node, dict):
                continue
            if node.get("type") != "trigger.form":
                continue
            data = node.get("data") or {}
            properties = data.get("properties") or {}
            # The Form trigger's field rows: {name, type, value}.
            input_schema = properties.get("inputs") or []
            if not isinstance(input_schema, list):
                continue
            for entry in input_schema:
                if not isinstance(entry, dict):
                    continue
                name = entry.get("name")
                if not isinstance(name, str) or not name:
                    continue
                params[name] = ToolParamSchema(
                    type=str(entry.get("type") or "string"),
                    required=bool(entry.get("required", False)),
                    visibility="user-or-llm",
                    description=str(entry.get("description") or ""),
                )
            break
        return params


def get_workflow_tools_service(
    db: AsyncSession = Depends(get_db),
) -> WorkflowToolsService:
    return WorkflowToolsService(db)


# ──────────────────────────────────────────────────────────────────────────
#  MCP server probe
# ──────────────────────────────────────────────────────────────────────────


class McpProbeService:
    """Validates an MCP server URL by calling its `tools/list` method.

    Returns the discovered tool list so the inspector can preview what
    the agent will see at run time. Transport errors raise as
    HTTPException; server-reported errors land in the response's
    ``error`` field with ``success=False``.
    """

    async def probe(self, url: str, api_key: str | None) -> McpProbeResponse:
        # Local import — keeps the MCP module out of the cold-path import
        # graph for callers that never use this endpoint.
        from apps.api.app.node_system.tools.mcp.client import MCPClient

        # `server_name` only affects the tool id namespacing in the
        # response — the probe never stores anything, so a stable preview
        # value is enough.
        client = MCPClient(server_name="probe", url=url, api_key=api_key)
        try:
            definitions = await client.list_tools()
        except Exception as exc:
            return McpProbeResponse(success=False, tools=[], error=str(exc))

        tools = [McpProbeTool(id=d.id, name=d.name, description=d.description) for d in definitions]
        return McpProbeResponse(success=True, tools=tools, error=None)


def get_mcp_probe_service() -> McpProbeService:
    return McpProbeService()
