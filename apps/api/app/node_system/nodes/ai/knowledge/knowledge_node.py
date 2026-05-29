from __future__ import annotations

import uuid
from typing import Any

from pydantic import BaseModel

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.base_node import BaseNode
from apps.api.app.node_system.base.node_context import NodeContext
from apps.api.app.node_system.base.node_metadata import NodeMetadata
from apps.api.app.node_system.base.node_result import NodeResult

logger = get_logger(__name__)


class KnowledgeProperties(BaseModel):
    knowledge_base_id: str | None = None
    query: str = ""
    top_k: int = 5
    include_scores: bool = False


class KnowledgeNode(BaseNode[KnowledgeProperties]):
    @classmethod
    def get_properties_model(cls) -> type[KnowledgeProperties]:
        return KnowledgeProperties

    @classmethod
    def get_metadata(cls) -> NodeMetadata:
        return NodeMetadata(
            type="action.knowledge",
            name="Knowledge Base",
            category="ai",
            description="Search a knowledge base using semantic similarity. Returns the most relevant text chunks.",
            icon="Database",
            color="#0ea5e9",
            properties=[
                {
                    "name": "knowledge_base_id",
                    "label": "Knowledge Base",
                    "type": "string",
                    "required": True,
                    "loadOptions": "/kb/list-options",
                    "placeholder": "Select a knowledge base",
                },
                {
                    "name": "query",
                    "label": "Search Query",
                    "type": "string",
                    "required": True,
                    "placeholder": "What is the refund policy? {{trigger.output}}",
                },
                {
                    "name": "top_k",
                    "label": "Results",
                    "type": "number",
                    "default": 5,
                    "description": "Number of chunks to return (1–20)",
                },
                {
                    "name": "include_scores",
                    "label": "Include Similarity Scores",
                    "type": "boolean",
                    "default": False,
                    "mode": "advanced",
                },
            ],
            inputs=1,
            outputs=1,
            outputs_schema=[
                {"label": "results", "type": "array"},
                {"label": "context", "type": "string"},
                {"label": "count", "type": "number"},
            ],
            allow_error=True,
        )

    async def execute(self, input_data: dict[str, Any], context: NodeContext) -> NodeResult:
        if not self.props.knowledge_base_id:
            return NodeResult(success=False, error="Knowledge base is required.")
        if not self.props.query.strip():
            return NodeResult(success=False, error="Query is required.")
        if not context.db:
            return NodeResult(success=False, error="Database context not available.")

        try:
            kb_id = uuid.UUID(self.props.knowledge_base_id)
        except ValueError:
            return NodeResult(success=False, error="Invalid knowledge base ID.")

        try:
            from apps.api.app.features.credentials.repository import CredentialRepository
            from apps.api.app.features.credentials.service import CredentialService
            from apps.api.app.features.knowledge.repository import KnowledgeRepository
            from apps.api.app.features.knowledge.service import KnowledgeService

            repo = KnowledgeRepository(context.db)

            # Find KB — search across all users' KBs since we don't have user_id here
            import sqlalchemy as sa

            from apps.api.app.features.knowledge.models import KnowledgeBase

            result = await context.db.execute(
                sa.select(KnowledgeBase).where(KnowledgeBase.id == kb_id)
            )
            kb = result.scalar_one_or_none()
            if not kb:
                return NodeResult(success=False, error=f"Knowledge base {kb_id} not found.")

            if not kb.embedding_credential_id:
                return NodeResult(
                    success=False, error="Knowledge base has no embedding credential set."
                )

            cred_repo = CredentialRepository(context.db)
            cred = await cred_repo.get_by_id(kb.embedding_credential_id)
            if not cred:
                return NodeResult(success=False, error="Embedding credential not found.")

            cred_service = CredentialService(context.db)
            decrypted = await cred_service.get_decrypted_credential(cred)
            api_key = decrypted.get("api_key")
            if not api_key:
                return NodeResult(success=False, error="Embedding credential has no api_key.")

            svc = KnowledgeService(repo)
            top_k = max(1, min(self.props.top_k, 20))
            chunks = await svc.search(kb, self.props.query.strip(), api_key, top_k)

            results = (
                chunks
                if self.props.include_scores
                else [
                    {"id": c["id"], "content": c["content"], "document_id": c["document_id"]}
                    for c in chunks
                ]
            )
            context_text = "\n\n---\n\n".join(c["content"] for c in chunks)

            return NodeResult(
                success=True,
                output_data={
                    "results": results,
                    "context": context_text,
                    "count": len(results),
                },
            )

        except Exception as e:
            logger.error(f"KnowledgeNode failed: {e}", exc_info=True)
            return NodeResult(success=False, error=str(e))
