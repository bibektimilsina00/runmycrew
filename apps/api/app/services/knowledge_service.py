from __future__ import annotations

import uuid

import httpx

from apps.api.app.core.logger import get_logger
from apps.api.app.models.knowledge import KBChunk, KBDocument, KnowledgeBase
from apps.api.app.repositories.knowledge_repository import KnowledgeRepository

logger = get_logger(__name__)

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MODEL_PROVIDER: dict[str, str] = {
    "text-embedding-3-small": "openai",
    "text-embedding-3-large": "openai",
    "text-embedding-ada-002": "openai",
    "text-embedding-004": "google",
    "mistral-embed": "mistral",
}


def _split_fixed(text: str, max_size: int, min_size: int, overlap: int) -> list[str]:
    """Fixed-size character splitting."""
    chunks: list[str] = []
    start = 0
    text = text.strip()
    while start < len(text):
        end = min(start + max_size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) >= min_size:
            chunks.append(chunk)
        elif chunks:
            # merge tiny tail into previous chunk
            chunks[-1] = (chunks[-1] + " " + chunk).strip()
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def _split_paragraph(text: str, max_size: int, min_size: int) -> list[str]:
    """Split on blank lines, merge short paragraphs, cap long ones."""
    raw = [p.strip() for p in text.split("\n\n") if p.strip()]
    chunks: list[str] = []
    buf = ""
    for para in raw:
        candidate = (buf + "\n\n" + para).strip() if buf else para
        if len(candidate) <= max_size:
            buf = candidate
        else:
            if buf and len(buf) >= min_size:
                chunks.append(buf)
            # para itself might be too long → fall back to fixed
            if len(para) > max_size:
                chunks.extend(_split_fixed(para, max_size, min_size, max_size // 5))
                buf = ""
            else:
                buf = para
    if buf and len(buf) >= min_size:
        chunks.append(buf)
    return chunks or _split_fixed(text, max_size, min_size, max_size // 5)


def _split_sentence(text: str, max_size: int, min_size: int) -> list[str]:
    """Split on sentence boundaries, aggregate into chunks."""
    import re
    sentences = re.split(r'(?<=[.!?])\s+', text.strip())
    chunks: list[str] = []
    buf = ""
    for s in sentences:
        candidate = (buf + " " + s).strip() if buf else s
        if len(candidate) <= max_size:
            buf = candidate
        else:
            if buf and len(buf) >= min_size:
                chunks.append(buf)
            buf = s if len(s) <= max_size else s[:max_size]
    if buf and len(buf) >= min_size:
        chunks.append(buf)
    return chunks or _split_fixed(text, max_size, min_size, max_size // 5)


def _split_markdown(text: str, max_size: int, min_size: int) -> list[str]:
    """Split on markdown # headings, keeping heading with its section."""
    import re
    sections = re.split(r'(?=\n#{1,6} )', text)
    chunks: list[str] = []
    for section in sections:
        section = section.strip()
        if not section:
            continue
        if len(section) <= max_size:
            if len(section) >= min_size:
                chunks.append(section)
        else:
            chunks.extend(_split_paragraph(section, max_size, min_size))
    return chunks or _split_fixed(text, max_size, min_size, max_size // 5)


def _detect_strategy(text: str) -> str:
    """Heuristic: pick best strategy from content."""
    import re
    if re.search(r'\n#{1,6} ', text):
        return "markdown"
    if text.count("\n\n") > 5:
        return "paragraph"
    if re.search(r'[.!?]\s+[A-Z]', text):
        return "sentence"
    return "fixed"


def _split_text(
    text: str,
    max_size: int = CHUNK_SIZE,
    min_size: int = 100,
    overlap: int = CHUNK_OVERLAP,
    strategy: str = "auto",
) -> list[str]:
    if strategy == "auto":
        strategy = _detect_strategy(text)
    if strategy == "paragraph":
        return _split_paragraph(text, max_size, min_size)
    if strategy == "sentence":
        return _split_sentence(text, max_size, min_size)
    if strategy == "markdown":
        return _split_markdown(text, max_size, min_size)
    return _split_fixed(text, max_size, min_size, overlap)


def _provider_from_model(model: str) -> str:
    """Infer provider from model name."""
    if model in MODEL_PROVIDER:
        return MODEL_PROVIDER[model]
    if model.startswith("models/") or "gemini" in model:
        return "google"
    if "mistral" in model:
        return "mistral"
    if model.startswith("text-embedding") or model.startswith("text-embed"):
        return "openai"
    return "openai"


async def _embed_openai(texts: list[str], api_key: str, model: str) -> list[list[float]]:
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.openai.com/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "input": texts},
        )
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]


async def _embed_mistral(texts: list[str], api_key: str, model: str) -> list[list[float]]:
    """Mistral uses OpenAI-compatible embeddings API."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.mistral.ai/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "input": texts},
        )
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]


async def _embed_google(texts: list[str], api_key: str, model: str) -> list[list[float]]:
    """Google Generative AI batch embeddings."""
    # model may be prefixed "models/" already or just "text-embedding-004"
    model_id = model if model.startswith("models/") else f"models/{model}"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_id}:batchEmbedContents?key={api_key}"
    requests_payload = [{"model": model_id, "content": {"parts": [{"text": t}]}} for t in texts]
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json={"requests": requests_payload})
        resp.raise_for_status()
        return [item["values"] for item in resp.json()["embeddings"]]


async def _embed_texts(texts: list[str], api_key: str, model: str = "text-embedding-3-small") -> list[list[float]]:
    provider = _provider_from_model(model)
    if provider == "google":
        return await _embed_google(texts, api_key, model)
    if provider == "mistral":
        return await _embed_mistral(texts, api_key, model)
    return await _embed_openai(texts, api_key, model)


async def _embed_one(text: str, api_key: str, model: str = "text-embedding-3-small") -> list[float]:
    return (await _embed_texts([text], api_key, model))[0]


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
        min_chunk_size: int = 100,
        chunk_size: int = 4096,       # max chars
        chunk_overlap: int = 800,     # chars
        chunking_strategy: str = "auto",
    ) -> KnowledgeBase:
        kb = KnowledgeBase(
            user_id=user_id,
            workspace_id=workspace_id,
            name=name,
            description=description,
            embedding_model=embedding_model,
            embedding_provider=_provider_from_model(embedding_model),
            embedding_credential_id=embedding_credential_id,
            min_chunk_size=max(50, min_chunk_size),
            chunk_size=max(200, min(chunk_size, 32000)),
            chunk_overlap=max(0, min(chunk_overlap, chunk_size // 2)),
            chunking_strategy=chunking_strategy,
        )
        return await self.repo.create_kb(kb)

    async def add_document_from_text(
        self,
        kb: KnowledgeBase,
        name: str,
        text: str,
        api_key: str,
        existing_doc: KBDocument | None = None,
        source_type: str = "text",
    ) -> KBDocument:
        if existing_doc is not None:
            # Reindex mode: reuse the existing document row
            doc = existing_doc
            doc.raw_content = text  # refresh stored content in case it changed
        else:
            doc = KBDocument(
                knowledge_base_id=kb.id,
                name=name,
                source_type=source_type,
                chunk_count=0,
                raw_content=text,  # stored for re-indexing
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

    async def add_document_from_url(
        self,
        kb: KnowledgeBase,
        url: str,
        api_key: str,
    ) -> KBDocument:
        """Fetch a URL, strip HTML tags, and ingest as a text document."""
        async with httpx.AsyncClient(timeout=30.0, follow_redirects=True) as client:
            resp = await client.get(url, headers={"User-Agent": "fuse-kb-crawler/1.0"})
            resp.raise_for_status()
            content_type = resp.headers.get("content-type", "")
            raw = resp.text

        # Strip HTML if it looks like HTML
        if "html" in content_type or raw.lstrip().startswith("<"):
            import re
            raw = re.sub(r"<script[^>]*>.*?</script>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<style[^>]*>.*?</style>", " ", raw, flags=re.DOTALL | re.IGNORECASE)
            raw = re.sub(r"<[^>]+>", " ", raw)
            raw = re.sub(r"\s{2,}", " ", raw).strip()

        # Use the URL hostname + path as document name
        from urllib.parse import urlparse
        parsed = urlparse(url)
        doc_name = f"{parsed.netloc}{parsed.path}".rstrip("/") or url

        return await self.add_document_from_text(kb, doc_name, raw, api_key, source_type="url")

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

        return await self.add_document_from_text(kb, name, full_text, api_key, source_type="file")

    async def search(
        self,
        kb: KnowledgeBase,
        query: str,
        api_key: str,
        top_k: int = 5,
    ) -> list[dict]:
        query_embedding = await _embed_one(query, api_key, kb.embedding_model)
        return await self.repo.search_chunks(kb.id, query_embedding, top_k)
