import secrets
import uuid
from typing import Any

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.database import get_db
from apps.api.app.credential_manager.api_keys import PROVIDERS as API_KEY_PROVIDERS
from apps.api.app.credential_manager.oauth.flow import PROVIDERS as OAUTH_PROVIDERS
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


@router.get("/{credential_id}/drive/folders")
async def list_drive_folders(
    credential_id: uuid.UUID,
    parent_id: str = "root",
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """Server-proxied Drive folder browser. Avoids the Picker SDK so
    adblockers (which block apis.google.com) don't kill the UX."""
    import asyncio

    import httpx

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

    parent = parent_id or "root"
    headers = {"Authorization": f"Bearer {access_token}"}
    folder_mime = "application/vnd.google-apps.folder"

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            list_resp = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers=headers,
                params={
                    "q": (
                        f"'{parent}' in parents and mimeType = '{folder_mime}' and trashed = false"
                    ),
                    "orderBy": "name",
                    "pageSize": 1000,
                    "fields": "files(id,name)",
                    "supportsAllDrives": "true",
                    "includeItemsFromAllDrives": "true",
                },
            )
            list_resp.raise_for_status()
            folders = list_resp.json().get("files") or []

            parent_meta: dict[str, str] = {"id": parent, "name": "My Drive"}
            if parent != "root":
                meta_resp = await client.get(
                    f"https://www.googleapis.com/drive/v3/files/{parent}",
                    headers=headers,
                    params={"fields": "id,name", "supportsAllDrives": "true"},
                )
                if meta_resp.status_code == 200:
                    body = meta_resp.json()
                    parent_meta = {
                        "id": body.get("id", parent),
                        "name": body.get("name", parent),
                    }

            async def has_kids(folder_id: str) -> bool:
                resp = await client.get(
                    "https://www.googleapis.com/drive/v3/files",
                    headers=headers,
                    params={
                        "q": (
                            f"'{folder_id}' in parents and "
                            f"mimeType = '{folder_mime}' and "
                            "trashed = false"
                        ),
                        "pageSize": 1,
                        "fields": "files(id)",
                        "supportsAllDrives": "true",
                        "includeItemsFromAllDrives": "true",
                    },
                )
                if resp.status_code != 200:
                    return False
                return bool(resp.json().get("files"))

            children_flags = await asyncio.gather(*[has_kids(f.get("id", "")) for f in folders])
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Drive folder list failed ({exc.response.status_code}): {exc.response.text[:200]}"
            ),
        ) from exc

    return {
        "parent": parent_meta,
        "folders": [
            {"id": f.get("id"), "name": f.get("name"), "has_children": flag}
            for f, flag in zip(folders, children_flags, strict=False)
        ],
    }


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


@router.get("/{credential_id}/google-files")
async def list_google_files(
    credential_id: uuid.UUID,
    mime_type: str,
    query: str = "",
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """Generic Google file picker — lists files of the requested MIME type
    via Drive's `files.list`. Used by the inspector's file-picker renderer
    for Sheets / Docs / Slides / folders / any other Google-native type."""
    import httpx

    if not mime_type:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`mime_type` is required.",
        )

    token = await _resolve_google_token(credential_id, workspace, service)
    safe_query = (query or "").strip().replace("'", "\\'")
    safe_mime = mime_type.replace("'", "\\'")
    q_parts = [f"mimeType = '{safe_mime}'", "trashed = false"]
    if safe_query:
        q_parts.append(f"name contains '{safe_query}'")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://www.googleapis.com/drive/v3/files",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "q": " and ".join(q_parts),
                    "orderBy": "modifiedTime desc",
                    "pageSize": max(1, min(int(page_size or 50), 200)),
                    "fields": "files(id,name,modifiedTime,webViewLink,iconLink)",
                    "supportsAllDrives": "true",
                    "includeItemsFromAllDrives": "true",
                },
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(f"Drive list failed ({exc.response.status_code}): {exc.response.text[:200]}"),
        ) from exc

    return {"files": resp.json().get("files") or []}


