from __future__ import annotations

import uuid
from typing import Literal

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
from apps.api.app.models.secret import Secret
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace

router = APIRouter()
_enc = AESEncryptionService()

VariableScope = Literal["workspace", "personal"]


# ── Schemas ──────────────────────────────────────────────────────────────────

class SecretCreate(BaseModel):
    name: str = Field(..., min_length=1, max_length=200)
    value: str = Field(default="")
    scope: VariableScope = "workspace"
    is_secret: bool = True


class SecretUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=200)
    value: str | None = None
    scope: VariableScope | None = None
    is_secret: bool | None = None


class SecretOut(BaseModel):
    id: str
    name: str
    # value only returned for non-secrets (is_secret=False)
    value: str | None
    scope: str
    is_secret: bool
    created_at: str
    updated_at: str


class SecretRevealOut(BaseModel):
    id: str
    name: str
    value: str


# ── Helpers ──────────────────────────────────────────────────────────────────

def _normalize_key(key: str) -> str:
    return key.strip().upper().replace(" ", "_").replace("-", "_")


def _to_out(s: Secret) -> SecretOut:
    plain: str | None = None
    if not s.is_secret:
        try:
            plain = _enc.decrypt(s.encrypted_value)
        except Exception:
            plain = s.encrypted_value
    return SecretOut(
        id=str(s.id),
        name=s.name,
        value=plain,
        scope=s.scope,
        is_secret=s.is_secret,
        created_at=s.created_at.isoformat(),
        updated_at=s.updated_at.isoformat(),
    )


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("/", response_model=list[SecretOut])
async def list_secrets(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    # Return workspace-scoped secrets (visible to all) + caller's own personal secrets
    result = await db.execute(
        sa.select(Secret)
        .where(
            Secret.workspace_id == workspace.id,
            sa.or_(
                Secret.scope == "workspace",
                sa.and_(Secret.scope == "personal", Secret.user_id == current_user.id),
            ),
        )
        .order_by(Secret.name)
    )
    return [_to_out(s) for s in result.scalars().all()]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SecretOut)
async def create_secret(
    body: SecretCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    name = _normalize_key(body.name)
    if not name:
        raise HTTPException(status_code=400, detail="Variable name is required.")

    existing = await db.execute(
        sa.select(Secret).where(Secret.workspace_id == workspace.id, Secret.name == name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Variable '{name}' already exists.")

    secret = Secret(
        user_id=current_user.id,
        workspace_id=workspace.id,
        name=name,
        encrypted_value=_enc.encrypt(body.value),
        scope=body.scope,
        is_secret=body.is_secret,
    )
    db.add(secret)
    await db.commit()
    await db.refresh(secret)
    return _to_out(secret)


@router.put("/{secret_id}", response_model=SecretOut)
async def update_secret(
    secret_id: uuid.UUID,
    body: SecretUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        sa.select(Secret).where(Secret.id == secret_id, Secret.workspace_id == workspace.id)
    )
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail="Variable not found.")

    if body.name is not None:
        new_name = _normalize_key(body.name)
        if new_name != secret.name:
            conflict = await db.execute(
                sa.select(Secret).where(
                    Secret.workspace_id == workspace.id,
                    Secret.name == new_name,
                    Secret.id != secret_id,
                )
            )
            if conflict.scalar_one_or_none():
                raise HTTPException(status_code=409, detail=f"Variable '{new_name}' already exists.")
        secret.name = new_name

    if body.value is not None:
        secret.encrypted_value = _enc.encrypt(body.value)
    if body.scope is not None:
        secret.scope = body.scope
    if body.is_secret is not None:
        secret.is_secret = body.is_secret

    await db.commit()
    await db.refresh(secret)
    return _to_out(secret)


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        sa.select(Secret).where(Secret.id == secret_id, Secret.workspace_id == workspace.id)
    )
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail="Variable not found.")
    await db.delete(secret)
    await db.commit()


@router.get("/{secret_id}/reveal", response_model=SecretRevealOut)
async def reveal_secret(
    secret_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Return the decrypted value for a secret variable."""
    result = await db.execute(
        sa.select(Secret).where(Secret.id == secret_id, Secret.workspace_id == workspace.id)
    )
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail="Variable not found.")
    try:
        plain = _enc.decrypt(secret.encrypted_value)
    except Exception:
        plain = secret.encrypted_value
    return SecretRevealOut(id=str(secret.id), name=secret.name, value=plain)
