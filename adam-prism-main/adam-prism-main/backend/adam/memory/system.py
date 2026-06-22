"""
Adam Prism - نظام الذاكرة
========================
ذاكرة طويلة المدى + قصيرة المدى مع Vector Search عبر Qdrant + Nomic Embedding
"""

import asyncio
import logging
from datetime import datetime
from typing import Any

import httpx

from infrastructure import TTLCache

logger = logging.getLogger("adam_prism.memory")

class MemorySystem:
    """
    نظام الذاكرة لآدم بريزم.

    البنية:
    - Short-term: آخر N رسالة في الذاكرة العاملة
    - Long-term: Qdrant vector store مع Nomic embeddings
    - Episodic: أحداث ومواقف مهمة مع سياقها
    """

    def __init__(self, config: dict[str, Any], shared_clients=None):
        self.config = config
        self.shared_clients = shared_clients
        self.qdrant_url = config.get("qdrant_url", "http://localhost:6333")
        self.ollama_base = config.get("ollama_base", "http://localhost:11434")
        self.embedding_model = config.get("embedding_model", "nomic-embed-text")
        self.short_term_limit = config.get("short_term_limit", 50)
        self.embed_cache = TTLCache(default_ttl=600.0, max_size=200)
        self.search_cache = TTLCache(default_ttl=120.0, max_size=100)
        self._init_lock = asyncio.Lock()
        self.collections = {
            "knowledge": "adam_knowledge",
            "conversations": "adam_conversations",
            "patterns": "adam_patterns",
            "reasoning_patterns": "adam_reasoning_patterns",
            "summaries": "adam_summaries",
            "connections": "adam_connections"
        }

        # ذاكرة قصيرة المدى
        self.short_term: list[dict] = []

        # ذاكرة حلقاتية (أحداث مهمة)
        self.episodes: list[dict] = []

    async def _get_client(self, name: str, base_url: str, timeout: float = 30.0) -> httpx.AsyncClient:
        if self.shared_clients:
            return await self.shared_clients.get(name, base_url, timeout)
        attr = f"_pool_{name}"
        if not hasattr(self, attr) or getattr(self, attr) is None:
            setattr(self, attr, httpx.AsyncClient(base_url=base_url, timeout=timeout))
        return getattr(self, attr)

    async def _close_client(self, client):
        if not self.shared_clients and client is not None:
            if hasattr(client, 'aclose') and not client.is_closed:
                await client.aclose()

    async def initialize(self):
        """تهيئة المجموعات في Qdrant"""
        async with self._init_lock:
            client = await self._get_client("qdrant", self.qdrant_url, 30.0)
            try:
                for _coll_type, coll_name in self.collections.items():
                    try:
                        resp = await client.get(f"/collections/{coll_name}")
                        if resp.status_code == 404:
                            await client.put(
                                f"/collections/{coll_name}",
                                json={
                                    "vectors": {
                                        "size": 768,
                                        "distance": "Cosine"
                                    }
                                }
                            )
                            logger.info(f"تم إنشاء مجموعة: {coll_name}")
                    except Exception:
                        logger.exception("خطأ في تهيئة {coll_name}:")
            finally:
                await self._close_client(client)

    async def embed(self, text: str) -> list[float]:
        """تحويل النص إلى embedding عبر Ollama مع كاش"""
        cache_key = self.embed_cache._key(text)
        cached = self.embed_cache.get(cache_key)
        if cached is not None:
            return cached

        client = await self._get_client("ollama", self.ollama_base, 60.0)
        try:
            response = await client.post(
                "/api/embeddings",
                json={
                    "model": self.embedding_model,
                    "prompt": text
                }
            )
            response.raise_for_status()
            embedding = response.json().get("embedding", [])
            if embedding:
                self.embed_cache.set(cache_key, embedding, ttl=600.0)
            return embedding
        finally:
            await self._close_client(client)

    async def store(self, collection: str, text: str, metadata: dict[str, Any],
                    point_id: str | None = None) -> bool:
        """تخزين عنصر في Qdrant"""
        import uuid
        if not point_id:
            point_id = str(uuid.uuid4())

        embedding = await self.embed(text)
        if not embedding:
            logger.error("تعذر في إنشاء embedding")
            return False

        coll_name = self.collections.get(collection, collection)

        client = await self._get_client("qdrant", self.qdrant_url, 30.0)
        try:
            response = await client.put(
                f"/collections/{coll_name}/points",
                json={
                    "points": [{
                        "id": point_id,
                        "vector": embedding,
                        "payload": {
                            "text": text,
                            "metadata": metadata,
                            "timestamp": datetime.now().isoformat()
                        }
                    }]
                }
            )
            return response.status_code == 200
        except Exception:
            logger.exception("خطأ في التخزين:")
            return False
        finally:
            await self._close_client(client)

    async def search(self, query: str, collection: str = "knowledge",
                     top_k: int = 5, score_threshold: float = 0.5) -> list[dict[str, Any]]:
        """البحث الدلالي في القاعدة المعرفية"""
        coll_name = self.collections.get(collection, collection)

        cache_key = self.search_cache._key(query, collection, top_k, score_threshold)
        cached = self.search_cache.get(cache_key)
        if cached is not None:
            return cached

        query_embedding = await self.embed(query)
        if not query_embedding:
            return []

        client = await self._get_client("qdrant", self.qdrant_url, 30.0)
        try:
            response = await client.post(
                f"/collections/{coll_name}/points/search",
                json={
                    "vector": query_embedding,
                    "limit": top_k,
                    "score_threshold": score_threshold,
                    "with_payload": True
                }
            )
            results = response.json().get("result", [])
            parsed = [
                {
                    "id": r.get("id"),
                    "score": r.get("score", 0),
                    "text": r.get("payload", {}).get("text", ""),
                    "metadata": r.get("payload", {}).get("metadata", {})
                }
                for r in results
            ]
            self.search_cache.set(cache_key, parsed, ttl=120.0)
            return parsed
        except Exception:
            logger.exception("خطأ في البحث:")
            return []
        finally:
            await self._close_client(client)

    async def retrieve(self, query: str, top_k: int = 5, collections: list[str] | None = None) -> list[dict[str, Any]]:
        """استرجاع ذكريات ذات صلة (من collections محددة) — بالتوازي"""
        coll_types = collections or ["knowledge", "conversations"]
        tasks = [self.search(query, collection=coll_type, top_k=top_k) for coll_type in coll_types]
        all_results = []
        for coll_type, results in zip(coll_types, await asyncio.gather(*tasks), strict=False):
            for r in results:
                r["source"] = coll_type
                all_results.append(r)
        all_results.sort(key=lambda x: x.get("score", 0), reverse=True)
        return all_results[:top_k]

    async def store_conversation(self, question: str, answer: str, metadata: dict | None = None):
        """تخزين محادثة"""
        text = f"سؤال: {question}\nجواب: {answer}"
        await self.store("conversations", text, metadata or {})

        # إضافة للذاكرة القصيرة
        self.short_term.append({
            "question": question,
            "answer": answer,
            "metadata": metadata,
            "timestamp": datetime.now().isoformat()
        })

        # حفظ حجم الذاكرة القصيرة
        if len(self.short_term) > self.short_term_limit:
            self.short_term = self.short_term[-self.short_term_limit:]

    async def store_knowledge(self, text: str, source: str, topics: list[str] | None = None):
        """تخزين معرفة جديدة"""
        metadata = {
            "source": source,
            "topics": topics or [],
            "type": "knowledge"
        }
        return await self.store("knowledge", text, metadata)

    async def store_pattern(self, pattern: str, pattern_type: str, frequency: int = 1):
        """تخزين نمط تفكير أو سلوك"""
        metadata = {
            "pattern_type": pattern_type,
            "frequency": frequency,
            "type": "pattern"
        }
        return await self.store("patterns", pattern, metadata)

    async def store_summary(self, summary: str, source: str, key_topics: list[str] | None = None):
        """تخزين ملخص"""
        metadata = {
            "source": source,
            "key_topics": key_topics or [],
            "type": "summary"
        }
        return await self.store("summaries", summary, metadata)

    async def store_connection(self, idea_a: str, idea_b: str, connection_type: str, evidence: str = ""):
        """تخزين ربط بين فكرتين"""
        text = f"{idea_a} ↔ {idea_b}: {connection_type}"
        metadata = {
            "idea_a": idea_a,
            "idea_b": idea_b,
            "connection_type": connection_type,
            "evidence": evidence,
            "type": "connection"
        }
        return await self.store("connections", text, metadata)

    def add_episode(self, event: str, context: dict, importance: float = 0.5):
        """إضافة حدق حلقي (episodic memory)"""
        self.episodes.append({
            "event": event,
            "context": context,
            "importance": importance,
            "timestamp": datetime.now().isoformat()
        })

    def get_short_term(self, limit: int = 10) -> list[dict]:
        """استرجاع آخر N من الذاكرة القصيرة"""
        return self.short_term[-limit:]

    def get_stats(self) -> dict:
        """إحصائيات الذاكرة"""
        return {
            "short_term_count": len(self.short_term),
            "episodic_count": len(self.episodes),
            "collections": list(self.collections.keys())
        }
