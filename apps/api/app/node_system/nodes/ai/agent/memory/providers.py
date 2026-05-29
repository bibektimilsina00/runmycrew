from __future__ import annotations

import json
from typing import Any, Protocol

from apps.api.app.core.logger import get_logger
from apps.api.app.node_system.base.node_context import NodeContext

logger = get_logger(__name__)


class MemoryProvider(Protocol):
    async def get(self, key: str, limit: int, query: str | None = None) -> list[dict[str, Any]]: ...
    async def append(self, key: str, messages: list[dict[str, Any]], limit: int) -> None: ...


# ---------------------------------------------------------------------------
# Workflow-variable memory (default — no external deps)
# ---------------------------------------------------------------------------


class WorkflowMemoryProvider:
    def __init__(self, context: NodeContext):
        self._ctx = context

    def _var_key(self, key: str) -> str:
        return f"agent_memory:{key}"

    async def get(self, key: str, limit: int, query: str | None = None) -> list[dict[str, Any]]:
        raw = self._ctx.variables.get(self._var_key(key), [])
        if not isinstance(raw, list):
            return []
        return raw[-max(limit, 1) :]

    async def append(self, key: str, messages: list[dict[str, Any]], limit: int) -> None:
        existing = await self.get(key, limit)
        combined = [*existing, *messages][-max(limit, 1) :]
        self._ctx.variables[self._var_key(key)] = combined


# ---------------------------------------------------------------------------
# Redis memory (short-term, TTL-backed)
# ---------------------------------------------------------------------------


class RedisMemoryProvider:
    def __init__(self, ttl_seconds: int = 86400):
        self._ttl = ttl_seconds

    def _redis_key(self, key: str) -> str:
        return f"fuse:agent_memory:{key}"

    async def get(self, key: str, limit: int, query: str | None = None) -> list[dict[str, Any]]:
        try:
            from apps.api.app.core.redis import get_redis

            redis = await get_redis()
            raw = await redis.get(self._redis_key(key))
            if not raw:
                return []
            messages = json.loads(raw)
            if not isinstance(messages, list):
                return []
            return messages[-max(limit, 1) :]
        except Exception as e:
            logger.warning(f"Redis memory get failed: {e}")
            return []

    async def append(self, key: str, messages: list[dict[str, Any]], limit: int) -> None:
        try:
            from apps.api.app.core.redis import get_redis

            redis = await get_redis()
            rkey = self._redis_key(key)
            raw = await redis.get(rkey)
            existing = json.loads(raw) if raw else []
            combined = [*existing, *messages][-max(limit, 1) :]
            await redis.set(rkey, json.dumps(combined), ex=self._ttl)
        except Exception as e:
            logger.warning(f"Redis memory append failed: {e}")


# ---------------------------------------------------------------------------
# Pinecone vector memory
# ---------------------------------------------------------------------------


class PineconeMemoryProvider:
    def __init__(self, api_key: str, index_name: str, namespace: str = "agent"):
        self._api_key = api_key
        self._index_name = index_name
        self._namespace = namespace

    async def _embed(self, text: str) -> list[float]:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._api_key}"},
                json={"model": "text-embedding-3-small", "input": text},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]

    async def get(self, key: str, limit: int, query: str | None = None) -> list[dict[str, Any]]:
        try:
            from pinecone import Pinecone  # type: ignore[import]

            pc = Pinecone(api_key=self._api_key)
            index = pc.Index(self._index_name)

            if query:
                vector = await self._embed(query)
                results = index.query(
                    vector=vector,
                    top_k=limit,
                    namespace=f"{self._namespace}:{key}",
                    include_metadata=True,
                )
                return [
                    json.loads(m.metadata.get("content", "{}"))
                    for m in results.matches
                    if m.metadata
                ]
            else:
                # No query — fetch most recent by score
                results = index.query(
                    vector=[0.0] * 1536,
                    top_k=limit,
                    namespace=f"{self._namespace}:{key}",
                    include_metadata=True,
                )
                return [
                    json.loads(m.metadata.get("content", "{}"))
                    for m in results.matches
                    if m.metadata
                ]
        except ImportError:
            logger.warning("pinecone-client not installed. Run: pip install pinecone-client")
            return []
        except Exception as e:
            logger.warning(f"Pinecone memory get failed: {e}")
            return []

    async def append(self, key: str, messages: list[dict[str, Any]], limit: int) -> None:
        try:
            import uuid

            from pinecone import Pinecone  # type: ignore[import]

            pc = Pinecone(api_key=self._api_key)
            index = pc.Index(self._index_name)
            ns = f"{self._namespace}:{key}"

            for msg in messages:
                text = msg.get("content", "")
                if not text:
                    continue
                vector = await self._embed(str(text))
                index.upsert(
                    vectors=[
                        {
                            "id": str(uuid.uuid4()),
                            "values": vector,
                            "metadata": {
                                "content": json.dumps(msg),
                                "role": msg.get("role", "user"),
                            },
                        }
                    ],
                    namespace=ns,
                )
        except ImportError:
            logger.warning("pinecone-client not installed")
        except Exception as e:
            logger.warning(f"Pinecone memory append failed: {e}")


