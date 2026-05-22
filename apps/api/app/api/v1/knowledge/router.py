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
from apps.api.app.services.knowledge_service import KnowledgeService, _provider_from_model

logger = get_logger(__name__)
router = APIRouter()


# ── Schemas ────────────────────────────────────────────────────────────────────

TOKENS_TO_CHARS = 4  # 1 token ≈ 4 characters


class KBCreate(BaseModel):
    name: str
    description: str | None = None
    embedding_model: str = "text-embedding-3-small"
    embedding_credential_id: uuid.UUID | None = None
    min_chunk_size: int = 100                  # characters
    max_chunk_tokens: int = 1024               # tokens  → stored as chars
    overlap_tokens: int = 200                  # tokens  → stored as chars
    chunking_strategy: str = "auto"


class KBOut(BaseModel):
    id: str
    name: str
    description: str | None
    embedding_model: str
    embedding_credential_id: str | None
    document_count: int
    total_chunks: int
    min_chunk_size: int
    max_chunk_tokens: int   # chunk_size chars ÷ 4
    overlap_tokens: int     # chunk_overlap chars ÷ 4
    chunking_strategy: str
    created_at: str


class DocumentOut(BaseModel):
    id: str
    name: str
    source_type: str
    chunk_count: int
    status: str  # pending | indexed | failed | partial
    created_at: str


class AddUrlRequest(BaseModel):
    url: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5


class AddTextRequest(BaseModel):
    name: str
    text: str


# ── Helpers ────────────────────────────────────────────────────────────────────

EMBEDDING_CRED_TYPES = ["openai_api_key", "mistral_api_key", "google_api_key"]

# Map model name patterns → credential type
MODEL_CRED_TYPE: dict[str, str] = {
    "text-embedding-3-small": "openai_api_key",
    "text-embedding-3-large": "openai_api_key",
    "text-embedding-ada-002":  "openai_api_key",
    "text-embedding-004":     "google_api_key",
    "mistral-embed":          "mistral_api_key",
}


def _cred_type_for_model(model: str) -> str:
    """Return the credential type that matches the embedding model."""
    if model in MODEL_CRED_TYPE:
        return MODEL_CRED_TYPE[model]
    if "mistral" in model:
        return "mistral_api_key"
    if "gemini" in model or "embedding-004" in model:
        return "google_api_key"
    return "openai_api_key"


def _handle_ingestion_error(e: Exception) -> None:
    """Convert common embedding errors into useful 400s instead of opaque 500s."""
    msg = str(e)
    if "401" in msg or "Unauthorized" in msg or "Invalid API key" in msg:
        raise HTTPException(
            status_code=400,
            detail="Embedding credential rejected (401 Unauthorized). "
                   "The API key may be invalid or expired — update it in Connections.",
        )
    if "429" in msg or "Too Many Requests" in msg or "Rate limit" in msg:
        raise HTTPException(
            status_code=400,
            detail="Embedding API rate limit hit. Wait a moment and try again.",
        )
    if "quota" in msg.lower() or "insufficient_quota" in msg:
        raise HTTPException(
            status_code=400,
            detail="Embedding API quota exceeded. Check your API key billing in the provider dashboard.",
        )
    raise HTTPException(status_code=500, detail=f"Ingestion failed: {msg}")


