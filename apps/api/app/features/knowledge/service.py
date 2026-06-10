import uuid

import httpx
from fastapi import Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.core.config import settings
from apps.api.app.core.database import get_db
from apps.api.app.core.logger import get_logger
from apps.api.app.features.credentials.repository import CredentialRepository
from apps.api.app.features.credentials.service import CredentialService
from apps.api.app.features.knowledge.embedding_catalog import (
    EmbeddingModelInfo,
    list_embedding_models,
)
from apps.api.app.features.knowledge.models import KBChunk, KBDocument, KnowledgeBase
from apps.api.app.features.knowledge.repository import KnowledgeRepository
from apps.api.app.features.knowledge.schemas import (
    AddTextRequest,
    ChunkOut,
    DocumentOut,
    KBCreate,
    KBOut,
    KBReindexResponse,
    SearchResult,
)
from apps.api.app.features.knowledge.service_helpers import (
    TOKENS_TO_CHARS,
    _cred_type_for_model,
    _embed_one,
    _embed_texts,
    _handle_ingestion_error,
    _is_default_model,
    _provider_from_model,
    _split_text,
)

logger = get_logger(__name__)


class KnowledgeService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.repo = KnowledgeRepository(db)

    async def _get_api_key(self, kb: KnowledgeBase, workspace_id: uuid.UUID) -> str:
        model = kb.embedding_model or "text-embedding-3-small"

        # Fuse-managed default: use Gemini key from settings, skip credential lookup.
        if _is_default_model(model):
            if not settings.GEMINI_API_KEY:
                raise HTTPException(
                    status_code=400,
                    detail=(
                        "Fuse default embedding model is unavailable: GEMINI_API_KEY is not set "
                        "on the server. Pick a different provider in KB settings."
                    ),
                )
            return settings.GEMINI_API_KEY

        cred_repo = CredentialRepository(self.db)
        cred_service = CredentialService(self.db)
        required_cred_type = _cred_type_for_model(model)

        if kb.embedding_credential_id:
            cred = await cred_repo.get_by_id_and_workspace(kb.embedding_credential_id, workspace_id)
            if cred and cred.type == required_cred_type:
                decrypted = await cred_service.get_decrypted_credential(cred)
                api_key = decrypted.get("api_key")
                if api_key:
                    return api_key

        cred = await cred_repo.get_first_by_type_and_workspace(required_cred_type, workspace_id)
        if cred:
            decrypted = await cred_service.get_decrypted_credential(cred)
            api_key = decrypted.get("api_key")
            if api_key:
                kb.embedding_credential_id = cred.id
                await self.db.commit()
                return api_key

        provider = required_cred_type.replace("_api_key", "").title()
        raise HTTPException(
            status_code=400,
            detail=(
                f"No {provider} credential found for model '{kb.embedding_model}'. "
                f"Add a {provider} API key in Connections, or switch to a different model in KB settings."
            ),
        )

    async def _require_kb(self, kb_id: uuid.UUID, workspace_id: uuid.UUID) -> KnowledgeBase:
        kb = await self.repo.get_kb(kb_id, workspace_id)
        if not kb:
            raise HTTPException(status_code=404, detail="Knowledge base not found.")
        return kb

    async def list_embedding_models(
        self,
        workspace_id: uuid.UUID,
        provider: str,
        credential_id: uuid.UUID | None,
    ) -> list[EmbeddingModelInfo]:
        """List embedding models live from the provider's API.

        - Default provider: uses server-managed `GEMINI_API_KEY`.
        - Other providers: requires `credential_id` of the matching cred type.
        """
        if provider == "Default":
            if not settings.GEMINI_API_KEY:
                raise HTTPException(
                    status_code=400,
                    detail="Default provider unavailable: GEMINI_API_KEY is not set on the server.",
                )
            return await list_embedding_models("Default", settings.GEMINI_API_KEY)

        cred_type_map = {
            "OpenAI": "openai_api_key",
            "Google": "google_api_key",
            "Mistral": "mistral_api_key",
        }
        cred_type = cred_type_map.get(provider)
        if cred_type is None:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")

        if not credential_id:
            raise HTTPException(
                status_code=400,
                detail=f"credential_id is required for {provider}.",
            )

        cred_repo = CredentialRepository(self.db)
        cred = await cred_repo.get_by_id_and_workspace(credential_id, workspace_id)
        if not cred or cred.type != cred_type:
            raise HTTPException(
                status_code=404,
                detail=f"No {provider} credential found for id {credential_id}.",
            )
        decrypted = await CredentialService(self.db).get_decrypted_credential(cred)
        api_key = decrypted.get("api_key")
        if not api_key:
            raise HTTPException(
                status_code=400,
                detail=f"{provider} credential has no api_key field.",
            )
        return await list_embedding_models(provider, api_key)

    async def list_kb_options(self, workspace_id: uuid.UUID) -> list[dict]:
        kbs = await self.repo.list_kbs(workspace_id)
        return [{"label": kb.name, "value": str(kb.id)} for kb in kbs]

    async def create_kb(self, user_id: uuid.UUID, workspace_id: uuid.UUID, body: KBCreate) -> KBOut:
        kb = KnowledgeBase(
            user_id=user_id,
            workspace_id=workspace_id,
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
        kb = await self.repo.create_kb(kb)
        return await self._kb_out(kb)

    async def list_kbs(self, workspace_id: uuid.UUID) -> list[KBOut]:
        kbs = await self.repo.list_kbs(workspace_id)
        return [await self._kb_out(kb) for kb in kbs]

    async def get_kb(self, kb_id: uuid.UUID, workspace_id: uuid.UUID) -> dict:
        kb = await self._require_kb(kb_id, workspace_id)
        docs = await self.repo.list_documents(kb.id)
        total_chunks = await self.repo.count_chunks_for_kb(kb.id)
        kb_out = await self._kb_out(kb)
        data = kb_out.model_dump()
        data["total_chunks"] = total_chunks
        data["documents"] = [
            DocumentOut(
                id=str(d.id),
                name=d.name,
                source_type=d.source_type,
                chunk_count=d.chunk_count,
                status=d.status,
                created_at=d.created_at.isoformat(),
            ).model_dump()
            for d in docs
        ]
        return data

    async def update_kb(self, kb_id: uuid.UUID, workspace_id: uuid.UUID, body: KBCreate) -> KBOut:
        kb = await self._require_kb(kb_id, workspace_id)
        kb = await self.repo.update_kb(
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
        return await self._kb_out(kb)

    async def delete_kb(self, kb_id: uuid.UUID, workspace_id: uuid.UUID) -> None:
        kb = await self._require_kb(kb_id, workspace_id)
        await self.repo.delete_kb(kb)

    async def _add_document_from_text_inner(
        self,
        kb: KnowledgeBase,
        name: str,
        text: str,
        api_key: str,
        existing_doc: KBDocument | None = None,
        source_type: str = "text",
    ) -> KBDocument:
        if existing_doc is not None:
            doc = existing_doc
            doc.raw_content = text
        else:
            doc = KBDocument(
                knowledge_base_id=kb.id,
                name=name,
                source_type=source_type,
                chunk_count=0,
                raw_content=text,
            )
            doc = await self.repo.create_document(doc)

        chunks_text = _split_text(
            text,
            max_size=kb.chunk_size,
            min_size=getattr(kb, "min_chunk_size", 100),
            overlap=kb.chunk_overlap,
            strategy=getattr(kb, "chunking_strategy", "auto"),
        )
        if not chunks_text:
            return doc

        embeddings = await _embed_texts(chunks_text, api_key, kb.embedding_model)

        chunks = [
            KBChunk(
                document_id=doc.id,
                knowledge_base_id=kb.id,
                content=chunk_text,
                chunk_index=i,
                embedding=emb,
            )
            for i, (chunk_text, emb) in enumerate(zip(chunks_text, embeddings, strict=True))
        ]
        await self.repo.bulk_insert_chunks(chunks)
        await self.repo.update_chunk_count(doc.id, len(chunks))
        doc.chunk_count = len(chunks)
        return doc

    async def add_text_document(
        self, kb_id: uuid.UUID, workspace_id: uuid.UUID, body: AddTextRequest
    ) -> DocumentOut:
        kb = await self._require_kb(kb_id, workspace_id)
        api_key = await self._get_api_key(kb, workspace_id)
        try:
            doc = await self._add_document_from_text_inner(kb, body.name, body.text, api_key)
            doc.status = "indexed"
            await self.db.commit()
        except Exception as e:
            logger.error(f"Text document ingestion failed: {e}", exc_info=True)
            _handle_ingestion_error(e)
        return self._document_out(doc)

    async def upload_document(
        self, kb_id: uuid.UUID, workspace_id: uuid.UUID, filename: str, content: bytes
    ) -> DocumentOut:
        kb = await self._require_kb(kb_id, workspace_id)
        api_key = await self._get_api_key(kb, workspace_id)

        try:
            if filename.lower().endswith(".pdf"):
                import io

                from pypdf import PdfReader

                reader = PdfReader(io.BytesIO(content))
                pages = [page.extract_text() or "" for page in reader.pages]
                full_text = "\n\n".join(p for p in pages if p.strip())
                doc = await self._add_document_from_text_inner(
                    kb, filename, full_text, api_key, source_type="file"
                )
            else:
                text = content.decode("utf-8", errors="replace")
                doc = await self._add_document_from_text_inner(
                    kb, filename, text, api_key, source_type="file"
                )
            doc.status = "indexed"
            await self.db.commit()
        except Exception as e:
            logger.error(f"File upload ingestion failed: {e}", exc_info=True)
            _handle_ingestion_error(e)

        return self._document_out(doc)

    async def add_url_document(
        self, kb_id: uuid.UUID, workspace_id: uuid.UUID, url: str
    ) -> DocumentOut:
        kb = await self._require_kb(kb_id, workspace_id)
        api_key = await self._get_api_key(kb, workspace_id)
        try:
            async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
                resp = await client.get(url, headers={"User-Agent": "fuse-kb-crawler/1.0"})
                resp.raise_for_status()
                content_type = resp.headers.get("content-type", "")
                raw = resp.text

            if "html" in content_type or raw.lstrip().startswith("<"):
                import re

                raw = re.sub(
                    r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE
                )
                raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
                raw = re.sub(r"<[^>]+>", " ", raw)
                raw = re.sub(r"\s{2,}", " ", raw).strip()

            from urllib.parse import urlparse

            parsed = urlparse(url)
            doc_name = f"{parsed.netloc}{parsed.path}".rstrip("/") or url

            doc = await self._add_document_from_text_inner(
                kb, doc_name, raw, api_key, source_type="url"
            )
            doc.status = "indexed"
            await self.db.commit()
        except Exception as e:
            logger.error(f"URL ingestion failed: {e}", exc_info=True)
            _handle_ingestion_error(e)
        return self._document_out(doc)

    async def delete_document(
        self, kb_id: uuid.UUID, doc_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> None:
        await self._require_kb(kb_id, workspace_id)
        doc = await self.repo.get_document(doc_id, kb_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        await self.repo.delete_document(doc)

    async def reindex_document(
        self, kb_id: uuid.UUID, doc_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> DocumentOut:
        kb = await self._require_kb(kb_id, workspace_id)
        doc = await self.repo.get_document(doc_id, kb_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        if not doc.raw_content:
            raise HTTPException(
                status_code=400,
                detail="This document has no stored content and must be re-uploaded.",
            )

        api_key = await self._get_api_key(kb, workspace_id)

        existing_chunks = await self.repo.list_chunks_for_document(doc.id)
        for chunk in existing_chunks:
            await self.db.delete(chunk)
        await self.db.flush()

        try:
            refreshed_doc = await self._add_document_from_text_inner(
                kb, doc.name, doc.raw_content, api_key, existing_doc=doc
            )
            refreshed_doc.status = "indexed"
            await self.db.commit()
            return self._document_out(refreshed_doc)
        except Exception as e:
            doc.status = "failed"
            await self.db.commit()
            logger.warning(f"Per-document reindex failed for {doc.name}: {e}")
            _handle_ingestion_error(e)

    async def search(
        self, kb_id: uuid.UUID, workspace_id: uuid.UUID, query: str, top_k: int
    ) -> list[SearchResult]:
        kb = await self._require_kb(kb_id, workspace_id)
        api_key = await self._get_api_key(kb, workspace_id)
        try:
            query_embedding = await _embed_one(query, api_key, kb.embedding_model)
            results = await self.repo.search_chunks(kb.id, query_embedding, top_k)
            return [SearchResult(**r) for r in results]
        except Exception as e:
            _handle_ingestion_error(e)

    async def list_chunks(
        self, kb_id: uuid.UUID, doc_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> list[ChunkOut]:
        await self._require_kb(kb_id, workspace_id)
        doc = await self.repo.get_document(doc_id, kb_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        chunks = await self.repo.list_chunks_for_document(doc_id)
        return [
            ChunkOut(
                id=str(c.id),
                content=c.content,
                chunk_index=c.chunk_index,
                has_embedding=c.embedding is not None,
            )
            for c in chunks
        ]

    async def create_chunk(
        self, kb_id: uuid.UUID, doc_id: uuid.UUID, workspace_id: uuid.UUID, content: str
    ) -> ChunkOut:
        kb = await self._require_kb(kb_id, workspace_id)
        doc = await self.repo.get_document(doc_id, kb_id)
        if not doc:
            raise HTTPException(status_code=404, detail="Document not found.")
        chunks = await self.repo.list_chunks_for_document(doc_id)
        next_index = max((c.chunk_index for c in chunks), default=-1) + 1

        try:
            api_key = await self._get_api_key(kb, workspace_id)
            embeddings = await _embed_texts([content], api_key, kb.embedding_model)
            embedding = embeddings[0]
        except Exception:
            embedding = None

        chunk = KBChunk(
            document_id=doc_id,
            knowledge_base_id=kb_id,
            content=content,
            chunk_index=next_index,
            embedding=embedding,
        )
        self.db.add(chunk)
        await self.db.commit()
        await self.db.refresh(chunk)
        await self.repo.update_chunk_count(doc_id, len(chunks) + 1)
        return ChunkOut(
            id=str(chunk.id),
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            has_embedding=chunk.embedding is not None,
        )

    async def update_chunk(
        self, kb_id: uuid.UUID, chunk_id: uuid.UUID, workspace_id: uuid.UUID, content: str
    ) -> ChunkOut:
        kb = await self._require_kb(kb_id, workspace_id)
        chunk = await self.repo.get_chunk(chunk_id, kb_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found.")
        chunk.content = content
        try:
            api_key = await self._get_api_key(kb, workspace_id)
            embeddings = await _embed_texts([content], api_key, kb.embedding_model)
            chunk.embedding = embeddings[0]
        except Exception:
            chunk.embedding = None
        await self.db.commit()
        await self.db.refresh(chunk)
        return ChunkOut(
            id=str(chunk.id),
            content=chunk.content,
            chunk_index=chunk.chunk_index,
            has_embedding=chunk.embedding is not None,
        )

    async def delete_chunk(
        self, kb_id: uuid.UUID, chunk_id: uuid.UUID, workspace_id: uuid.UUID
    ) -> None:
        await self._require_kb(kb_id, workspace_id)
        chunk = await self.repo.get_chunk(chunk_id, kb_id)
        if not chunk:
            raise HTTPException(status_code=404, detail="Chunk not found.")
        doc_id = chunk.document_id
        await self.db.delete(chunk)
        await self.db.commit()
        remaining = await self.repo.list_chunks_for_document(doc_id)
        await self.repo.update_chunk_count(doc_id, len(remaining))

    async def reindex_kb(self, kb_id: uuid.UUID, workspace_id: uuid.UUID) -> KBReindexResponse:
        kb = await self._require_kb(kb_id, workspace_id)
        api_key = await self._get_api_key(kb, workspace_id)
        docs = await self.repo.list_documents(kb.id)

        reindexed = 0
        needs_reupload = 0

        for doc in docs:
            chunks = await self.repo.list_chunks_for_document(doc.id)
            if chunks:
                continue
            if doc.raw_content:
                try:
                    await self._add_document_from_text_inner(
                        kb, doc.name, doc.raw_content, api_key, existing_doc=doc
                    )
                    doc.status = "indexed"
                    await self.db.commit()
                    reindexed += 1
                except Exception as e:
                    doc.status = "failed"
                    await self.db.commit()
                    logger.warning(f"Re-index failed for {doc.name}: {e}")
            else:
                needs_reupload += 1

        message = f"Re-indexed {reindexed} document(s)." + (
            f" {needs_reupload} document(s) need to be re-uploaded (no stored content)."
            if needs_reupload
            else ""
        )
        return KBReindexResponse(
            reindexed=reindexed, needs_reupload=needs_reupload, message=message
        )

    async def _kb_out(self, kb: KnowledgeBase) -> KBOut:
        docs = await self.repo.list_documents(kb.id)
        total_chunks = await self.repo.count_chunks_for_kb(kb.id)
        return KBOut(
            id=str(kb.id),
            name=kb.name,
            description=kb.description,
            embedding_model=kb.embedding_model,
            embedding_credential_id=str(kb.embedding_credential_id)
            if kb.embedding_credential_id
            else None,
            document_count=len(docs),
            total_chunks=total_chunks,
            min_chunk_size=getattr(kb, "min_chunk_size", 100),
            max_chunk_tokens=getattr(kb, "chunk_size", 4096) // TOKENS_TO_CHARS,
            overlap_tokens=getattr(kb, "chunk_overlap", 800) // TOKENS_TO_CHARS,
            chunking_strategy=getattr(kb, "chunking_strategy", "auto"),
            created_at=kb.created_at.isoformat(),
        )

    def _document_out(self, doc: KBDocument) -> DocumentOut:
        return DocumentOut(
            id=str(doc.id),
            name=doc.name,
            source_type=doc.source_type,
            chunk_count=doc.chunk_count,
            status=doc.status,
            created_at=doc.created_at.isoformat(),
        )


def get_knowledge_service(db: AsyncSession = Depends(get_db)) -> KnowledgeService:
    return KnowledgeService(db)