# ---------------------------------------------------------------------------
# Qdrant vector memory
# ---------------------------------------------------------------------------


class QdrantMemoryProvider:
    def __init__(self, url: str, collection: str, openai_api_key: str):
        self._url = url.rstrip("/")
        self._collection = collection
        self._openai_api_key = openai_api_key

    async def _embed(self, text: str) -> list[float]:
        import httpx

        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                "https://api.openai.com/v1/embeddings",
                headers={"Authorization": f"Bearer {self._openai_api_key}"},
                json={"model": "text-embedding-3-small", "input": text},
            )
            resp.raise_for_status()
            return resp.json()["data"][0]["embedding"]

    async def get(self, key: str, limit: int, query: str | None = None) -> list[dict[str, Any]]:
        try:
            import httpx

            query_vec = await self._embed(query or "conversation history")
            async with httpx.AsyncClient(timeout=30) as client:
                resp = await client.post(
                    f"{self._url}/collections/{self._collection}/points/search",
                    json={
                        "vector": query_vec,
                        "limit": limit,
                        "filter": {"must": [{"key": "memory_key", "match": {"value": key}}]},
                        "with_payload": True,
                    },
                )
                resp.raise_for_status()
                data = resp.json()
                return [
                    json.loads(p["payload"].get("content", "{}"))
                    for p in data.get("result", [])
                    if p.get("payload")
                ]
        except Exception as e:
            logger.warning(f"Qdrant memory get failed: {e}")
            return []

    async def append(self, key: str, messages: list[dict[str, Any]], limit: int) -> None:
        try:
            import uuid

            import httpx

            async with httpx.AsyncClient(timeout=30) as client:
                points = []
                for msg in messages:
                    text = msg.get("content", "")
                    if not text:
                        continue
                    vector = await self._embed(str(text))
                    points.append(
                        {
                            "id": str(uuid.uuid4()),
                            "vector": vector,
                            "payload": {
                                "memory_key": key,
                                "content": json.dumps(msg),
                                "role": msg.get("role", "user"),
                            },
                        }
                    )
                if points:
                    resp = await client.put(
                        f"{self._url}/collections/{self._collection}/points",
                        json={"points": points},
                    )
                    resp.raise_for_status()
        except Exception as e:
            logger.warning(f"Qdrant memory append failed: {e}")


# ---------------------------------------------------------------------------
# mem0 memory (intelligent persistent memory)
# ---------------------------------------------------------------------------


class Mem0MemoryProvider:
    def __init__(self, api_key: str):
        self._api_key = api_key

    async def get(self, key: str, limit: int, query: str | None = None) -> list[dict[str, Any]]:
        try:
            from mem0 import AsyncMemoryClient  # type: ignore[import]

            client = AsyncMemoryClient(api_key=self._api_key)
            if query:
                results = await client.search(query=query, user_id=key, limit=limit)
            else:
                results = await client.get_all(user_id=key, limit=limit)
            return [
                {"role": "assistant", "content": r.get("memory", r.get("text", ""))}
                for r in (results or [])
            ]
        except ImportError:
            logger.warning("mem0ai not installed. Run: pip install mem0ai")
            return []
        except Exception as e:
            logger.warning(f"mem0 memory get failed: {e}")
            return []

    async def append(self, key: str, messages: list[dict[str, Any]], limit: int) -> None:
        try:
            from mem0 import AsyncMemoryClient  # type: ignore[import]

            client = AsyncMemoryClient(api_key=self._api_key)
            for msg in messages:
                await client.add(
                    messages=[msg],
                    user_id=key,
                )
        except ImportError:
            logger.warning("mem0ai not installed")
        except Exception as e:
            logger.warning(f"mem0 memory append failed: {e}")


# ---------------------------------------------------------------------------
# Factory
# ---------------------------------------------------------------------------


def get_memory_provider(
    memory_type: str,
    context: NodeContext,
    ttl_seconds: int = 86400,
    pinecone_api_key: str = "",
    pinecone_index: str = "",
    qdrant_url: str = "",
    qdrant_collection: str = "",
    openai_api_key: str = "",
    mem0_api_key: str = "",
) -> MemoryProvider:
    if memory_type == "redis":
        return RedisMemoryProvider(ttl_seconds=ttl_seconds)
    if memory_type == "pinecone" and pinecone_api_key and pinecone_index:
        return PineconeMemoryProvider(pinecone_api_key, pinecone_index)
    if memory_type == "qdrant" and qdrant_url and qdrant_collection:
        return QdrantMemoryProvider(qdrant_url, qdrant_collection, openai_api_key)
    if memory_type == "mem0" and mem0_api_key:
        return Mem0MemoryProvider(mem0_api_key)
    return WorkflowMemoryProvider(context)
