from __future__ import annotations

import uuid

import sqlalchemy as sa
from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.core.database import get_db
from apps.api.app.credential_manager.encryption.aes import AESEncryptionService
from apps.api.app.models.secret import Secret
from apps.api.app.models.user import User

router = APIRouter()
_enc = AESEncryptionService()


class SecretCreate(BaseModel):
    name: str
    value: str


class SecretUpdate(BaseModel):
    name: str | None = None
    value: str | None = None


class SecretOut(BaseModel):
    id: str
    name: str
    created_at: str
    updated_at: str


@router.get("/", response_model=list[SecretOut])
async def list_secrets(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        sa.select(Secret)
        .where(Secret.user_id == current_user.id)
        .order_by(Secret.name)
    )
    secrets = result.scalars().all()
    return [
        SecretOut(id=str(s.id), name=s.name, created_at=s.created_at.isoformat(), updated_at=s.updated_at.isoformat())
        for s in secrets
    ]


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=SecretOut)
async def create_secret(
    body: SecretCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    name = body.name.strip().upper().replace(" ", "_")
    if not name:
        raise HTTPException(status_code=400, detail="Secret name is required.")

    # Check uniqueness per user
    existing = await db.execute(
        sa.select(Secret).where(Secret.user_id == current_user.id, Secret.name == name)
    )
    if existing.scalar_one_or_none():
        raise HTTPException(status_code=409, detail=f"Secret '{name}' already exists.")

    secret = Secret(
        user_id=current_user.id,
        name=name,
        encrypted_value=_enc.encrypt(body.value),
    )
    db.add(secret)
    await db.commit()
    await db.refresh(secret)
    return SecretOut(id=str(secret.id), name=secret.name, created_at=secret.created_at.isoformat(), updated_at=secret.updated_at.isoformat())


@router.put("/{secret_id}", response_model=SecretOut)
async def update_secret(
    secret_id: uuid.UUID,
    body: SecretUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        sa.select(Secret).where(Secret.id == secret_id, Secret.user_id == current_user.id)
    )
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found.")

    if body.name is not None:
        secret.name = body.name.strip().upper().replace(" ", "_")
    if body.value is not None:
        secret.encrypted_value = _enc.encrypt(body.value)

    await db.commit()
    await db.refresh(secret)
    return SecretOut(id=str(secret.id), name=secret.name, created_at=secret.created_at.isoformat(), updated_at=secret.updated_at.isoformat())


@router.delete("/{secret_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_secret(
    secret_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        sa.select(Secret).where(Secret.id == secret_id, Secret.user_id == current_user.id)
    )
    secret = result.scalar_one_or_none()
    if not secret:
        raise HTTPException(status_code=404, detail="Secret not found.")
    await db.delete(secret)
    await db.commit()
