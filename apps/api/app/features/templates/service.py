"""Template marketplace business rules.

Holds the parts of the flow that are NOT just DB plumbing — slug
generation, creator-only updates, premium gating, graph scrubbing,
and the "publish workflow → template" + "install template → workflow"
glue.
"""

from __future__ import annotations

import copy
import re
import uuid
from typing import Any
from uuid import UUID

from fastapi import Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.features.users.models import User
from apps.api.app.features.workflows.models import Workflow
from apps.api.app.features.workflows.repository import WorkflowRepository
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.node_system.registry.registry import node_registry

from .models import Template, TemplatePurchase
from .repository import SortKey, TemplatePurchaseRepository, TemplateRepository
from .schemas import (
    CreatorOut,
    InstallResultOut,
    PublishTemplateIn,
    TemplateCategorySchema,
    TemplateDetailOut,
    TemplateListOut,
    TemplateListResponse,
    UpdateTemplateIn,
)

_CATEGORY_LABELS: dict[str, str] = {
    "revenue-ops": "Revenue ops",
    "engineering": "Engineering",
    "inbox": "Inbox",
    "reporting": "Reporting",
    "sales": "Sales",
    "loops": "Loops",
}


def _slugify(text: str) -> str:
    """URL-safe slug — lowercase, hyphen-separated, ascii-only.

    Treats underscores as word separators so ids like
    ``loop_linear_triage`` become ``loop-linear-triage`` instead of
    being smushed into ``looplineartriage``.
    """
    cleaned = re.sub(r"[^a-zA-Z0-9\s_-]", "", text).strip().lower()
    cleaned = re.sub(r"[\s_-]+", "-", cleaned)
    return cleaned.strip("-")[:140] or "template"


