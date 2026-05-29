import uuid
from datetime import datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Column
from sqlmodel import Field, Relationship

from apps.api.app.shared.sqlmodel import SQLModelBase, created_at_field, updated_at_field


class KnowledgeBase(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    user_id: uuid.UUID = Field(foreign_key="user.id", ondelete="CASCADE")
    workspace_id: uuid.UUID = Field(foreign_key="workspace.id", ondelete="CASCADE", index=True)
    name: str = Field(max_length=200)
    description: str | None = Field(default=None)
    embedding_model: str = Field(default="text-embedding-3-small", max_length=100)
    embedding_provider: str = Field(default="openai", max_length=50)
    embedding_credential_id: uuid.UUID | None = Field(default=None)
    min_chunk_size: int = Field(default=100)
    chunk_size: int = Field(default=4096)
    chunk_overlap: int = Field(default=800)
    chunking_strategy: str = Field(default="auto", max_length=50)
    created_at: datetime = created_at_field()
    updated_at: datetime = updated_at_field()

    documents: list["KBDocument"] = Relationship(
        back_populates="knowledge_base", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class KBDocument(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    knowledge_base_id: uuid.UUID = Field(foreign_key="knowledgebase.id", ondelete="CASCADE")
    name: str = Field(max_length=500)
    source_type: str = Field(default="text", max_length=50)
    chunk_count: int = Field(default=0)
    status: str = Field(default="pending", max_length=20)
    raw_content: str | None = Field(default=None)
    created_at: datetime = created_at_field()

    knowledge_base: "KnowledgeBase" = Relationship(back_populates="documents")
    chunks: list["KBChunk"] = Relationship(
        back_populates="document", sa_relationship_kwargs={"cascade": "all, delete-orphan"}
    )


class KBChunk(SQLModelBase, table=True):
    id: uuid.UUID = Field(default_factory=uuid.uuid4, primary_key=True)
    document_id: uuid.UUID = Field(foreign_key="kbdocument.id", ondelete="CASCADE")
    knowledge_base_id: uuid.UUID = Field(foreign_key="knowledgebase.id", ondelete="CASCADE")
    content: str = Field()
    chunk_index: int = Field(default=0)
    embedding: list[float] | None = Field(default=None, sa_column=Column(Vector()))

    document: "KBDocument" = Relationship(back_populates="chunks")