@router.post("/{credential_id}/google-files", status_code=status.HTTP_201_CREATED)
async def create_google_file(
    credential_id: uuid.UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """Create a new Google-native file (Sheet / Doc / Slides) of the
    requested mime type. Routes to the right native API based on
    `_GOOGLE_CREATE_DISPATCH`. Returns `{id, name, webViewLink}`."""
    import httpx

    mime = str((payload or {}).get("mime_type") or "").strip()
    title = str((payload or {}).get("title") or "").strip()
    if not mime:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`mime_type` is required.",
        )
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`title` is required.",
        )
    if mime not in _GOOGLE_CREATE_DISPATCH:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Mime type {mime!r} is not creatable via this endpoint.",
        )

    token = await _resolve_google_token(credential_id, workspace, service)
    endpoint, response_shape = _GOOGLE_CREATE_DISPATCH[mime]

    # Shape the create body per surface. Sheets accepts an optional
    # initial-tabs list; other surfaces only take a title.
    if mime == "application/vnd.google-apps.spreadsheet":
        body: dict = {"properties": {"title": title}}
        raw_sheets = (payload or {}).get("sheet_titles") or []
        if isinstance(raw_sheets, list):
            sheet_titles = [str(t) for t in raw_sheets if str(t).strip()]
            if sheet_titles:
                body["sheets"] = [{"properties": {"title": t}} for t in sheet_titles]
    elif mime in (
        "application/vnd.google-apps.document",
        "application/vnd.google-apps.presentation",
    ):
        body = {"title": title}
    elif mime == "application/vnd.google-apps.form":
        # Forms wraps the title under `info`; the API rejects the bare
        # `{title}` shape with a 400.
        body = {"info": {"title": title, "documentTitle": title}}
    else:  # pragma: no cover - guarded above
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="unreachable")

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                endpoint,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=body,
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(f"Create failed ({exc.response.status_code}): {exc.response.text[:200]}"),
        ) from exc

    data = resp.json()
    file_id = data.get(response_shape["id_key"])
    name = (
        ((data.get("properties") or {}).get("title"))
        or ((data.get("info") or {}).get("title"))
        or data.get("title")
        or title
    )
    return {
        "id": file_id,
        "name": name,
        "webViewLink": data.get(response_shape["url_key"]) if response_shape["url_key"] else None,
        "mime_type": mime,
    }


@router.get("/{credential_id}/sheets/spreadsheets/{spreadsheet_id}/tabs")
async def list_sheets_tabs(
    credential_id: uuid.UUID,
    spreadsheet_id: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List the sheets (tabs) inside a spreadsheet — id, title, and
    zero-based index — for the tab-picker dropdown."""
    import httpx

    token = await _resolve_google_token(credential_id, workspace, service)

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                f"https://sheets.googleapis.com/v4/spreadsheets/{spreadsheet_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"fields": "sheets.properties(sheetId,title,index)"},
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Sheets tab list failed ({exc.response.status_code}): {exc.response.text[:200]}"
            ),
        ) from exc

    tabs = []
    for sheet in resp.json().get("sheets") or []:
        props = (sheet or {}).get("properties") or {}
        tabs.append(
            {
                "sheet_id": int(props.get("sheetId") or 0),
                "title": str(props.get("title") or ""),
                "index": int(props.get("index") or 0),
            }
        )
    tabs.sort(key=lambda t: t["index"])
    return {"tabs": tabs}


# ── Google Tasks tasklist picker ────────────────────────────────────────


@router.get("/{credential_id}/gtasks/tasklists")
async def list_gtasks_tasklists(
    credential_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List the user's Google Tasks tasklists — backs the tasklist
    picker on the Tasks action node + trigger."""
    import httpx

    token = await _resolve_google_token(credential_id, workspace, service)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://tasks.googleapis.com/tasks/v1/users/@me/lists",
                headers={"Authorization": f"Bearer {token}"},
                params={"maxResults": 100},
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(f"Tasks list failed ({exc.response.status_code}): {exc.response.text[:200]}"),
        ) from exc

    items = resp.json().get("items") or []
    tasklists = [
        {
            "id": str(item.get("id") or ""),
            "title": str(item.get("title") or ""),
            "updated": str(item.get("updated") or ""),
        }
        for item in items
        if item.get("id")
    ]
    return {"tasklists": tasklists}


@router.post("/{credential_id}/gtasks/tasklists", status_code=status.HTTP_201_CREATED)
async def create_gtasks_tasklist(
    credential_id: uuid.UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """Create a new Google Tasks tasklist — used by the picker's inline
    "+ Create new tasklist" CTA. Returns the new tasklist so the picker
    can auto-select it."""
    import httpx

    title = str((payload or {}).get("title") or "").strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`title` is required.",
        )

    token = await _resolve_google_token(credential_id, workspace, service)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://tasks.googleapis.com/tasks/v1/users/@me/lists",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"title": title},
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(f"Tasks create failed ({exc.response.status_code}): {exc.response.text[:200]}"),
        ) from exc

    data = resp.json()
    return {
        "id": str(data.get("id") or ""),
        "title": str(data.get("title") or title),
        "updated": str(data.get("updated") or ""),
    }


