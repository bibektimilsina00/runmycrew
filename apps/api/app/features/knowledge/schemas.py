import uuid

from sqlmodel import SQLModel


class KBCreate(SQLModel):
    name: str
    description: str | None = None
    embedding_model: str = "default:gemini-embedding-001"
    embedding_credential_id: uuid.UUID | None = None
    min_chunk_size: int = 100  # characters
    max_chunk_tokens: int = 1024  # tokens  → stored as chars
    overlap_tokens: int = 200  # tokens  → stored as chars
    chunking_strategy: str = "auto"


class KBOut(SQLModel):
    id: str
    name: str
    description: str | None
    embedding_model: str
    embedding_credential_id: str | None
    document_count: int
    total_chunks: int
    min_chunk_size: int
    max_chunk_tokens: int  # chunk_size chars ÷ 4
    overlap_tokens: int  # chunk_overlap chars ÷ 4
    chunking_strategy: str
    created_at: str


class DocumentOut(SQLModel):
    id: str
    name: str
    source_type: str
    chunk_count: int
    status: str  # pending | indexed | failed | partial
    created_at: str


class AddUrlRequest(SQLModel):
    url: str


class SearchResult(SQLModel):
    document_name: str
    chunk_index: int
    content: str
    score: float
    kb_id: uuid.UUID
    doc_id: uuid.UUID


class SearchResponse(SQLModel):
    query: str
    results: list[SearchResult]
    count: int


class SearchRequest(SQLModel):
    query: str
    top_k: int = 5


class AddTextRequest(SQLModel):
    name: str
    text: str


class ChunkOut(SQLModel):
    id: str
    content: str
    chunk_index: int
    has_embedding: bool


class ChunkCreate(SQLModel):
    content: str


class ChunkUpdate(SQLModel):
    content: str


class KBReindexResponse(SQLModel):
    reindexed: int
    needs_reupload: int
    message: str


class KBListOption(SQLModel):
    label: str
    value: str


class KBListOptionsResponse(SQLModel):
    ok: bool
    data: list[KBListOption]
