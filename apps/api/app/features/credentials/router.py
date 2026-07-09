import secrets
import uuid

import httpx
import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.credential_manager.api_keys import PROVIDERS as API_KEY_PROVIDERS
from apps.api.app.credential_manager.oauth.flow import PROVIDERS as OAUTH_PROVIDERS
from apps.api.app.features.credentials.lookups import LookupResponse, get_lookup_handler
from apps.api.app.features.credentials.schemas import (
    AuditLogOut,
    CredentialCreate,
    CredentialOut,
    CredentialRename,
    OAuthUrlResponse,
    ProviderOut,
)
from apps.api.app.features.credentials.service import CredentialService, get_credential_service
from apps.api.app.features.logs.service import LogsService
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace, WorkspaceMember
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()

MANAGE_ROLES = {"owner", "admin"}


async def _require_manage_credentials(
    current_user: User, workspace: Workspace, db: AsyncSession
) -> None:
    """Only owners and admins can create/rename/delete workspace connections."""
    result = await db.execute(
        sa.select(WorkspaceMember.role).where(
            WorkspaceMember.workspace_id == workspace.id,
            WorkspaceMember.user_id == current_user.id,
        )
    )
    role = result.scalar_one_or_none()
    if role not in MANAGE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only workspace owners and admins can manage connections.",
        )


@router.get("/providers", response_model=list[ProviderOut])
async def list_providers():
    providers = []

    for p in OAUTH_PROVIDERS.values():
        providers.append(
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "description": p.description,
                "icon_slug": p.icon_slug,
                "color": p.color,
                "fields": getattr(p, "fields", None),
                "hint": getattr(p, "hint", None),
                "scopes": getattr(p, "scopes", None),
                "brand": getattr(p, "brand", None),
            }
        )

    for p in API_KEY_PROVIDERS.values():
        providers.append(
            {
                "id": p.id,
                "name": p.name,
                "type": p.type,
                "description": p.description,
                "icon_slug": p.icon_slug,
                "color": p.color,
                "fields": p.fields,
                "hint": p.hint,
                "scopes": getattr(p, "scopes", None),
                "brand": getattr(p, "brand", None),
            }
        )

    return providers


@router.get("/", response_model=list[CredentialOut])
async def list_credentials(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: CredentialService = Depends(get_credential_service),
):
    return await service.list_credentials(current_user, workspace)


