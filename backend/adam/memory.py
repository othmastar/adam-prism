"""
Adam Memory — Short-term + Long-term Unified
=============================================
يجمع:
1. Short-term memory (SQLite + FTS5) — للبحث السريع
2. Long-term memory (vector embeddings عبر Ollama) — للـ semantic search
3. Hybrid search (BM25 + Vector) — أفضل من أي واحد لوحده
4. Auto-extraction من المحادثات
5. Memory decay + consolidation

No external dependencies beyond Ollama + SQLite.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import math
import re
import sqlite3
import struct
import time
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx

logger = logging.getLogger("adam_prism.memory")


# ============================================================
# Constants
# ============================================================

EMBEDDING_DIM = 768  # nomic-embed-text
DECAY_HALF_LIFE_DAYS = 30
CONSOLIDATION_SIMILARITY_THRESHOLD = 0.85
BM25_WEIGHT = 0.4
VECTOR_WEIGHT = 0.6


# ============================================================
# Helpers
# ============================================================

def cosine_similarity(a: list[float], b: list[float]) -> float:
    if not a or not b or len(a) != len(b):
        return 0.0
    dot = sum(x * y for x, y in zip(a, b))
    norm_a = math.sqrt(sum(x * x for x in a))
    norm_b = math.sqrt(sum(x * x for x in b))
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot / (norm_a * norm_b)


def serialize_vector(vec: list[float]) -> bytes:
    return struct.pack(f"{len(vec)}f", *vec)


def deserialize_vector(data: bytes) -> list[float]:
    if not data:
        return []
    n = len(data) // 4
    return list(struct.unpack(f"{n}f", data))


# ============================================================
# Embedding Client
# ============================================================

class EmbeddingClient:
    """عميل embeddings عبر Ollama (nomic-embed-text)."""

    def __init__(self, ollama_url: str, model: str = "nomic-embed-text", timeout: float = 30.0):
        self.ollama_url = ollama_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, list[float]] = {}
        self._available: bool | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=3, max_keepalive_connections=2),
            )
        return self._client

    async def embed(self, text: str) -> list[float]:
        """يرجع embedding لنص. يرجع [] لو فشل."""
        if not text.strip():
            return []

        # cache
        h = hashlib.sha256(text.encode()).hexdigest()[:16]
        if h in self._cache:
            return self._cache[h]

        # check availability (one-time)
        if self._available is False:
            return []

        client = await self._get_client()
        try:
            response = await client.post(
                f"{self.ollama_url}/api/embeddings",
                json={"model": self.model, "prompt": text[:8000]},
            )
            if response.status_code != 200:
                if self._available is None:
                    logger.warning(
                        f"Embedding model '{self.model}' not available "
                        f"(status {response.status_code}). Run: ollama pull {self.model}"
                    )
                    self._available = False
                return []

            data = response.json()
            embedding = data.get("embedding", [])
            if embedding and len(embedding) == EMBEDDING_DIM:
                self._available = True
                # cache (limit)
                if len(self._cache) > 500:
                    keys = list(self._cache.keys())[:250]
                    for k in keys:
                        del self._cache[k]
                self._cache[h] = embedding
                return embedding

            logger.warning(f"Bad embedding dim: {len(embedding)}")
            return []
        except Exception as e:
            if self._available is None:
                logger.warning(f"Embedding failed: {e}. Will use BM25 only.")
                self._available = False
            return []

    async def health_check(self) -> bool:
        """يتحقق من توفر الـ model."""
        emb = await self.embed("test")
        ok = len(emb) == EMBEDDING_DIM
        self._available = ok
        return ok

    async def cleanup(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# ============================================================
# Memory Store — unified
# ============================================================

@dataclass
class Memory:
    id: int | None
    content: str
    type: str = "semantic"  # episodic, semantic, procedural, preference
    priority: int = 3
    tags: list[str] = field(default_factory=list)
    source: str = "chat"
    session_id: str | None = None
    created_at: str = ""
    accessed_at: str | None = None
    access_count: int = 0
    decay_score: float = 1.0


@dataclass
class SearchResult:
    memory: Memory
    score: float
    bm25_score: float = 0.0
    vector_score: float = 0.0


class MemoryStore:
    """ذاكرة موحدة: short-term (BM25) + long-term (vector)."""

    def __init__(
        self,
        db_path: str = "~/.adam/memory.db",
        ollama_url: str = "http://localhost:11434",
        embedding_model: str = "nomic-embed-text",
    ):
        self.db_path = str(Path(db_path).expanduser())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.embedding_client = EmbeddingClient(ollama_url, embedding_model)
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()
        self._last_decay = 0.0
        self._init_db()

    def _init_db(self) -> None:
        self._conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            isolation_level=None,
            timeout=30.0,
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")

        # جدول memories
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                content_hash TEXT NOT NULL,
                embedding BLOB,
                type TEXT DEFAULT 'semantic',
                priority INTEGER DEFAULT 3,
                tags TEXT DEFAULT '',
                source TEXT DEFAULT 'chat',
                session_id TEXT,
                created_at TEXT NOT NULL,
                accessed_at TEXT,
                access_count INTEGER DEFAULT 0,
                decay_score REAL DEFAULT 1.0,
                metadata TEXT DEFAULT '{}'
            )
        """)
        self._conn.execute(
            "CREATE UNIQUE INDEX IF NOT EXISTS idx_memories_hash ON memories(content_hash)"
        )

        # FTS5
        try:
            self._conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS memories_fts
                USING fts5(content, tags, type, content='memories', content_rowid='id')
            """)
            self._conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ai AFTER INSERT ON memories
                BEGIN
                    INSERT INTO memories_fts(rowid, content, tags, type)
                    VALUES (new.id, new.content, new.tags, new.type);
                END
            """)
            self._conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_ad AFTER DELETE ON memories
                BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, tags, type)
                    VALUES('delete', old.id, old.content, old.tags, old.type);
                END
            """)
            self._conn.execute("""
                CREATE TRIGGER IF NOT EXISTS memories_au AFTER UPDATE ON memories
                BEGIN
                    INSERT INTO memories_fts(memories_fts, rowid, content, tags, type)
                    VALUES('delete', old.id, old.content, old.tags, old.type);
                    INSERT INTO memories_fts(rowid, content, tags, type)
                    VALUES (new.id, new.content, new.tags, new.type);
                END
            """)
        except sqlite3.OperationalError as e:
            logger.warning(f"FTS5 unavailable: {e}")

        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_type ON memories(type, priority DESC)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_memories_priority ON memories(decay_score DESC, priority DESC)"
        )

        logger.info(f"MemoryStore initialized: {self.db_path}")

    # ============================================================
    # Store
    # ============================================================

    async def store(
        self,
        content: str,
        type: str = "semantic",
        priority: int = 3,
        tags: list[str] | None = None,
        source: str = "chat",
        session_id: str | None = None,
        metadata: dict | None = None,
    ) -> int | None:
        """يخزّن ذكرى مع embedding."""
        if not content.strip():
            return None
        content = content.strip()[:2000]
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]

        # check duplicate
        async with self._lock:
            existing = self._conn.execute(
                "SELECT id, priority FROM memories WHERE content_hash = ?",
                (content_hash,),
            ).fetchone()
            if existing:
                new_priority = max(existing["priority"], priority)
                self._conn.execute(
                    "UPDATE memories SET priority = ?, accessed_at = ?, access_count = access_count + 1 WHERE id = ?",
                    (new_priority, datetime.now().isoformat(), existing["id"]),
                )
                return existing["id"]

        # compute embedding (non-blocking)
        embedding = await self.embedding_client.embed(content)

        now = datetime.now().isoformat()
        tags_str = ",".join(tags) if tags else ""

        async with self._lock:
            cursor = self._conn.execute(
                """INSERT INTO memories
                   (content, content_hash, embedding, type, priority, tags, source,
                    session_id, created_at, accessed_at, access_count, decay_score, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (
                    content, content_hash,
                    serialize_vector(embedding) if embedding else None,
                    type, max(1, min(5, priority)), tags_str, source,
                    session_id, now, now, 0, 1.0,
                    json.dumps(metadata or {}, ensure_ascii=False),
                ),
            )
            mem_id = cursor.lastrowid

        logger.debug(f"Stored memory {mem_id}: type={type}")
        return mem_id

    # ============================================================
    # Search — Hybrid (BM25 + Vector)
    # ============================================================

    async def search(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str | None = None,
        min_priority: int = 1,
    ) -> list[SearchResult]:
        """بحث هجين."""
        if not query.strip():
            return []

        # decay
        self._apply_decay()

        # 1. BM25
        bm25_results = self._bm25_search(query, top_k * 3, memory_type, min_priority)

        # 2. Vector
        query_embedding = await self.embedding_client.embed(query)
        vector_results = []
        if query_embedding:
            vector_results = self._vector_search(
                query_embedding, top_k * 3, memory_type, min_priority
            )

        # 3. Merge
        merged = self._merge_results(bm25_results, vector_results)
        merged.sort(key=lambda x: x.score, reverse=True)
        results = merged[:top_k]

        # update access
        for r in results:
            async with self._lock:
                self._conn.execute(
                    "UPDATE memories SET access_count = access_count + 1, accessed_at = ? WHERE id = ?",
                    (datetime.now().isoformat(), r.memory.id),
                )

        return results

    def _bm25_search(
        self, query: str, limit: int, memory_type: str | None, min_priority: int
    ) -> list[tuple[Memory, float]]:
        clean = re.sub(r'[^\w\s\u0600-\u06FF]', ' ', query)
        words = clean.split()
        if not words:
            return []
        fts_query = " OR ".join(f'"{w}"*' for w in words[:5])

        sql = """
            SELECT m.*, bm25(memories_fts) as score
            FROM memories_fts f
            JOIN memories m ON m.id = f.rowid
            WHERE memories_fts MATCH ?
              AND m.priority >= ?
              AND m.decay_score > 0.1
        """
        params: list = [fts_query, min_priority]
        if memory_type:
            sql += " AND m.type = ?"
            params.append(memory_type)
        sql += " ORDER BY score ASC LIMIT ?"
        params.append(limit)

        try:
            rows = self._conn.execute(sql, params).fetchall()
            max_score = max(abs(r["score"]) for r in rows) if rows else 1.0
            return [
                (self._row_to_memory(r),
                 1.0 - (abs(r["score"]) / max_score if max_score > 0 else 0))
                for r in rows
            ]
        except sqlite3.OperationalError:
            # LIKE fallback
            sql = """SELECT * FROM memories
                     WHERE content LIKE ? AND priority >= ? AND decay_score > 0.1"""
            params = [f"%{query}%", min_priority]
            if memory_type:
                sql += " AND type = ?"
                params.append(memory_type)
            sql += " ORDER BY priority DESC, access_count DESC LIMIT ?"
            params.append(limit)
            rows = self._conn.execute(sql, params).fetchall()
            return [(self._row_to_memory(r), 0.5) for r in rows]

    def _vector_search(
        self, query_embedding: list[float], limit: int,
        memory_type: str | None, min_priority: int
    ) -> list[tuple[Memory, float]]:
        sql = """SELECT * FROM memories
                 WHERE embedding IS NOT NULL AND priority >= ? AND decay_score > 0.1"""
        params: list = [min_priority]
        if memory_type:
            sql += " AND type = ?"
            params.append(memory_type)
        sql += " ORDER BY priority DESC LIMIT 500"
        rows = self._conn.execute(sql, params).fetchall()

        results = []
        for row in rows:
            embedding = deserialize_vector(row["embedding"])
            if not embedding:
                continue
            sim = cosine_similarity(query_embedding, embedding)
            results.append((self._row_to_memory(row), sim))

        results.sort(key=lambda x: x[1], reverse=True)
        return results[:limit]

    def _merge_results(
        self, bm25: list[tuple[Memory, float]], vector: list[tuple[Memory, float]]
    ) -> list[SearchResult]:
        merged: dict[int, SearchResult] = {}
        for mem, score in bm25:
            merged[mem.id] = SearchResult(
                memory=mem,
                score=score * BM25_WEIGHT,
                bm25_score=score,
            )
        for mem, score in vector:
            if mem.id in merged:
                merged[mem.id].vector_score = score
                merged[mem.id].score += score * VECTOR_WEIGHT
            else:
                merged[mem.id] = SearchResult(
                    memory=mem,
                    score=score * VECTOR_WEIGHT,
                    vector_score=score,
                )
        return list(merged.values())

    def _row_to_memory(self, row: sqlite3.Row) -> Memory:
        return Memory(
            id=row["id"],
            content=row["content"],
            type=row["type"],
            priority=row["priority"],
            tags=[t for t in (row["tags"] or "").split(",") if t],
            source=row["source"],
            session_id=row["session_id"],
            created_at=row["created_at"],
            accessed_at=row["accessed_at"],
            access_count=row["access_count"],
            decay_score=row["decay_score"],
        )

    # ============================================================
    # Decay
    # ============================================================

    def _apply_decay(self) -> None:
        if time.time() - self._last_decay < 3600:
            return
        self._last_decay = time.time()
        try:
            self._conn.execute("""
                UPDATE memories
                SET decay_score = MAX(0.05,
                    1.0 - (julianday('now') - COALESCE(julianday(accessed_at), julianday(created_at))) / ?
                )
                WHERE decay_score > 0.05
            """, (DECAY_HALF_LIFE_DAYS * 2,))
        except sqlite3.OperationalError:
            pass

    # ============================================================
    # Recall for context
    # ============================================================

    async def recall_for_context(
        self, query: str, max_memories: int = 5, max_chars: int = 1500
    ) -> str:
        results = await self.search(query, top_k=max_memories)
        if not results:
            return ""
        lines = []
        total = 0
        for r in results:
            line = f"- [{r.memory.type}] {r.memory.content}"
            if total + len(line) > max_chars:
                break
            lines.append(line)
            total += len(line)
        return "\n".join(lines)

    # ============================================================
    # Auto-extraction
    # ============================================================

    async def auto_extract_from_conversation(
        self,
        user_message: str,
        assistant_response: str,
        session_id: str | None,
        auxiliary_client,
    ) -> list[int]:
        """يستخرج ذكريات تلقائياً بـ auxiliary LLM."""
        if not auxiliary_client:
            return []

        prompt = f"""Analyze this conversation and extract memories worth remembering.
Output JSON only: {{"memories": [{{"content": "...", "type": "episodic|semantic|procedural|preference", "priority": 1-5}}]}}

User: {user_message[:500]}
Assistant: {assistant_response[:500]}

Rules:
- Only WORTH REMEMBERING info (not small talk)
- Max 200 chars per memory
- Skip if nothing worth remembering
- Output JSON only"""

        try:
            result = await auxiliary_client.chat(
                [
                    {"role": "system", "content": "You are a memory extractor. Output JSON only."},
                    {"role": "user", "content": prompt},
                ],
                max_tokens=400,
                temperature=0.1,
            )
            result = result.strip()
            if result.startswith("```"):
                result = re.sub(r"^```\w*\n?", "", result)
                result = re.sub(r"\n?```$", "", result)
            data = json.loads(result)
            stored = []
            for mem in data.get("memories", [])[:3]:
                mem_id = await self.store(
                    content=mem.get("content", ""),
                    type=mem.get("type", "semantic"),
                    priority=int(mem.get("priority", 3)),
                    source="auto_extracted",
                    session_id=session_id,
                )
                if mem_id:
                    stored.append(mem_id)
            if stored:
                logger.info(f"Auto-extracted {len(stored)} memories")
            return stored
        except Exception as e:
            logger.debug(f"Auto-extract failed: {e}")
            return []

    # ============================================================
    # Stats & Management
    # ============================================================

    def stats(self) -> dict:
        if not self._conn:
            return {"available": False}
        total = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        with_emb = self._conn.execute(
            "SELECT COUNT(*) FROM memories WHERE embedding IS NOT NULL"
        ).fetchone()[0]
        by_type = {}
        for row in self._conn.execute(
            "SELECT type, COUNT(*) as cnt FROM memories GROUP BY type"
        ).fetchall():
            by_type[row["type"]] = row["cnt"]

        return {
            "available": True,
            "total": total,
            "with_embeddings": with_emb,
            "by_type": by_type,
            "embedding_model": self.embedding_client.model,
            "embedding_available": self.embedding_client._available,
            "db_path": self.db_path,
        }

    async def health_check(self) -> dict:
        return {
            "db_connected": self._conn is not None,
            "embedding_available": await self.embedding_client.health_check(),
            "embedding_model": self.embedding_client.model,
        }

    async def delete(self, memory_id: int) -> bool:
        async with self._lock:
            cursor = self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
            return cursor.rowcount > 0

    async def delete_all(self, memory_type: str | None = None) -> int:
        async with self._lock:
            if memory_type:
                cursor = self._conn.execute(
                    "DELETE FROM memories WHERE type = ?", (memory_type,)
                )
            else:
                cursor = self._conn.execute("DELETE FROM memories")
            return cursor.rowcount

    def close(self) -> None:
        if self._conn:
            self._conn.close()
            self._conn = None
