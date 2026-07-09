"""Owner-side endpoints: publish, unpublish, list versions, analytics.

Mounted under the /workflows router — all endpoints route through
``/workflows/{workflow_id}/app...`` so app management lives alongside the
workflow it belongs to.
"""

import uuid

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.features.apps.schemas import (
    PublishAppRequest,
    PublishedAppOut,
)
from apps.api.app.features.apps.service import PublishedAppService
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.features.workspaces.service import WorkspaceService
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


def _to_public_url(workspace_slug: str, app_slug: str) -> str:
    base = getattr(settings, "PUBLIC_APP_BASE_URL", None) or ""
    base = base.rstrip("/")
    return (
        f"{base}/apps/{workspace_slug}/{app_slug}" if base else f"/apps/{workspace_slug}/{app_slug}"
    )


@router.post(
    "/{workflow_id}/publish",
    response_model=PublishedAppOut,
    status_code=status.HTTP_201_CREATED,
)
async def publish_workflow(
    workflow_id: uuid.UUID,
    data: PublishAppRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Publish (or re-publish) the workflow at this ID as a hosted app."""
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    service = PublishedAppService(db)
    app = await service.publish(workflow_id, data, current_user, workspace)
    return _wrap(app, workspace.slug)


@router.delete(
    "/{workflow_id}/publish",
    status_code=status.HTTP_204_NO_CONTENT,
    response_class=Response,
)
async def unpublish_workflow(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await WorkspaceService(db).require_edit(workspace.id, current_user)
    await PublishedAppService(db).unpublish(workflow_id, current_user, workspace)


@router.get("/{workflow_id}/app", response_model=PublishedAppOut | None)
async def get_current_app(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    app = await PublishedAppService(db).get_for_workflow(workflow_id, workspace)
    return _wrap(app, workspace.slug) if app else None


@router.get("/{workflow_id}/app/versions", response_model=list[PublishedAppOut])
async def list_versions(
    workflow_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    versions = await PublishedAppService(db).list_versions(workflow_id, workspace)
    return [_wrap(v, workspace.slug) for v in versions]


def _wrap(app, workspace_slug: str) -> PublishedAppOut:
    return PublishedAppOut(
        id=app.id,
        workspace_id=app.workspace_id,
        workflow_id=app.workflow_id,
        published_by=app.published_by,
        app_slug=app.app_slug,
        title=app.title,
        description=app.description,
        mode=app.mode,
        version_num=app.version_num,
        config=app.config or {},
        auth_mode=app.auth_mode,
        is_active=app.is_active,
        published_at=app.published_at,
        updated_at=app.updated_at,
        expires_at=app.expires_at,
        public_url=_to_public_url(workspace_slug, app.app_slug),
    )