@router.get("/audit", response_model=list[AuditLogOut])
async def list_audit_log(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    entries = await LogsService(db).list_for_workspace(
        workspace_id=workspace.id,
        resource_type="credential",
        limit=100,
    )
    return [
        AuditLogOut(
            id=str(e.id),
            action=e.action,
            resource_type=e.resource_type,
            resource_id=e.resource_id,
            resource_name=e.resource_name,
            meta=e.meta,
            created_at=e.created_at.isoformat(),
            user_email=e.user.email if e.user else None,
            user_name=e.user.full_name if e.user else None,
        )
        for e in entries
    ]


@router.post("/", response_model=CredentialOut, status_code=status.HTTP_201_CREATED)
async def create_credential(
    data: CredentialCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    await _require_manage_credentials(current_user, workspace, db)
    credential = await service.store_credential(
        name=data.name,
        type=data.type,
        data=data.data,
        user=current_user,
        workspace=workspace,
    )
    await LogsService(db).log(
        workspace_id=workspace.id,
        user_id=current_user.id,
        action="credential.created",
        resource_type="credential",
        resource_id=str(credential.id),
        resource_name=credential.name,
        meta={"type": credential.type},
    )
    await db.commit()
    return credential


@router.patch("/{credential_id}", response_model=CredentialOut)
async def rename_credential(
    credential_id: uuid.UUID,
    data: CredentialRename,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    await _require_manage_credentials(current_user, workspace, db)
    old = await service.repo.get_by_id_and_workspace(credential_id, workspace.id)
    old_name = old.name if old else str(credential_id)
    credential = await service.rename_credential(credential_id, data.name, current_user, workspace)
    await LogsService(db).log(
        workspace_id=workspace.id,
        user_id=current_user.id,
        action="credential.renamed",
        resource_type="credential",
        resource_id=str(credential.id),
        resource_name=credential.name,
        meta={"old_name": old_name, "new_name": credential.name},
    )
    await db.commit()
    return credential


async def _resolve_google_token(
    credential_id: uuid.UUID,
    workspace: Workspace,
    service: CredentialService,
) -> str:
    """Shared helper — fetch decrypted Google OAuth token for an endpoint.

    Raises 404 if cred not found, 400 if cred has no access_token (e.g. the
    OAuth callback hasn't completed or the row was a stub created during
    install)."""
    cred = await service.repo.get_by_id_and_workspace(credential_id, workspace.id)
    if cred is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    data = await service.get_decrypted_credential(cred)
    access_token = (data or {}).get("access_token") if isinstance(data, dict) else None
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credential has no access_token. Re-connect the account.",
        )
    return str(access_token)


# ── Generic remote-picker dispatcher ──────────────────────────────────
#
# One endpoint drives every FieldSpec that declares `remote=RemoteLookup(...)`.
# The router only routes; the actual "call GitHub / Slack / Notion" logic
# lives in per-node `lookups.py` modules (auto-discovered on boot). New
# picker = 1 handler function + a `remote=` annotation on the manifest
# field. No dispatch table to hand-edit here.
_LOOKUP_RESERVED_PARAMS = {"q", "cursor"}


@router.get("/{credential_id}/lookup/{provider}/{resource}", response_model=LookupResponse)
async def lookup_credential_resource(
    credential_id: uuid.UUID,
    provider: str,
    resource: str,
    request: Request,
    q: str | None = Query(None),
    cursor: str | None = Query(None),
    workspace: Workspace = Depends(get_current_workspace),
    service: CredentialService = Depends(get_credential_service),
) -> LookupResponse:
    """Populate a remote-picker dropdown for a given credential.

    Routes to the handler registered under `(provider, resource)`.
    Non-reserved query params are passed straight through to the
    handler — used for dependent pickers (e.g. `?owner=octocat` when
    listing repos).
    """
    handler = get_lookup_handler(provider, resource)
    if handler is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No lookup handler for {provider}:{resource}",
        )
    cred = await service.repo.get_by_id_and_workspace(credential_id, workspace.id)
    if cred is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    data = await service.get_decrypted_credential(cred)
    if not isinstance(data, dict):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credential is missing decrypted token data.",
        )
    # Pass every non-reserved query param through to the handler as a
    # flat string map. Handlers pick what they need + ignore the rest.
    extra = {k: v for k, v in request.query_params.items() if k not in _LOOKUP_RESERVED_PARAMS}
    async with httpx.AsyncClient(timeout=15.0) as client:
        return await handler(client, data, extra, cursor, q)


# ── Google file pickers (generic — any Google-native mime) ──────────────


# Map Google-native MIME types to the API that creates them. Any mime
# in this table can be created via POST /google-files; others get a 400.
_GOOGLE_CREATE_DISPATCH: dict[str, tuple[str, dict]] = {
    "application/vnd.google-apps.spreadsheet": (
        "https://sheets.googleapis.com/v4/spreadsheets",
        # response keys: id from `spreadsheetId`, name from `properties.title`,
        # link from `spreadsheetUrl`.
        {"id_key": "spreadsheetId", "url_key": "spreadsheetUrl"},
    ),
    "application/vnd.google-apps.document": (
        "https://docs.googleapis.com/v1/documents",
        {"id_key": "documentId", "url_key": None},
    ),
    "application/vnd.google-apps.presentation": (
        "https://slides.googleapis.com/v1/presentations",
        {"id_key": "presentationId", "url_key": None},
    ),
    "application/vnd.google-apps.form": (
        "https://forms.googleapis.com/v1/forms",
        {"id_key": "formId", "url_key": "responderUri"},
    ),
}


# ── Google Tasks tasklist picker ────────────────────────────────────────


# ── Google Contacts (People) group picker ──────────────────────────────


# ── YouTube pickers ────────────────────────────────────────────────────


# ── Google Chat space picker ────────────────────────────────────────────


# ── Google Analytics 4 property picker ──────────────────────────────────


# ── Google Search Console site picker ──────────────────────────────────


# ── Google Cloud Storage bucket picker ─────────────────────────────────