# ── Google Contacts (People) group picker ──────────────────────────────


@router.get("/{credential_id}/gpeople/groups")
async def list_gpeople_groups(
    credential_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List the user's contact groups (labels). Backs the group picker
    on the Contacts action node."""
    import httpx

    token = await _resolve_google_token(credential_id, workspace, service)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://people.googleapis.com/v1/contactGroups",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "pageSize": 200,
                    "groupFields": "name,memberCount,groupType",
                },
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Contact groups list failed ({exc.response.status_code}): "
                f"{exc.response.text[:200]}"
            ),
        ) from exc

    groups = [
        {
            "resource_name": g.get("resourceName"),
            "name": g.get("formattedName") or g.get("name") or "",
            "member_count": int(g.get("memberCount") or 0),
            "type": g.get("groupType") or "",
        }
        for g in (resp.json().get("contactGroups") or [])
        if g.get("resourceName")
    ]
    return {"groups": groups}


@router.post("/{credential_id}/gpeople/groups", status_code=status.HTTP_201_CREATED)
async def create_gpeople_group(
    credential_id: uuid.UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """Create a new contact group from inside the picker."""
    import httpx

    name = str((payload or {}).get("name") or "").strip()
    if not name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`name` is required.",
        )
    token = await _resolve_google_token(credential_id, workspace, service)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://people.googleapis.com/v1/contactGroups",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json={"contactGroup": {"name": name}},
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(f"Create group failed ({exc.response.status_code}): {exc.response.text[:200]}"),
        ) from exc

    data = resp.json()
    return {
        "resource_name": data.get("resourceName"),
        "name": data.get("formattedName") or data.get("name") or name,
        "member_count": int(data.get("memberCount") or 0),
        "type": data.get("groupType") or "",
    }


# ── YouTube pickers ────────────────────────────────────────────────────


@router.get("/{credential_id}/youtube/videos")
async def list_youtube_videos(
    credential_id: uuid.UUID,
    query: str = "",
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List the signed-in account's own uploaded videos. Backs the
    youtube-video picker on the YouTube action node."""
    import httpx

    token = await _resolve_google_token(credential_id, workspace, service)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            ch_resp = await client.get(
                "https://www.googleapis.com/youtube/v3/channels",
                headers={"Authorization": f"Bearer {token}"},
                params={"part": "contentDetails", "mine": "true"},
            )
            ch_resp.raise_for_status()
            ch_items = ch_resp.json().get("items") or []
            if not ch_items:
                return {"videos": []}
            uploads = ((ch_items[0].get("contentDetails") or {}).get("relatedPlaylists") or {}).get(
                "uploads"
            ) or ""
            if not uploads:
                return {"videos": []}

            pl_resp = await client.get(
                "https://www.googleapis.com/youtube/v3/playlistItems",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "part": "contentDetails,snippet",
                    "playlistId": uploads,
                    "maxResults": max(1, min(int(page_size or 50), 50)),
                },
            )
            pl_resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"YouTube videos list failed ({exc.response.status_code}): "
                f"{exc.response.text[:200]}"
            ),
        ) from exc

    q = (query or "").strip().lower()
    items = pl_resp.json().get("items") or []
    videos = []
    for i in items:
        snippet = i.get("snippet") or {}
        vid = ((i.get("contentDetails") or {}).get("videoId")) or ""
        title = snippet.get("title") or ""
        if q and q not in title.lower():
            continue
        thumb = ((snippet.get("thumbnails") or {}).get("default") or {}).get("url") or ""
        videos.append(
            {
                "id": vid,
                "title": title,
                "channel_title": snippet.get("channelTitle") or "",
                "published_at": snippet.get("publishedAt") or "",
                "thumbnail_url": thumb,
            }
        )
    return {"videos": videos}