class TemplateService:
    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.repo = TemplateRepository(db)
        self.purchases = TemplatePurchaseRepository(db)

    # ── Public reads ─────────────────────────────────────────────────

    async def list_marketplace(
        self,
        *,
        category: str | None,
        kind: str | None,
        q: str | None,
        sort: SortKey,
        limit: int,
        offset: int,
    ) -> TemplateListResponse:
        rows, total = await self.repo.list_published(
            category=category, kind=kind, q=q, sort=sort, limit=limit, offset=offset
        )
        creators = await self.repo.fetch_creators(rows)
        return TemplateListResponse(
            items=[self._to_list_out(t, creators.get(t.creator_id)) for t in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_public(
        self,
        *,
        category: str | None = None,
        limit: int = 60,
        offset: int = 0,
    ) -> TemplateListResponse:
        """Anonymous marketing endpoint — only official, published rows.

        Sorted by featured first then newest so the curated entries lead
        the grid. Creator lookup is skipped because every row is
        first-party.
        """
        rows, total = await self.repo.list_published(
            category=category,
            kind=None,
            q=None,
            sort="newest",
            limit=limit,
            offset=offset,
            official_only=True,
        )
        rows.sort(key=lambda t: (not t.featured, -int(t.created_at.timestamp())))
        return TemplateListResponse(
            items=[self._to_list_out(t, None) for t in rows],
            total=total,
            limit=limit,
            offset=offset,
        )

    async def list_categories(self) -> list[TemplateCategorySchema]:
        counts = await self.repo.category_counts()
        return [
            TemplateCategorySchema(
                id=key, label=_CATEGORY_LABELS.get(key, key.title()), count=count
            )
            for key, count in sorted(counts.items())
        ]

    async def get_detail(self, slug_or_id: str) -> TemplateDetailOut:
        template = await self._resolve(slug_or_id)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        creator = await self.repo.fetch_creator(template)
        return self._to_detail_out(template, creator)

    async def list_mine(self, user: User) -> list[TemplateListOut]:
        rows = await self.repo.list_by_creator(user.id)
        creators = await self.repo.fetch_creators(rows)
        return [self._to_list_out(t, creators.get(t.creator_id)) for t in rows]

    # ── Writes ───────────────────────────────────────────────────────

    async def publish_from_workflow(
        self,
        data: PublishTemplateIn,
        user: User,
        workspace: Workspace,
    ) -> TemplateListOut:
        """Snapshot the user's workflow into a fresh marketplace row.

        The graph is fetched server-side and scrubbed — credential ids are
        replaced with empty strings so installs don't inherit the
        publisher's tokens. credentials_required + tools_required are
        derived from the scrubbed graph so the install-time
        missing-credentials check has accurate data.
        """
        workflow_repo = WorkflowRepository(self.db)
        workflow = await workflow_repo.get_by_id_and_workspace(data.workflow_id, workspace.id)
        if workflow is None or workflow.user_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")

        scrubbed_graph, creds_required, tools_required = _prepare_graph_snapshot(workflow.graph)

        slug = await self._unique_slug(data.title)
        template = Template(
            creator_id=user.id,
            workspace_id=workspace.id,
            slug=slug,
            title=data.title.strip(),
            summary=data.summary.strip(),
            description=data.description,
            category=data.category,
            kind=data.kind,
            graph=scrubbed_graph,
            credentials_required=creds_required,
            tools_required=tools_required,
            bg_variant=data.bg_variant,
            is_published=True,
            is_official=False,
            is_premium=bool(data.is_premium),
            price_cents=max(0, int(data.price_cents or 0)) if data.is_premium else 0,
        )
        created = await self.repo.create(template)
        return self._to_list_out(created, user)

    async def update_template(
        self, template_id: UUID, data: UpdateTemplateIn, user: User
    ) -> TemplateListOut:
        template = await self._owned_or_404(template_id, user)
        if data.title is not None:
            template.title = data.title.strip()
        if data.summary is not None:
            template.summary = data.summary.strip()
        if data.description is not None:
            template.description = data.description
        if data.category is not None:
            template.category = data.category
        if data.kind is not None:
            template.kind = data.kind
        if data.bg_variant is not None:
            template.bg_variant = data.bg_variant
        if data.is_published is not None:
            template.is_published = data.is_published
        if data.is_premium is not None:
            template.is_premium = data.is_premium
            if not data.is_premium:
                template.price_cents = 0
        if data.price_cents is not None and template.is_premium:
            template.price_cents = max(0, int(data.price_cents))
        updated = await self.repo.update(template)
        return self._to_list_out(updated, user)

    async def delete_template(self, template_id: UUID, user: User) -> None:
        template = await self._owned_or_404(template_id, user)
        await self.repo.delete(template)

    async def install(
        self,
        template_id_or_slug: str,
        user: User,
        workspace: Workspace,
    ) -> InstallResultOut:
        """Create a workflow from the template + record the install."""
        template = await self._resolve(template_id_or_slug)
        if template is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        if not template.is_published:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Template not available"
            )

        # Premium gate: paid templates require a recorded purchase OR
        # ownership (creator gets free access). We return 402 so the
        # frontend can distinguish "you need to buy this" from a generic
        # 403.
        is_owner = template.creator_id == user.id
        if template.is_premium and not is_owner:
            already_bought = await self.purchases.is_owned_by(template.id, user.id)
            if not already_bought:
                raise HTTPException(
                    status_code=status.HTTP_402_PAYMENT_REQUIRED,
                    detail="Purchase required to install this template",
                )

        workflow = Workflow(
            user_id=user.id,
            workspace_id=workspace.id,
            name=template.title,
            description=template.summary or None,
            graph=copy.deepcopy(template.graph),
        )
        self.db.add(workflow)
        await self.db.commit()
        await self.db.refresh(workflow)

        await self.repo.increment_download(template.id)

        # Record the install as a zero-cost purchase row even when the
        # template is free; lets the dashboard count "installed by user"
        # without a separate downloads table. Skip when the user has
        # already installed it once — second install is a re-deploy.
        if not await self.purchases.is_owned_by(template.id, user.id):
            await self.purchases.record(
                TemplatePurchase(
                    template_id=template.id,
                    user_id=user.id,
                    workspace_id=workspace.id,
                    price_cents=0 if not template.is_premium else template.price_cents,
                )
            )

        return InstallResultOut(
            workflow_id=workflow.id,
            message=f"Installed '{template.title}'",
        )

    # ── Helpers ──────────────────────────────────────────────────────

    async def _resolve(self, slug_or_id: str) -> Template | None:
        try:
            template_id = uuid.UUID(slug_or_id)
            return await self.repo.get_by_id(template_id)
        except ValueError:
            return await self.repo.get_by_slug(slug_or_id)

    async def _owned_or_404(self, template_id: UUID, user: User) -> Template:
        template = await self.repo.get_by_id(template_id)
        if template is None or template.creator_id != user.id:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Template not found")
        return template

    async def _unique_slug(self, title: str) -> str:
        base = _slugify(title)
        candidate = base
        suffix = 1
        while await self.repo.slug_exists(candidate):
            suffix += 1
            candidate = f"{base}-{suffix}"
        return candidate

    def _to_list_out(self, t: Template, creator: User | None = None) -> TemplateListOut:
        return TemplateListOut(
            id=t.id,
            slug=t.slug,
            title=t.title,
            summary=t.summary,
            category=t.category,
            kind=t.kind,
            bg_variant=t.bg_variant,
            is_official=t.is_official,
            is_published=t.is_published,
            is_premium=t.is_premium,
            price_cents=t.price_cents,
            download_count=t.download_count,
            steps=_count_steps(t.graph),
            featured=t.featured,
            creator=_creator_to_out(creator) if not t.is_official else None,
            tools_required=list(t.tools_required or []),
            graph=t.graph or {"nodes": [], "edges": []},
            created_at=t.created_at,
            updated_at=t.updated_at,
        )

    def _to_detail_out(self, t: Template, creator: User | None = None) -> TemplateDetailOut:
        # graph + tools_required live on the base list payload now, so
        # don't pass them again — would crash with "multiple values for
        # keyword argument".
        base = self._to_list_out(t, creator)
        return TemplateDetailOut(
            **base.model_dump(),
            description=t.description,
            credentials_required=t.credentials_required,
        )


def _count_steps(graph: dict[str, Any]) -> int:
    """Card field — show node count as the "steps" badge."""
    return len(graph.get("nodes", []) or [])


def _creator_to_out(user: User | None) -> CreatorOut | None:
    if user is None:
        return None
    return CreatorOut(
        id=user.id,
        full_name=user.full_name,
        email=user.email,
        avatar_url=user.avatar_url,
    )


def _prepare_graph_snapshot(
    graph: dict[str, Any],
) -> tuple[dict[str, Any], list[str], list[str]]:
    """Deep-copy + scrub the graph for marketplace publication.

    Replaces every credential id reference inside node properties with
    an empty string — installs must connect their own integrations.
    Returns the scrubbed graph plus the derived
    `credentials_required` + `tools_required` lists so the install-time
    check has accurate metadata without scanning the graph again.
    """
    snapshot = copy.deepcopy(graph) if graph else {"nodes": [], "edges": []}
    creds: set[str] = set()
    tools: set[str] = set()

    for node in snapshot.get("nodes", []) or []:
        if not isinstance(node, dict):
            continue
        node_type = str(node.get("type") or "")
        # A node is an integration iff its definition declares a
        # credential type — core nodes (agent, http_request, condition…)
        # don't. `tools_required` is presentational (the install-time
        # check reads `credentials_required`), so store the brand-icon
        # slug when the node has one, else the type suffix.
        node_cls = node_registry.find(node_type)
        meta = node_cls.get_metadata() if node_cls else None
        if meta and meta.credential_type:
            icon = (meta.icon or "").strip()
            is_brand_slug = bool(icon) and icon == icon.lower()
            tools.add(icon if is_brand_slug else node_type.split(".", 1)[-1])
        data = node.get("data") or {}
        props = data.get("properties") if isinstance(data, dict) else None
        if not isinstance(props, dict):
            continue

        for key in ("credential", "credential_id", "credentialId"):
            if key in props and props[key]:
                creds.add(str(node_type) or "credential")
                props[key] = ""

        # Common multi-credential property names that some integrations
        # use for primary/secondary OAuth tokens.
        for key in list(props.keys()):
            if key.lower().endswith("credential") and isinstance(props[key], str) and props[key]:
                creds.add(str(node_type) or "credential")
                props[key] = ""

    return snapshot, sorted(creds), sorted(tools)


def get_template_service(db: AsyncSession = Depends(get_db)) -> TemplateService:
    return TemplateService(db)
