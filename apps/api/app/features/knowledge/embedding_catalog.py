"""Live-discover embedding models from provider APIs.

Each provider's list endpoint is queried with the user's credential (or the
server's Gemini key for the Default provider). Results are filtered down to
embedding-capable models and cached for 1 hour keyed by sha256(api_key).

Dim numbers are not reliably exposed by list endpoints, so we annotate known
models from a static map and leave the field `null` otherwise — the UI shows
"—" in that case rather than fabricating a value.
"""

from __future__ import annotations

import hashlib
import time

import httpx
from fastapi import HTTPException
from pydantic import BaseModel

CACHE_TTL_SECONDS = 60 * 60  # 1 hour


class EmbeddingModelInfo(BaseModel):
    id: str  # Saved value (sentinel-prefixed for Default provider)
    label: str  # Display name
    provider: str  # 'Default' | 'OpenAI' | 'Google' | 'Mistral'
    cred_type: str | None = None
    dims: int | None = None


# Known output dimensions. Provider list endpoints generally don't include this.
KNOWN_DIMS: dict[str, int] = {
    # OpenAI
    "text-embedding-3-small": 1536,
    "text-embedding-3-large": 3072,
    "text-embedding-ada-002": 1536,
    # Google
    "gemini-embedding-001": 3072,
    "gemini-embedding-2": 3072,
    "gemini-embedding-2-preview": 3072,
    "text-embedding-004": 768,
    # Mistral
    "mistral-embed": 1024,
    "codestral-embed": 1536,
}


# ── In-memory TTL cache ──────────────────────────────────────────────────────

_cache: dict[str, tuple[float, list[EmbeddingModelInfo]]] = {}


def _cache_key(provider: str, api_key: str) -> str:
    h = hashlib.sha256(api_key.encode()).hexdigest()[:16]
    return f"{provider}:{h}"


def _cache_get(provider: str, api_key: str) -> list[EmbeddingModelInfo] | None:
    key = _cache_key(provider, api_key)
    entry = _cache.get(key)
    if not entry:
        return None
    expires_at, value = entry
    if expires_at < time.time():
        _cache.pop(key, None)
        return None
    return value


def _cache_set(provider: str, api_key: str, value: list[EmbeddingModelInfo]) -> None:
    _cache[_cache_key(provider, api_key)] = (time.time() + CACHE_TTL_SECONDS, value)


# ── Provider fetchers ────────────────────────────────────────────────────────


async def _list_google(api_key: str, *, default_provider: bool) -> list[EmbeddingModelInfo]:
    """List Gemini models that support `embedContent`."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models?key={api_key}"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url)
        resp.raise_for_status()
        data = resp.json()

    out: list[EmbeddingModelInfo] = []
    for m in data.get("models", []):
        methods = m.get("supportedGenerationMethods") or []
        if "embedContent" not in methods:
            continue
        full = m.get("name", "")  # e.g. "models/gemini-embedding-001"
        short = full.split("/", 1)[-1]
        provider = "Default" if default_provider else "Google"
        out.append(
            EmbeddingModelInfo(
                id=f"default:{short}" if default_provider else short,
                label=m.get("displayName") or short,
                provider=provider,
                cred_type=None if default_provider else "google_api_key",
                dims=KNOWN_DIMS.get(short),
            )
        )
    # Stable display order: known/popular first, then alpha.
    out.sort(key=lambda x: (x.label.lower()))
    return out


async def _list_openai(api_key: str) -> list[EmbeddingModelInfo]:
    """List OpenAI models, filter by id containing 'embedding'."""
    url = "https://api.openai.com/v1/models"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        resp.raise_for_status()
        data = resp.json()

    out: list[EmbeddingModelInfo] = []
    for m in data.get("data", []):
        mid = m.get("id", "")
        if "embedding" not in mid:
            continue
        out.append(
            EmbeddingModelInfo(
                id=mid,
                label=mid,
                provider="OpenAI",
                cred_type="openai_api_key",
                dims=KNOWN_DIMS.get(mid),
            )
        )
    out.sort(key=lambda x: x.id.lower())
    return out


async def _list_mistral(api_key: str) -> list[EmbeddingModelInfo]:
    """List Mistral models, filter by 'embed' in id."""
    url = "https://api.mistral.ai/v1/models"
    async with httpx.AsyncClient(timeout=20.0) as client:
        resp = await client.get(url, headers={"Authorization": f"Bearer {api_key}"})
        resp.raise_for_status()
        data = resp.json()

    out: list[EmbeddingModelInfo] = []
    for m in data.get("data", []):
        mid = m.get("id", "")
        if "embed" not in mid.lower():
            continue
        out.append(
            EmbeddingModelInfo(
                id=mid,
                label=mid,
                provider="Mistral",
                cred_type="mistral_api_key",
                dims=KNOWN_DIMS.get(mid),
            )
        )
    out.sort(key=lambda x: x.id.lower())
    return out


# ── Public entry ─────────────────────────────────────────────────────────────


async def list_embedding_models(provider: str, api_key: str) -> list[EmbeddingModelInfo]:
    """Return embedding models for `provider`, using `api_key` to authenticate.

    `provider` is one of: Default | OpenAI | Google | Mistral. The Default
    provider lists Google models but prefixes ids with `default:` so the backend
    recognises them as Fuse-managed.
    """
    cached = _cache_get(provider, api_key)
    if cached is not None:
        return cached

    try:
        if provider == "Default":
            models = await _list_google(api_key, default_provider=True)
        elif provider == "Google":
            models = await _list_google(api_key, default_provider=False)
        elif provider == "OpenAI":
            models = await _list_openai(api_key)
        elif provider == "Mistral":
            models = await _list_mistral(api_key)
        else:
            raise HTTPException(status_code=400, detail=f"Unknown provider: {provider}")
    except httpx.HTTPStatusError as e:
        # Surface the upstream error verbatim — usually 401 (bad key) or 403
        # (API not enabled). Don't cache failures.
        raise HTTPException(
            status_code=400,
            detail=f"{provider} model listing failed: HTTP {e.response.status_code}",
        ) from e
    except (TimeoutError, httpx.HTTPError) as e:
        raise HTTPException(
            status_code=502,
            detail=f"{provider} model listing failed: {e}",
        ) from e

    _cache_set(provider, api_key, models)
    return models