@router.get("/{credential_id}/youtube/playlists")
async def list_youtube_playlists(
    credential_id: uuid.UUID,
    query: str = "",
    page_size: int = 50,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List the user's playlists. Backs the youtube-playlist picker."""
    import httpx

    token = await _resolve_google_token(credential_id, workspace, service)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://www.googleapis.com/youtube/v3/playlists",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "part": "snippet,contentDetails,status",
                    "mine": "true",
                    "maxResults": max(1, min(int(page_size or 50), 50)),
                },
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"YouTube playlists list failed ({exc.response.status_code}): "
                f"{exc.response.text[:200]}"
            ),
        ) from exc

    q = (query or "").strip().lower()
    items = resp.json().get("items") or []
    playlists = []
    for p in items:
        snippet = p.get("snippet") or {}
        title = snippet.get("title") or ""
        if q and q not in title.lower():
            continue
        playlists.append(
            {
                "id": p.get("id"),
                "title": title,
                "description": snippet.get("description") or "",
                "item_count": int((p.get("contentDetails") or {}).get("itemCount") or 0),
                "privacy": (p.get("status") or {}).get("privacyStatus") or "",
            }
        )
    return {"playlists": playlists}


@router.post("/{credential_id}/youtube/playlists", status_code=status.HTTP_201_CREATED)
async def create_youtube_playlist(
    credential_id: uuid.UUID,
    payload: dict,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """Create a new playlist from inside the picker."""
    import httpx

    title = str((payload or {}).get("title") or "").strip()
    if not title:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`title` is required.",
        )
    privacy = str((payload or {}).get("privacy") or "private")
    token = await _resolve_google_token(credential_id, workspace, service)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://www.googleapis.com/youtube/v3/playlists",
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                params={"part": "snippet,status"},
                json={
                    "snippet": {"title": title},
                    "status": {"privacyStatus": privacy},
                },
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"Create playlist failed ({exc.response.status_code}): {exc.response.text[:200]}"
            ),
        ) from exc

    data = resp.json()
    return {
        "id": data.get("id"),
        "title": ((data.get("snippet") or {}).get("title")) or title,
        "description": (data.get("snippet") or {}).get("description") or "",
        "item_count": 0,
        "privacy": (data.get("status") or {}).get("privacyStatus") or privacy,
    }


@router.get("/{credential_id}/youtube/channels")
async def search_youtube_channels(
    credential_id: uuid.UUID,
    query: str,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """Search channels by name or @handle. Backs the youtube-channel
    picker on the YouTube action node + trigger."""
    import httpx

    q = (query or "").strip()
    if not q:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`query` is required.",
        )

    token = await _resolve_google_token(credential_id, workspace, service)
    # `@handle` lookups go through the channels endpoint directly;
    # free-text searches use the search endpoint.
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            if q.startswith("@"):
                ch_resp = await client.get(
                    "https://www.googleapis.com/youtube/v3/channels",
                    headers={"Authorization": f"Bearer {token}"},
                    params={"part": "snippet,statistics", "forHandle": q},
                )
                ch_resp.raise_for_status()
                items = ch_resp.json().get("items") or []
                channels = [
                    {
                        "id": c.get("id"),
                        "title": (c.get("snippet") or {}).get("title") or "",
                        "handle": q,
                        "subscriber_count": int(
                            (c.get("statistics") or {}).get("subscriberCount") or 0
                        ),
                        "thumbnail_url": (
                            ((c.get("snippet") or {}).get("thumbnails") or {}).get("default") or {}
                        ).get("url")
                        or "",
                    }
                    for c in items
                ]
                return {"channels": channels}

            r = await client.get(
                "https://www.googleapis.com/youtube/v3/search",
                headers={"Authorization": f"Bearer {token}"},
                params={
                    "part": "snippet",
                    "type": "channel",
                    "q": q,
                    "maxResults": 25,
                },
            )
            r.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=(
                f"YouTube channel search failed ({exc.response.status_code}): "
                f"{exc.response.text[:200]}"
            ),
        ) from exc

    items = r.json().get("items") or []
    channels = [
        {
            "id": ((item.get("id") or {}).get("channelId") or item.get("id") or ""),
            "title": (item.get("snippet") or {}).get("title") or "",
            "description": (item.get("snippet") or {}).get("description") or "",
            "thumbnail_url": (
                ((item.get("snippet") or {}).get("thumbnails") or {}).get("default") or {}
            ).get("url")
            or "",
        }
        for item in items
    ]
    return {"channels": channels}


# ── Google Chat space picker ────────────────────────────────────────────