async def _get_api_key(
    kb,
    db: AsyncSession,
    workspace_id: uuid.UUID,
) -> str:
    """Return the API key for the KB's embedding model.

    Priority:
    1. The explicitly saved embedding_credential_id (only if it matches the model's provider).
    2. Auto-select the first credential in the workspace that matches the model's provider.
    Never falls back to a different provider — that caused wrong-model 401 errors.
    """
    cred_repo = CredentialRepository(db)
    cred_service = CredentialService(db)
    required_cred_type = _cred_type_for_model(kb.embedding_model or "text-embedding-3-small")

    # 1. Try the explicitly configured credential — but only if it matches the model's provider
    if kb.embedding_credential_id:
        cred = await cred_repo.get_by_id_and_workspace(kb.embedding_credential_id, workspace_id)
        if cred and cred.type == required_cred_type:
            decrypted = await cred_service.get_decrypted_credential(cred)
            api_key = decrypted.get("api_key")
            if api_key:
                return api_key

    # 2. Auto-select the first matching credential for this model's provider
    cred = await cred_repo.get_first_by_type_and_workspace(required_cred_type, workspace_id)
    if cred:
        decrypted = await cred_service.get_decrypted_credential(cred)
        api_key = decrypted.get("api_key")
        if api_key:
            # Persist so future calls skip the lookup
            kb.embedding_credential_id = cred.id
            await db.commit()
            return api_key

    provider = required_cred_type.replace("_api_key", "").title()
    raise HTTPException(
        status_code=400,
        detail=(
            f"No {provider} credential found for model '{kb.embedding_model}'. "
            f"Add a {provider} API key in Connections, or switch to a different model in KB settings."
        ),
    )


async def _require_kb(kb_id: uuid.UUID, workspace_id: uuid.UUID, db: AsyncSession):
    repo = KnowledgeRepository(db)
    kb = await repo.get_kb(kb_id, workspace_id)
    if not kb:
        raise HTTPException(status_code=404, detail="Knowledge base not found.")
    return kb


async def _kb_out(kb, repo: KnowledgeRepository) -> dict:
    docs = await repo.list_documents(kb.id)
    total_chunks = await repo.count_chunks_for_kb(kb.id)
    return {
        "id": str(kb.id),
        "name": kb.name,
        "description": kb.description,
        "embedding_model": kb.embedding_model,
        "embedding_credential_id": str(kb.embedding_credential_id) if kb.embedding_credential_id else None,
        "document_count": len(docs),
        "total_chunks": total_chunks,
        "min_chunk_size": getattr(kb, "min_chunk_size", 100),
        "max_chunk_tokens": getattr(kb, "chunk_size", 4096) // TOKENS_TO_CHARS,
        "overlap_tokens": getattr(kb, "chunk_overlap", 800) // TOKENS_TO_CHARS,
        "chunking_strategy": getattr(kb, "chunking_strategy", "auto"),
        "created_at": kb.created_at.isoformat(),
    }


def _document_out(doc) -> dict:
    return {
        "id": str(doc.id),
        "name": doc.name,
        "source_type": doc.source_type,
        "chunk_count": doc.chunk_count,
        "status": doc.status,
        "created_at": doc.created_at.isoformat(),
    }


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
        min_chunk_size=body.min_chunk_size,
        chunk_size=body.max_chunk_tokens * TOKENS_TO_CHARS,
        chunk_overlap=body.overlap_tokens * TOKENS_TO_CHARS,
        chunking_strategy=body.chunking_strategy,
    )
    return await _kb_out(kb, repo)