@router.post("/{credential_id}/picker-token")
async def get_picker_token(
    credential_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """Return the fields the Google Picker SDK needs to render its file
    browser against the user's Drive: a fresh OAuth access token from
    the stored credential, plus the workspace's `GOOGLE_API_KEY` (Picker
    developer key) and `GOOGLE_APP_ID` (Cloud project number).

    The endpoint is per-credential because the OAuth token has to be
    the same one the trigger / action node will run against — Picker
    grants `drive.file` access tied to *that* OAuth client, so a
    mismatch would let the user pick a folder the runtime then can't
    see.
    """
    from apps.api.app.core.config import settings

    cred = await service.repo.get_by_id_and_workspace(credential_id, workspace.id)
    if cred is None or cred.user_id != current_user.id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")
    # `get_decrypted_credential` runs the same refresh-if-near-expiry
    # path the runtime hits, so the token we hand to Picker is the same
    # one a polling-trigger HTTP call would use moments later.
    data = await service.get_decrypted_credential(cred)
    access_token = (data or {}).get("access_token") if isinstance(data, dict) else None
    if not access_token:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Credential has no access_token. Re-connect the account.",
        )
    if not settings.GOOGLE_API_KEY or not settings.GOOGLE_APP_ID:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=(
                "Google Picker is not configured on this RunMyCrew instance "
                "(missing GOOGLE_API_KEY / GOOGLE_APP_ID)."
            ),
        )
    return {
        "access_token": access_token,
        "developer_key": settings.GOOGLE_API_KEY,
        "app_id": settings.GOOGLE_APP_ID,
    }


@router.delete("/{credential_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_credential(
    credential_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    await _require_manage_credentials(current_user, workspace, db)
    cred = await service.repo.get_by_id_and_workspace(credential_id, workspace.id)
    cred_name = cred.name if cred else str(credential_id)
    cred_type = cred.type if cred else ""
    await service.delete_credential(credential_id, current_user, workspace)
    await LogsService(db).log(
        workspace_id=workspace.id,
        user_id=current_user.id,
        action="credential.deleted",
        resource_type="credential",
        resource_id=str(credential_id),
        resource_name=cred_name,
        meta={"type": cred_type},
    )
    await db.commit()


@router.get("/oauth/{service_name}/url", response_model=OAuthUrlResponse)
async def get_oauth_url(
    service_name: str,
    name: str | None = None,
    description: str | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _require_manage_credentials(current_user, workspace, db)
    try:
        from apps.api.app.credential_manager.oauth.flow import get_oauth_provider

        provider = get_oauth_provider(service_name)
        if not provider:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown OAuth service: {service_name}",
            )

        # Include metadata in state to retrieve on callback
        import base64
        import hashlib
        import json

        state_data = {
            "nonce": secrets.token_urlsafe(16),
            "name": name,
            "description": description,
            "user_id": str(current_user.id),
            "workspace_id": str(workspace.id),
        }

        # Add PKCE for Slack
        code_challenge = None
        if service_name == "slack":
            code_verifier = secrets.token_urlsafe(64)
            state_data["code_verifier"] = code_verifier
            # SHA256 hash of verifier, then base64url encoded
            challenge_hash = hashlib.sha256(code_verifier.encode()).digest()
            code_challenge = base64.urlsafe_b64encode(challenge_hash).decode().replace("=", "")

        state = base64.urlsafe_b64encode(json.dumps(state_data).encode()).decode()

        if service_name == "slack":
            url = provider.get_authorization_url(state=state, code_challenge=code_challenge)
        else:
            url = provider.get_authorization_url(state=state)

        return OAuthUrlResponse(url=url, state=state)
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth flow not yet implemented",
        ) from exc


@router.get("/oauth/{service_name}/callback")
async def oauth_callback(
    service_name: str,
    code: str,
    state: str,
    db: AsyncSession = Depends(get_db),
):
    try:
        # Decode metadata from state
        import base64
        import binascii
        import json

        try:
            state_data = json.loads(base64.urlsafe_b64decode(state).decode())
            custom_name = state_data.get("name")
            custom_description = state_data.get("description")
            code_verifier = state_data.get("code_verifier")
            user_id = state_data.get("user_id")
            workspace_id = state_data.get("workspace_id")
        except (binascii.Error, UnicodeDecodeError, ValueError):
            custom_name = None
            custom_description = None
            code_verifier = None
            user_id = None
            workspace_id = None

        if not user_id:
            raise HTTPException(status_code=400, detail="Invalid state: user_id missing")
        if not workspace_id:
            raise HTTPException(status_code=400, detail="Invalid state: workspace_id missing")

        from sqlalchemy import select

        from apps.api.app.features.users.models import User

        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        from apps.api.app.features.workspaces.service import WorkspaceService

        workspace = await WorkspaceService(db).resolve_workspace(user, uuid.UUID(workspace_id))

        from apps.api.app.credential_manager.oauth.callback import handle_oauth_callback

        await handle_oauth_callback(
            service_name=service_name,
            code=code,
            user=user,
            workspace=workspace,
            db=db,
            custom_name=custom_name,
            custom_description=custom_description,
            code_verifier=code_verifier,
        )
        from apps.api.app.core.config import settings

        # Redirect back to frontend integrations settings page
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/settings/integrations")
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth callback not yet implemented",
        ) from exc
