from __future__ import annotations

import uuid

import httpx

from apps.api.app.core.logger import get_logger
from apps.api.app.models.knowledge import KBChunk, KBDocument, KnowledgeBase
from apps.api.app.repositories.knowledge_repository import KnowledgeRepository

logger = get_logger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
EMBEDDING_DIM = 1536


def _split_text(text: str, chunk_size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    chunks: list[str] = []
    start = 0
    text = text.strip()
    while start < len(text):
        end = min(start + chunk_size, len(text))
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - overlap
    return chunks


async def _embed_texts(texts: list[str], api_key: str, model: str = "text-embedding-3-small") -> list[list[float]]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "input": texts},
        )
        resp.raise_for_status()
        data = resp.json()
        return [item["embedding"] for item in data["data"]]


async def _embed_one(text: str, api_key: str, model: str = "text-embedding-3-small") -> list[float]:
    results = await _embed_texts([text], api_key, model)
    return results[0]


class KnowledgeService:
    def __init__(self, repo: KnowledgeRepository):
        self.repo = repo

    async def create_kb(
        self,
        user_id: uuid.UUID,
        workspace_id: uuid.UUID,
        name: str,
        description: str | None = None,
        embedding_model: str = "text-embedding-3-small",
        embedding_credential_id: uuid.UUID | None = None,
    ) -> KnowledgeBase:
        kb = KnowledgeBase(
            user_id=user_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
            embedding_model=embedding_model,
            embedding_provider="openai",
            embedding_credential_id=embedding_credential_id,
        )
        return await self.repo.create_kb(kb)

    async def add_document_from_text(
        self,
        kb: KnowledgeBase,
        name: str,
        text: str,
        api_key: str,
    ) -> KBDocument:
        doc = KBDocument(
            knowledge_base_id=kb.id,
            name=name,
            source_type="text",
            chunk_count=0,
        )
        doc = await self.repo.create_document(doc)

        chunks_text = _split_text(text)
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

    async def add_document_from_pdf(
        self,
        kb: KnowledgeBase,
        name: str,
        pdf_bytes: bytes,
        api_key: str,
    ) -> KBDocument:
        import io

        from pypdf import PdfReader

        reader = PdfReader(io.BytesIO(pdf_bytes))
        pages = [page.extract_text() or "" for page in reader.pages]
        full_text = "\n\n".join(p for p in pages if p.strip())

        return await self.add_document_from_text(kb, name, full_text, api_key)

    async def search(
        self,
        kb: KnowledgeBase,
        query: str,
        api_key: str,
        top_k: int = 5,
    ) -> list[dict]:
        query_embedding = await _embed_one(query, api_key, kb.embedding_model)
        return await self.repo.search_chunks(kb.id, query_embedding, top_k)
