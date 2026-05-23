import httpx
from fastapi import HTTPException

TOKENS_TO_CHARS = 4

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
MODEL_PROVIDER: dict[str, str] = {
    "text-embedding-3-small": "openai",
    "text-embedding-3-large": "openai",
    "text-embedding-ada-002": "openai",
    "text-embedding-004": "google",
    "mistral-embed": "mistral",
}

MODEL_CRED_TYPE: dict[str, str] = {
    "text-embedding-3-small": "openai_api_key",
    "text-embedding-3-large": "openai_api_key",
    "text-embedding-ada-002": "openai_api_key",
    "text-embedding-004": "google_api_key",
    "mistral-embed": "mistral_api_key",
}


def _cred_type_for_model(model: str) -> str:
    if model in MODEL_CRED_TYPE:
        return MODEL_CRED_TYPE[model]
    if "mistral" in model:
        return "mistral_api_key"
    if "gemini" in model or "embedding-004" in model:
        return "google_api_key"
    return "openai_api_key"


def _provider_from_model(model: str) -> str:
    if model in MODEL_PROVIDER:
        return MODEL_PROVIDER[model]
    if model.startswith("models/") or "gemini" in model:
        return "google"
    if "mistral" in model:
        return "mistral"
    if model.startswith("text-embedding") or model.startswith("text-embed"):
        return "openai"
    return "openai"


def _handle_ingestion_error(e: Exception) -> None:
    msg = str(e)
    if "401" in msg or "Unauthorized" in msg or "Invalid API key" in msg:
        raise HTTPException(
            status_code=400,
            detail="Embedding credential rejected (401 Unauthorized). The API key may be invalid or expired — update it in Connections.",
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


def _split_fixed(text: str, max_size: int, min_size: int, overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    text = text.strip()
    while start < len(text):
        end = min(start + max_size, len(text))
        chunk = text[start:end].strip()
        if len(chunk) >= min_size:
            chunks.append(chunk)
        elif chunks:
            chunks[-1] = (chunks[-1] + " " + chunk).strip()
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def _split_paragraph(text: str, max_size: int, min_size: int) -> list[str]:
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
            if len(para) > max_size:
                chunks.extend(_split_fixed(para, max_size, min_size, max_size // 5))
                buf = ""
            else:
                buf = para
    if buf and len(buf) >= min_size:
        chunks.append(buf)
    return chunks or _split_fixed(text, max_size, min_size, max_size // 5)


def _split_sentence(text: str, max_size: int, min_size: int) -> list[str]:
    import re

    sentences = re.split(r"(?<=[.!?])\s+", text.strip())
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
    import re

    sections = re.split(r"(?=\n#{1,6} )", text)
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
    import re

    if re.search(r"\n#{1,6} ", text):
        return "markdown"
    if text.count("\n\n") > 5:
        return "paragraph"
    if re.search(r"[.!?]\s+[A-Z]", text):
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
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            "https://api.mistral.ai/v1/embeddings",
            headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"},
            json={"model": model, "input": texts},
        )
        resp.raise_for_status()
        return [item["embedding"] for item in resp.json()["data"]]


async def _embed_google(texts: list[str], api_key: str, model: str) -> list[list[float]]:
    model_id = model if model.startswith("models/") else f"models/{model}"
    url = f"https://generativelanguage.googleapis.com/v1beta/{model_id}:batchEmbedContents?key={api_key}"
    requests_payload = [{"model": model_id, "content": {"parts": [{"text": t}]}} for t in texts]
    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(url, json={"requests": requests_payload})
        resp.raise_for_status()
        return [item["values"] for item in resp.json()["embeddings"]]


async def _embed_texts(
    texts: list[str], api_key: str, model: str = "text-embedding-3-small"
) -> list[list[float]]:
    provider = _provider_from_model(model)
    if provider == "google":
        return await _embed_google(texts, api_key, model)
    if provider == "mistral":
        return await _embed_mistral(texts, api_key, model)
    return await _embed_openai(texts, api_key, model)


async def _embed_one(text: str, api_key: str, model: str = "text-embedding-3-small") -> list[float]:
    return (await _embed_texts([text], api_key, model))[0]
