from __future__ import annotations

import uuid
from typing import Any

from fastapi import APIRouter, Depends, File, Query, Response, UploadFile, status

from apps.api.app.features.knowledge.embedding_catalog import EmbeddingModelInfo
from apps.api.app.features.knowledge.schemas import (
    AddTextRequest,
    AddUrlRequest,
    ChunkCreate,
    ChunkOut,
    ChunkUpdate,
    DocumentOut,
    KBCreate,
    KBListOptionsResponse,
    KBOut,
    KBReindexResponse,
    SearchRequest,
    SearchResponse,
)
from apps.api.app.features.knowledge.service import KnowledgeService, get_knowledge_service
from apps.api.app.features.users.models import User
from apps.api.app.features.workspaces.models import Workspace
from apps.api.app.shared.dependencies import get_current_user, get_current_workspace

router = APIRouter()


# ── Knowledge Base CRUD ────────────────────────────────────────────────────────


@router.get("/list-options", response_model=KBListOptionsResponse)
async def list_kb_options(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """loadOptions endpoint for the Knowledge node dropdown."""
    options = await service.list_kb_options(workspace.id)
    return KBListOptionsResponse(ok=True, data=options)


@router.get("/embedding-models", response_model=list[EmbeddingModelInfo])
async def list_embedding_models_endpoint(
    provider: str = Query(..., description="Default | OpenAI | Google | Mistral"),
    credential_id: uuid.UUID | None = Query(None, description="Required for non-Default providers"),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """Live-list embedding models from the provider's API. Cached 1 hour per key."""
    return await service.list_embedding_models(workspace.id, provider, credential_id)


@router.post("/", status_code=status.HTTP_201_CREATED, response_model=KBOut)
async def create_kb(
    body: KBCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.create_kb(current_user.id, workspace.id, body)


@router.get("/", response_model=list[KBOut])
async def list_kbs(
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.list_kbs(workspace.id)


@router.get("/{kb_id}")
async def get_kb(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.get_kb(kb_id, workspace.id)


@router.patch("/{kb_id}", response_model=KBOut)
async def update_kb(
    kb_id: uuid.UUID,
    body: KBCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.update_kb(kb_id, workspace.id, body)


@router.delete("/{kb_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response)
async def delete_kb(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    await service.delete_kb(kb_id, workspace.id)


# ── Documents ──────────────────────────────────────────────────────────────────


@router.post(
    "/{kb_id}/documents/text", status_code=status.HTTP_201_CREATED, response_model=DocumentOut
)
async def add_text_document(
    kb_id: uuid.UUID,
    body: AddTextRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.add_text_document(kb_id, workspace.id, body)


@router.post(
    "/{kb_id}/documents/upload", status_code=status.HTTP_201_CREATED, response_model=DocumentOut
)
async def upload_document(
    kb_id: uuid.UUID,
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    content = await file.read()
    filename = file.filename or "upload"
    return await service.upload_document(kb_id, workspace.id, filename, content)


@router.post(
    "/{kb_id}/documents/url", status_code=status.HTTP_201_CREATED, response_model=DocumentOut
)
async def add_url_document(
    kb_id: uuid.UUID,
    body: AddUrlRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.add_url_document(kb_id, workspace.id, body.url)


@router.delete(
    "/{kb_id}/documents/{doc_id}", status_code=status.HTTP_204_NO_CONTENT, response_class=Response
)
async def delete_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    await service.delete_document(kb_id, doc_id, workspace.id)


# ── Per-document reindex ───────────────────────────────────────────────────────


@router.post(
    "/{kb_id}/documents/{doc_id}/reindex",
    status_code=status.HTTP_200_OK,
    response_model=DocumentOut,
)
async def reindex_document(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """Re-index a single document using its stored raw_content."""
    return await service.reindex_document(kb_id, doc_id, workspace.id)


# ── Search ─────────────────────────────────────────────────────────────────────


@router.post("/{kb_id}/search", response_model=SearchResponse)
async def search(
    kb_id: uuid.UUID,
    body: SearchRequest,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    results = await service.search(kb_id, workspace.id, body.query, body.top_k)
    return SearchResponse(query=body.query, results=results, count=len(results))


# ── Chunks ─────────────────────────────────────────────────────────────────────


@router.get("/{kb_id}/documents/{doc_id}/chunks", response_model=list[ChunkOut])
async def list_chunks(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.list_chunks(kb_id, doc_id, workspace.id)


@router.post("/{kb_id}/documents/{doc_id}/chunks", status_code=201, response_model=ChunkOut)
async def create_chunk(
    kb_id: uuid.UUID,
    doc_id: uuid.UUID,
    body: ChunkCreate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.create_chunk(kb_id, doc_id, workspace.id, body.content)


@router.patch("/{kb_id}/chunks/{chunk_id}", response_model=ChunkOut)
async def update_chunk(
    kb_id: uuid.UUID,
    chunk_id: uuid.UUID,
    body: ChunkUpdate,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    return await service.update_chunk(kb_id, chunk_id, workspace.id, body.content)


@router.delete("/{kb_id}/chunks/{chunk_id}", status_code=204, response_class=Response)
async def delete_chunk(
    kb_id: uuid.UUID,
    chunk_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> None:
    await service.delete_chunk(kb_id, chunk_id, workspace.id)


# ── Re-index ───────────────────────────────────────────────────────────────────


@router.post("/{kb_id}/reindex", response_model=KBReindexResponse)
async def reindex_kb(
    kb_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    workspace: Workspace = Depends(get_current_workspace),
    service: KnowledgeService = Depends(get_knowledge_service),
) -> Any:
    """Re-process all documents that have 0 chunks using stored raw_content."""
    return await service.reindex_kb(kb_id, workspace.id)
