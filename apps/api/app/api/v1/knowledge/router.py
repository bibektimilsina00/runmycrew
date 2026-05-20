from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.api.v1.auth.dependencies import get_current_user
from apps.api.app.api.v1.workspaces.dependencies import get_current_workspace
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.models.user import User
from apps.api.app.models.workspace import Workspace
from apps.api.app.repositories.credential_repository import CredentialRepository
from apps.api.app.repositories.knowledge_repository import KnowledgeRepository
from apps.api.app.services.credential_service import CredentialService
from apps.api.app.services.knowledge_service import KnowledgeService

logger = get_logger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

class KBCreate(BaseModel):
    name: str
    description: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_credential_id: uuid.UUID | None = None


class KBOut(BaseModel):
    id: uuid.UUID
    name: str
    description: str | None
    embedding_model: str
    embedding_credential_id: uuid.UUID | None
    document_count: int = 0
    created_at: str

    model_config = {"from_attributes": True}


class DocumentOut(BaseModel):
    id: uuid.UUID
    name: str
    source_type: str
    chunk_count: int
    created_at: str

    model_config = {"from_attributes": True}


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class AddTextRequest(BaseModel):
    name: str
    text: str


# ── Helpers ────────────────────────────────────────────────────────────────────

async def _get_api_key(
    kb,
    db: AsyncSession,
    user_id: uuid.UUID,
    override_credential_id: uuid.UUID | None = None,
) -> str:
    cred_id = override_credential_id or kb.embedding_credential_id
    if not cred_id:
        raise HTTPException(status_code=400, detail="No embedding credential set on this knowledge base.")
    cred_repo = CredentialRepository(db)
    cred = await cred_repo.get_by_id_and_user(cred_id, user_id)
    if not cred:
        raise HTTPException(status_code=404, detail="Embedding credential not found.")
    cred_service = CredentialService(db)
    decrypted = await cred_service.get_decrypted_credential(cred)
    api_key = decrypted.get("api_key")
    if not api_key:
        raise HTTPException(status_code=400, detail="Credential has no api_key field.")
    return api_key


async def _require_kb(kb_id: uuid.UUID, user_id: uuid.UUID, db: AsyncSession):
    repo = KnowledgeRepository(db)
    kb = await repo.get_kb(kb_id, user_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")
    return kb


# ── Knowledge Base CRUD ────────────────────────────────────────────────────────

@router.get("/list-options")
async def list_kb_options(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """loadOptions endpoint for the Knowledge node dropdown."""
    repo = KnowledgeRepository(db)
    kbs = await repo.list_kbs(workspace.id)
    return {"ok": True, "data": [{"label": kb.name, "value": str(kb.id)} for kb in kbs]}


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_kb(
    body: KBCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)
    kb = await svc.create_kb(
        user_id=current_user.id,
        workspace_id=workspace.id,
        name=body.name,
        description=body.description,
        embedding_model=body.embedding_model,
        embedding_credential_id=body.embedding_credential_id,
    )
    return {
        "id": str(kb.id),
        "name": kb.name,
        "description": kb.description,
        "embedding_model": kb.embedding_model,
        "embedding_credential_id": str(kb.embedding_credential_id) if kb.embedding_credential_id else None,
        "document_count": 0,
        "created_at": kb.created_at.isoformat(),
    }


@router.get("/")
async def list_kbs(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = KnowledgeRepository(db)
    kbs = await repo.list_kbs(workspace.id)
    result = []
    for kb in kbs:
        docs = await repo.list_documents(kb.id)
        result.append({
            "id": str(kb.id),
            "name": kb.name,
            "description": kb.description,
            "embedding_model": kb.embedding_model,
            "embedding_credential_id": str(kb.embedding_credential_id) if kb.embedding_credential_id else None,
            "document_count": len(docs),
            "created_at": kb.created_at.isoformat(),
        })
    return result


@router.get("/{kb_id}")
async def get_kb(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    repo = KnowledgeRepository(db)
    docs = await repo.list_documents(kb.id)
    return {
        "id": str(kb.id),
        "name": kb.name,
        "description": kb.description,
        "embedding_model": kb.embedding_model,
        "embedding_credential_id": str(kb.embedding_credential_id) if kb.embedding_credential_id else None,
        "document_count": len(docs),
        "created_at": kb.created_at.isoformat(),
        "documents": [
            {
                "id": str(d.id),
                "name": d.name,
                "source_type": d.source_type,
                "chunk_count": d.chunk_count,
                "created_at": d.created_at.isoformat(),
            }
            for d in docs
        ],
    }


@router.patch("/{kb_id}")
async def update_kb(
    kb_id: uuid.UUID,
    body: KBCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    repo = KnowledgeRepository(db)
    kb = await repo.update_kb(
        kb,
        name=body.name,
        description=body.description,
        embedding_model=body.embedding_model,
        embedding_credential_id=body.embedding_credential_id,
    )
    return {"id": str(kb.id), "name": kb.name}


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_kb(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    repo = KnowledgeRepository(db)
    await repo.delete_kb(kb)


# ── Documents ──────────────────────────────────────────────────────────────────

@router.post("/{kb_id}/documents/text", status_code=status.HTTP_201_CREATED)
async def add_text_document(
    kb_id: uuid.UUID,
    body: AddTextRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    api_key = await _get_api_key(kb, db, current_user.id)
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)
    try:
        doc = await svc.add_document_from_text(kb, body.name, body.text, api_key)
    except Exception as e:
        logger.error(f"Text document ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"id": str(doc.id), "name": doc.name, "chunk_count": doc.chunk_count}


@router.post("/{kb_id}/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    api_key = await _get_api_key(kb, db, current_user.id)

    content = await file.read()
    filename = file.filename or "upload"
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)

    try:
        if filename.lower().endswith(".pdf"):
            doc = await svc.add_document_from_pdf(kb, filename, content, api_key)
        else:
            text = content.decode("utf-8", errors="replace")
            doc = await svc.add_document_from_text(kb, filename, text, api_key)
    except Exception as e:
        logger.error(f"File upload ingestion failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e)) from e

    return {"id": str(doc.id), "name": doc.name, "chunk_count": doc.chunk_count}


@router.delete("/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _require_kb(kb_id, workspace.id, db)
    repo = KnowledgeRepository(db)
    doc = await repo.get_document(doc_id, kb_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    await repo.delete_document(doc)


# ── Search ─────────────────────────────────────────────────────────────────────

@router.post("/{kb_id}/search")
async def search(
    kb_id: uuid.UUID,
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    api_key = await _get_api_key(kb, db, current_user.id)
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)
    try:
        results = await svc.search(kb, body.query, api_key, body.top_k)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) from e
    return {"query": body.query, "results": results, "count": len(results)}