@router.get("/{credential_id}/gchat/spaces")
async def list_gchat_spaces(
    credential_id: uuid.UUID,
    q: str | None = None,
    space_type: str | None = None,
    page_token: str | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List the user's Google Chat spaces — backs the gchat-space picker
    on the Chat action node + trigger.

    ``q`` (optional) does a client-side substring match on display name
    once the API returns. ``space_type`` (``SPACE`` / ``DIRECT_MESSAGE``
    / ``GROUP_CHAT``) maps to the Chat API's CEL filter on space type.
    """
    import httpx

    token = await _resolve_google_token(credential_id, workspace, service)

    params: dict[str, Any] = {"pageSize": 100}
    if page_token:
        params["pageToken"] = page_token
    if space_type and space_type.upper() in {"SPACE", "DIRECT_MESSAGE", "GROUP_CHAT"}:
        params["filter"] = f'spaceType = "{space_type.upper()}"'

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://chat.googleapis.com/v1/spaces",
                headers={"Authorization": f"Bearer {token}"},
                params=params,
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        from apps.api.app.node_system.nodes.google.gchat.gchat_node import format_chat_error

        # Reuse the same hint logic the action / trigger use so the
        # picker dropdown shows the user *what to fix* (enable the
        # product, enable the API in GCP, re-OAuth, etc) rather than
        # just the raw API body.
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=format_chat_error(exc.response.status_code, exc.response.text),
        ) from exc

    data = resp.json() or {}
    needle = (q or "").strip().lower()
    spaces = []
    for item in data.get("spaces") or []:
        # Resource name is `spaces/AAAA`; expose the bare id so the
        # frontend can also show the human-readable display name. The
        # node-side validator accepts both forms.
        name = str(item.get("name") or "")
        space_id = name.split("/", 1)[1] if name.startswith("spaces/") else name
        display = str(item.get("displayName") or "")
        if needle and needle not in display.lower() and needle not in space_id.lower():
            continue
        spaces.append(
            {
                "id": space_id,
                "name": name,
                "displayName": display,
                "type": str(item.get("spaceType") or item.get("type") or ""),
                "singleUserBotDm": bool(item.get("singleUserBotDm") or False),
            }
        )

    return {
        "spaces": spaces,
        "nextPageToken": data.get("nextPageToken") or "",
    }


# ── Google Analytics 4 property picker ──────────────────────────────────


@router.get("/{credential_id}/ga4/properties")
async def list_ga4_properties(
    credential_id: uuid.UUID,
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List GA4 properties the connected account can see — backs the
    ``ga4-property`` picker on the Analytics action node.

    The Admin API lists properties one account at a time, so we first
    fetch every visible account (paginating), then issue one parallel
    ``properties.list`` per account. The result is flattened into
    ``{id, name, displayName, account, accountDisplayName}`` so the
    frontend can show a grouped, searchable list. ``q`` does a
    client-side substring match across display name + property id.
    """
    import asyncio

    import httpx

    from apps.api.app.node_system.nodes.google.ga4.ga4_node import format_ga4_error

    token = await _resolve_google_token(credential_id, workspace, service)
    admin = "https://analyticsadmin.googleapis.com/v1beta"
    auth_headers = {"Authorization": f"Bearer {token}"}

    async def _all_accounts(client: httpx.AsyncClient) -> list[dict[str, Any]]:
        accounts: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {"pageSize": 200}
            if page_token:
                params["pageToken"] = page_token
            resp = await client.get(f"{admin}/accounts", headers=auth_headers, params=params)
            resp.raise_for_status()
            data = resp.json() or {}
            for acc in data.get("accounts") or []:
                accounts.append(acc)
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return accounts

    async def _props_for(client: httpx.AsyncClient, account_name: str) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = []
        page_token: str | None = None
        while True:
            params: dict[str, Any] = {
                "pageSize": 200,
                "filter": f"parent:{account_name}",
            }
            if page_token:
                params["pageToken"] = page_token
            resp = await client.get(f"{admin}/properties", headers=auth_headers, params=params)
            resp.raise_for_status()
            data = resp.json() or {}
            for p in data.get("properties") or []:
                out.append(p)
            page_token = data.get("nextPageToken")
            if not page_token:
                break
        return out

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            accounts = await _all_accounts(client)
            # Map account-name → displayName so we can label rows.
            account_label = {
                str(a.get("name") or ""): str(a.get("displayName") or "") for a in accounts
            }
            if not accounts:
                return {"properties": []}
            tasks = [_props_for(client, str(a.get("name") or "")) for a in accounts]
            per_account = await asyncio.gather(*tasks)
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=format_ga4_error(exc.response.status_code, exc.response.text),
        ) from exc

    needle = (q or "").strip().lower()
    properties: list[dict[str, Any]] = []
    for batch in per_account:
        for p in batch:
            name = str(p.get("name") or "")  # e.g. "properties/123456789"
            pid = name.split("/", 1)[1] if name.startswith("properties/") else name
            display = str(p.get("displayName") or "")
            parent = str(p.get("parent") or "")  # "accounts/..."
            if needle and needle not in display.lower() and needle not in pid.lower():
                continue
            properties.append(
                {
                    "id": pid,
                    "name": name,
                    "displayName": display,
                    "account": parent,
                    "accountDisplayName": account_label.get(parent, ""),
                    "currencyCode": str(p.get("currencyCode") or ""),
                    "timeZone": str(p.get("timeZone") or ""),
                }
            )

    return {"properties": properties}


