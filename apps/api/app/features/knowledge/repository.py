from __future__ import annotations

import uuid
from typing import Any

import sqlalchemy as sa
from sqlalchemy.ext.asyncio import AsyncSession

from apps.api.app.features.knowledge.models import KBChunk, KBDocument, KnowledgeBase


class KnowledgeRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    # ── KnowledgeBase ──────────────────────────────────────────────────────────

    async def create_kb(self, kb: KnowledgeBase) -> KnowledgeBase:
        self.db.add(kb)
        await self.db.commit()
        await self.db.refresh(kb)
        return kb

    async def get_kb(self, kb_id: uuid.UUID, workspace_id: uuid.UUID) -> KnowledgeBase | None:
        result = await self.db.execute(
            sa.select(KnowledgeBase).where(
                KnowledgeBase.id == kb_id, KnowledgeBase.workspace_id == workspace_id
            )
        )
        return result.scalar_one_or_none()

    async def list_kbs(self, workspace_id: uuid.UUID) -> list[KnowledgeBase]:
        result = await self.db.execute(
            sa.select(KnowledgeBase)
            .where(KnowledgeBase.workspace_id == workspace_id)
            .order_by(KnowledgeBase.created_at.desc())
        )
        return list(result.scalars().all())

    async def update_kb(self, kb: KnowledgeBase, **fields: Any) -> KnowledgeBase:
        for k, v in fields.items():
            setattr(kb, k, v)
        await self.db.commit()
        await self.db.refresh(kb)
        return kb

    async def delete_kb(self, kb: KnowledgeBase) -> None:
        await self.db.delete(kb)
        await self.db.commit()

    # ── KBDocument ─────────────────────────────────────────────────────────────

    async def create_document(self, doc: KBDocument) -> KBDocument:
        self.db.add(doc)
        await self.db.commit()
        await self.db.refresh(doc)
        return doc

    async def get_document(self, doc_id: uuid.UUID, kb_id: uuid.UUID) -> KBDocument | None:
        result = await self.db.execute(
            sa.select(KBDocument).where(
                KBDocument.id == doc_id, KBDocument.knowledge_base_id == kb_id
            )
        )
        return result.scalar_one_or_none()

    async def list_documents(self, kb_id: uuid.UUID) -> list[KBDocument]:
        result = await self.db.execute(
            sa.select(KBDocument)
            .where(KBDocument.knowledge_base_id == kb_id)
            .order_by(KBDocument.created_at.desc())
        )
        return list(result.scalars().all())

    async def delete_document(self, doc: KBDocument) -> None:
        await self.db.delete(doc)
        await self.db.commit()

    async def update_chunk_count(self, doc_id: uuid.UUID, count: int) -> None:
        await self.db.execute(
            sa.update(KBDocument).where(KBDocument.id == doc_id).values(chunk_count=count)
        )
        await self.db.commit()

    # ── KBChunk ────────────────────────────────────────────────────────────────

    async def count_chunks_for_kb(self, kb_id: uuid.UUID) -> int:
        result = await self.db.execute(
            sa.select(sa.func.count(KBChunk.id)).where(KBChunk.knowledge_base_id == kb_id)
        )
        return result.scalar_one() or 0

    async def list_chunks_for_document(self, doc_id: uuid.UUID) -> list[KBChunk]:
        result = await self.db.execute(
            sa.select(KBChunk).where(KBChunk.document_id == doc_id).order_by(KBChunk.chunk_index)
        )
        return list(result.scalars().all())

    async def get_chunk(self, chunk_id: uuid.UUID, kb_id: uuid.UUID) -> KBChunk | None:
        result = await self.db.execute(
            sa.select(KBChunk).where(KBChunk.id == chunk_id, KBChunk.knowledge_base_id == kb_id)
        )
        return result.scalar_one_or_none()

    async def bulk_insert_chunks(self, chunks: list[KBChunk]) -> None:
        self.db.add_all(chunks)
        await self.db.commit()

    async def search_chunks(
        self,
        kb_id: uuid.UUID,
        embedding: list[float],
        top_k: int = 5,
    ) -> list[dict]:
        from pgvector.sqlalchemy import Vector

        vec_literal = sa.cast(embedding, Vector())

        result = await self.db.execute(
            sa.select(
                KBChunk.id,
                KBChunk.content,
                KBChunk.document_id,
                KBChunk.chunk_index,
                (1 - KBChunk.embedding.cosine_distance(vec_literal)).label("score"),
            )
            .where(
                KBChunk.knowledge_base_id == kb_id,
                KBChunk.embedding.is_not(None),
                sa.func.vector_dims(KBChunk.embedding) == len(embedding),
            )
            .order_by(KBChunk.embedding.cosine_distance(vec_literal))
            .limit(top_k)
        )
        rows = result.fetchall()
        return [
            {
                "id": str(r.id),
                "content": r.content,
                "document_id": str(r.document_id),
                "chunk_index": r.chunk_index,
                "score": float(r.score),
            }
            for r in rows
        ]