@router.get("/")
async def list_kbs(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    repo = KnowledgeRepository(db)
    kbs = await repo.list_kbs(workspace.id)
    return [await _kb_out(kb, repo) for kb in kbs]


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
    total_chunks = await repo.count_chunks_for_kb(kb.id)
    return {
        **await _kb_out(kb, repo),
        "total_chunks": total_chunks,
        "documents": [
            {
                "id": str(d.id),
                "name": d.name,
                "source_type": d.source_type,
                "chunk_count": d.chunk_count,
                "status": d.status,
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
        embedding_provider=_provider_from_model(body.embedding_model),
        embedding_credential_id=body.embedding_credential_id,
        min_chunk_size=max(50, body.min_chunk_size),
        chunk_size=max(200, min(body.max_chunk_tokens * TOKENS_TO_CHARS, 32000)),
        chunk_overlap=max(
            0,
            min(
                body.overlap_tokens * TOKENS_TO_CHARS,
                (body.max_chunk_tokens * TOKENS_TO_CHARS) // 2,
            ),
        ),
        chunking_strategy=body.chunking_strategy,
    )
    return await _kb_out(kb, repo)


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
    api_key = await _get_api_key(kb, db, workspace.id)
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)
    try:
        doc = await svc.add_document_from_text(kb, body.name, body.text, api_key)
        doc.status = "indexed"
        await db.commit()
    except Exception as e:
        logger.error(f"Text document ingestion failed: {e}", exc_info=True)
        _handle_ingestion_error(e)
    return _document_out(doc)


@router.post("/{kb_id}/documents/upload", status_code=status.HTTP_201_CREATED)
async def upload_document(
    kb_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    api_key = await _get_api_key(kb, db, workspace.id)

    content = await file.read()
    filename = file.filename or "upload"
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)

    try:
        if filename.lower().endswith(".pdf"):
            doc = await svc.add_document_from_pdf(kb, filename, content, api_key)
        else:
            text = content.decode("utf-8", errors="replace")
            doc = await svc.add_document_from_text(kb, filename, text, api_key, source_type="file")
        doc.status = "indexed"
        await db.commit()
    except Exception as e:
        logger.error(f"File upload ingestion failed: {e}", exc_info=True)
        _handle_ingestion_error(e)

    return _document_out(doc)


@router.post("/{kb_id}/documents/url", status_code=status.HTTP_201_CREATED)
async def add_url_document(
    kb_id: uuid.UUID,
    body: AddUrlRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    api_key = await _get_api_key(kb, db, workspace.id)
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)
    try:
        doc = await svc.add_document_from_url(kb, body.url, api_key)
        doc.status = "indexed"
        await db.commit()
    except Exception as e:
        logger.error(f"URL ingestion failed: {e}", exc_info=True)
        _handle_ingestion_error(e)
    return _document_out(doc)


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


# ── Per-document reindex ───────────────────────────────────────────────────────

@router.post("/{kb_id}/documents/{doc_id}/reindex", status_code=status.HTTP_200_OK)
async def reindex_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Re-index a single document using its stored raw_content."""
    kb = await _require_kb(kb_id, workspace.id, db)
    repo = KnowledgeRepository(db)
    doc = await repo.get_document(doc_id, kb_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")

    if not doc.raw_content:
        raise HTTPException(
            status_code=400,
            detail="This document has no stored content and must be re-uploaded.",
        )

    api_key = await _get_api_key(kb, db, workspace.id)
    svc = KnowledgeService(repo)

    # Delete existing chunks so we start clean
    existing_chunks = await repo.list_chunks_for_document(doc.id)
    for chunk in existing_chunks:
        await db.delete(chunk)
    await db.flush()

    try:
        refreshed_doc = await svc.add_document_from_text(
            kb, doc.name, doc.raw_content, api_key, existing_doc=doc
        )
        refreshed_doc.status = "indexed"
        await db.commit()
        return _document_out(refreshed_doc)
    except Exception as e:
        doc.status = "failed"
        await db.commit()
        logger.warning(f"Per-document reindex failed for {doc.name}: {e}")
        _handle_ingestion_error(e)


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
    api_key = await _get_api_key(kb, db, workspace.id)
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)
    try:
        results = await svc.search(kb, body.query, api_key, body.top_k)
    except Exception as e:
        _handle_ingestion_error(e)
    return {"query": body.query, "results": results, "count": len(results)}


# ── Chunks ─────────────────────────────────────────────────────────────────────

class ChunkOut(BaseModel):
    id: str
    content: str
    chunk_index: int
    has_embedding: bool


class ChunkCreate(BaseModel):
    content: str


class ChunkUpdate(BaseModel):
    content: str


@router.get("/{kb_id}/documents/{doc_id}/chunks")
async def list_chunks(
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
    chunks = await repo.list_chunks_for_document(doc_id)
    return [ChunkOut(id=str(c.id), content=c.content, chunk_index=c.chunk_index, has_embedding=c.embedding is not None) for c in chunks]


@router.post("/{kb_id}/documents/{doc_id}/chunks", status_code=201)
async def create_chunk(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: ChunkCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    repo = KnowledgeRepository(db)
    doc = await repo.get_document(doc_id, kb_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Document not found.")
    # Get current max index
    chunks = await repo.list_chunks_for_document(doc_id)
    next_index = max((c.chunk_index for c in chunks), default=-1) + 1

    # Try to embed the new chunk
    try:
        api_key = await _get_api_key(kb, db, workspace.id)
        from apps.api.app.services.knowledge_service import _embed_texts
        embeddings = await _embed_texts([body.content], api_key, kb.embedding_model)
        embedding = embeddings[0]
    except Exception:
        embedding = None

    from apps.api.app.models.knowledge import KBChunk
    chunk = KBChunk(document_id=doc_id, knowledge_base_id=kb_id, content=body.content, chunk_index=next_index, embedding=embedding)
    db.add(chunk)
    await db.commit()
    await db.refresh(chunk)
    await repo.update_chunk_count(doc_id, len(chunks) + 1)
    return ChunkOut(id=str(chunk.id), content=chunk.content, chunk_index=chunk.chunk_index, has_embedding=chunk.embedding is not None)


@router.patch("/{kb_id}/chunks/{chunk_id}")
async def update_chunk(
    kb_id: uuid.UUID,
    chunk_id: uuid.UUID,
    body: ChunkUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    kb = await _require_kb(kb_id, workspace.id, db)
    repo = KnowledgeRepository(db)
    chunk = await repo.get_chunk(chunk_id, kb_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found.")
    chunk.content = body.content
    # Re-embed
    try:
        api_key = await _get_api_key(kb, db, workspace.id)
        from apps.api.app.services.knowledge_service import _embed_texts
        embeddings = await _embed_texts([body.content], api_key, kb.embedding_model)
        chunk.embedding = embeddings[0]
    except Exception:
        chunk.embedding = None
    await db.commit()
    await db.refresh(chunk)
    return ChunkOut(id=str(chunk.id), content=chunk.content, chunk_index=chunk.chunk_index, has_embedding=chunk.embedding is not None)


@router.delete("/{kb_id}/chunks/{chunk_id}", status_code=204)
async def delete_chunk(
    kb_id: uuid.UUID,
    chunk_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    await _require_kb(kb_id, workspace.id, db)
    repo = KnowledgeRepository(db)
    chunk = await repo.get_chunk(chunk_id, kb_id)
    if not chunk:
        raise HTTPException(status_code=404, detail="Chunk not found.")
    doc_id = chunk.document_id
    await db.delete(chunk)
    await db.commit()
    # Update count
    remaining = await repo.list_chunks_for_document(doc_id)
    await repo.update_chunk_count(doc_id, len(remaining))


# ── Re-index ───────────────────────────────────────────────────────────────────

@router.post("/{kb_id}/reindex")
async def reindex_kb(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    db: AsyncSession = Depends(get_db),
):
    """Re-process all documents that have 0 chunks using stored raw_content."""
    kb = await _require_kb(kb_id, workspace.id, db)
    api_key = await _get_api_key(kb, db, workspace.id)
    repo = KnowledgeRepository(db)
    svc = KnowledgeService(repo)
    docs = await repo.list_documents(kb.id)

    reindexed = 0
    needs_reupload = 0

    for doc in docs:
        chunks = await repo.list_chunks_for_document(doc.id)
        if chunks:
            continue  # already indexed, skip
        if doc.raw_content:
            try:
                await svc.add_document_from_text(kb, doc.name, doc.raw_content, api_key, existing_doc=doc)
                doc.status = "indexed"
                await db.commit()
                reindexed += 1
            except Exception as e:
                doc.status = "failed"
                await db.commit()
                logger.warning(f"Re-index failed for {doc.name}: {e}")
        else:
            needs_reupload += 1

    return {
        "reindexed": reindexed,
        "needs_reupload": needs_reupload,
        "message": (
            f"Re-indexed {reindexed} document(s)."
            + (f" {needs_reupload} document(s) need to be re-uploaded (no stored content)." if needs_reupload else "")
        ),
    }