# ── Google Search Console site picker ──────────────────────────────────


@router.get("/{credential_id}/gsc/sites")
async def list_gsc_sites(
    credential_id: uuid.UUID,
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List Search Console properties the connected account has access
    to — backs the ``gsc-site`` picker.

    ``q`` does a case-insensitive substring match on the site URL so
    users with dozens of verified properties can find one fast.
    Returns rows like ``{siteUrl, permissionLevel, kind}`` — siteUrl
    is the literal URL the API uses as an identifier (no transformation).
    """
    import httpx

    from apps.api.app.node_system.nodes.google.gsc.gsc_node import format_gsc_error

    token = await _resolve_google_token(credential_id, workspace, service)
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.get(
                "https://www.googleapis.com/webmasters/v3/sites",
                headers={"Authorization": f"Bearer {token}"},
            )
            resp.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=format_gsc_error(exc.response.status_code, exc.response.text),
        ) from exc

    data = resp.json() or {}
    needle = (q or "").strip().lower()
    sites: list[dict[str, Any]] = []
    for entry in data.get("siteEntry") or []:
        site_url = str(entry.get("siteUrl") or "")
        if not site_url:
            continue
        if needle and needle not in site_url.lower():
            continue
        sites.append(
            {
                "siteUrl": site_url,
                "permissionLevel": str(entry.get("permissionLevel") or ""),
                # `sc-domain:` rows are domain properties; URL-prefix
                # rows look like a real URL. Surface a hint so the
                # frontend can icon them differently.
                "isDomainProperty": site_url.startswith("sc-domain:"),
            }
        )

    return {"sites": sites}


# ── Google Cloud Storage bucket picker ─────────────────────────────────


@router.get("/{credential_id}/gcs/buckets")
async def list_gcs_buckets(
    credential_id: uuid.UUID,
    project_id: str,
    q: str | None = None,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
    service: CredentialService = Depends(get_credential_service),
):
    """List Cloud Storage buckets in a GCP project — backs the
    ``gcs-bucket`` picker. ``project_id`` is required because the
    Storage API scopes bucket lists to one project at a time.
    """
    import httpx

    from apps.api.app.node_system.nodes.google.gcs.gcs_node import format_gcs_error

    project = project_id.strip()
    if not project:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="`project_id` is required.",
        )

    token = await _resolve_google_token(credential_id, workspace, service)
    needle = (q or "").strip().lower()
    buckets: list[dict[str, Any]] = []
    page_token: str | None = None

    try:
        async with httpx.AsyncClient(timeout=30) as client:
            while True:
                params: dict[str, Any] = {"project": project, "maxResults": 200}
                if page_token:
                    params["pageToken"] = page_token
                resp = await client.get(
                    "https://storage.googleapis.com/storage/v1/b",
                    headers={"Authorization": f"Bearer {token}"},
                    params=params,
                )
                resp.raise_for_status()
                data = resp.json() or {}
                for entry in data.get("items") or []:
                    name = str(entry.get("name") or "")
                    if not name:
                        continue
                    if needle and needle not in name.lower():
                        continue
                    buckets.append(
                        {
                            "name": name,
                            "location": str(entry.get("location") or ""),
                            "storageClass": str(entry.get("storageClass") or ""),
                            "created": str(entry.get("timeCreated") or ""),
                        }
                    )
                page_token = data.get("nextPageToken")
                if not page_token:
                    break
    except httpx.HTTPStatusError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=format_gcs_error(exc.response.status_code, exc.response.text),
        ) from exc

    return {"buckets": buckets}


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

        # Redirect to the frontend's `/oauth/return` landing page. That
        # component reads the return path the initiating tab stashed in
        # `sessionStorage` and bounces the user back to it — so an
        # inspector-triggered OAuth returns to the inspector, not the
        # dashboard.
        return RedirectResponse(url=f"{settings.FRONTEND_URL}/oauth/return")
    except ImportError as exc:
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="OAuth callback not yet implemented",
        ) from exc
