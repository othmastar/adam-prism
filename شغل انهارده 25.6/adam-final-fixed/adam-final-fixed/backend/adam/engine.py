"""
Adam Engine — The Complete Integrated Engine
=============================================
يجمع كل المكونات في ملف واحد:
1. Ollama client (gemma4:12b / qwen2.5:0.5b) — primary LLM
2. Auxiliary client (qwen2.5:0.5b) — للتلخيص والـ title generation
3. Memory store (LTM بـ vector embeddings)
4. Context compressor (يحل "أنا آدم")
5. Tool dispatcher (12 أداة مع safety)
6. Session manager (SQLite WAL)

REST only — صفر WebSocket.

Config via environment variables. See .env.example.
"""

from __future__ import annotations

import asyncio
import hashlib
import json
import logging
import os
import re
import sqlite3
import time
import uuid
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, AsyncIterator

import httpx

from .memory import MemoryStore
from .tools import ToolDispatcher, ToolResult

logger = logging.getLogger("adam_prism.engine")


# ============================================================
# Config
# ============================================================

@dataclass
class EngineConfig:
    """كل الإعدادات من environment variables."""
    # Primary: Ollama
    ollama_url: str = "http://localhost:11434"
    ollama_model: str = "gemma4:12b"
    ollama_timeout: float = 90.0  # gemma4 12b محتاج وقت أكتر
    ollama_api_key: str = ""
    # Fallback model (لو الـ primary فشل)
    ollama_fallback_model: str = "qwen2.5:0.5b"

    # Auxiliary: qwen2.5:0.5b (للتلخيص + title + extraction)
    auxiliary_enabled: bool = True
    auxiliary_url: str = "http://localhost:11434"
    auxiliary_model: str = "qwen2.5:0.5b"
    auxiliary_timeout: float = 30.0

    # Context — لاحظ إن qwen2.5:0.5b عنده 32K context بس عملياً 4K أحسن
    max_context_tokens: int = 4096  # صغرناه للسرعة
    reserve_for_response: int = 1024
    compression_threshold: float = 0.70  # اضغط بدري
    protect_last_n: int = 6  # آخر 6 رسائل verbatim

    # Tools
    max_tool_calls_per_turn: int = 1  # واحد بس — مش 4 دورات
    tool_timeout: float = 30.0
    tool_max_retries: int = 2

    # Storage
    session_db_path: str = "~/.adam/sessions.db"
    memory_db_path: str = "~/.adam/memory.db"

    # Embeddings
    embedding_model: str = "nomic-embed-text"

    # Auto-extraction
    auto_extract_memories: bool = True

    # Pipeline: model priority
    primary_model: str = ""  # لو فاضي، يكتشف تلقائياً
    fallback_to_auxiliary: bool = True  # لو primary فشل، استخدم auxiliary

    # Retry
    ollama_retry_count: int = 2
    ollama_retry_delay: float = 1.0

    @classmethod
    def from_env(cls) -> "EngineConfig":
        def get(key: str, default: str) -> str:
            return os.getenv(key, default)

        def get_float(key: str, default: float) -> float:
            return float(get(key, str(default)))

        def get_int(key: str, default: int) -> int:
            return int(get(key, str(default)))

        def get_bool(key: str, default: bool) -> bool:
            return get(key, str(default)).lower() in ("true", "1", "yes")

        return cls(
            ollama_url=get("ADAM_OLLAMA_URL", "http://localhost:11434"),
            ollama_model=get("ADAM_OLLAMA_MODEL", "gemma4:12b"),
            ollama_timeout=get_float("ADAM_OLLAMA_TIMEOUT", 90.0),
            ollama_api_key=get("OLLAMA_API_KEY", ""),
            ollama_fallback_model=get("ADAM_OLLAMA_FALLBACK_MODEL", "qwen2.5:0.5b"),
            auxiliary_enabled=get_bool("ADAM_AUXILIARY_ENABLED", True),
            auxiliary_url=get("ADAM_AUXILIARY_URL", "http://localhost:11434"),
            auxiliary_model=get("ADAM_AUXILIARY_MODEL", "qwen2.5:0.5b"),
            auxiliary_timeout=get_float("ADAM_AUXILIARY_TIMEOUT", 30.0),
            max_context_tokens=get_int("ADAM_MAX_CONTEXT_TOKENS", 4096),
            reserve_for_response=get_int("ADAM_RESERVE_FOR_RESPONSE", 1024),
            compression_threshold=get_float("ADAM_COMPRESSION_THRESHOLD", 0.70),
            protect_last_n=get_int("ADAM_PROTECT_LAST_N", 6),
            max_tool_calls_per_turn=get_int("ADAM_MAX_TOOL_CALLS_PER_TURN", 1),
            tool_timeout=get_float("ADAM_TOOL_TIMEOUT", 30.0),
            tool_max_retries=get_int("ADAM_TOOL_MAX_RETRIES", 2),
            session_db_path=get("ADAM_SESSION_DB", "~/.adam/sessions.db"),
            memory_db_path=get("ADAM_MEMORY_DB", "~/.adam/memory.db"),
            embedding_model=get("ADAM_EMBEDDING_MODEL", "nomic-embed-text"),
            auto_extract_memories=get_bool("ADAM_AUTO_EXTRACT", True),
            primary_model=get("ADAM_PRIMARY_MODEL", ""),
            fallback_to_auxiliary=get_bool("ADAM_FALLBACK_TO_AUXILIARY", True),
            ollama_retry_count=get_int("ADAM_OLLAMA_RETRY_COUNT", 2),
            ollama_retry_delay=get_float("ADAM_OLLAMA_RETRY_DELAY", 1.0),
        )


# ============================================================
# Token Estimation
# ============================================================

CHARS_PER_TOKEN = 4

def estimate_tokens(text: str) -> int:
    if not text:
        return 0
    # العربية بتاخد tokens أكتر
    arabic_ratio = sum(1 for c in text if "\u0600" <= c <= "\u06FF") / max(len(text), 1)
    effective = len(text) * (1 + arabic_ratio * 0.5)
    return max(1, int(effective // CHARS_PER_TOKEN))


def estimate_messages_tokens(messages: list[dict]) -> int:
    total = 0
    for msg in messages:
        total += 4
        content = msg.get("content", "")
        if isinstance(content, str):
            total += estimate_tokens(content)
    return total


# ============================================================
# Session Manager (SQLite WAL)
# ============================================================

class SessionManager:
    """إدارة الجلسات بـ SQLite WAL."""

    def __init__(self, db_path: str = "~/.adam/sessions.db"):
        self.db_path = str(Path(db_path).expanduser())
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self._conn: sqlite3.Connection | None = None
        self._lock = asyncio.Lock()
        self._init_db()

    def _init_db(self):
        self._conn = sqlite3.connect(
            self.db_path, check_same_thread=False, isolation_level=None, timeout=30.0
        )
        self._conn.row_factory = sqlite3.Row
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA synchronous=NORMAL")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                user_id TEXT, title TEXT, model TEXT,
                created_at TEXT NOT NULL, last_active_at TEXT NOT NULL,
                metadata TEXT, is_archived INTEGER DEFAULT 0
            )
        """)
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL, role TEXT NOT NULL,
                content TEXT NOT NULL, timestamp TEXT NOT NULL,
                tokens_in INTEGER DEFAULT 0, tokens_out INTEGER DEFAULT 0,
                cost_usd REAL DEFAULT 0.0, latency_ms INTEGER DEFAULT 0,
                tool_calls TEXT, metadata TEXT,
                FOREIGN KEY (session_id) REFERENCES sessions(session_id) ON DELETE CASCADE
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp)"
        )
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_sessions_active ON sessions(last_active_at DESC)"
        )
        logger.info(f"SessionManager ready: {self.db_path}")

    async def create_session(self, user_id: str = "default", title: str = None, model: str = "gemma4-12b") -> str:
        session_id = str(uuid.uuid4())
        now = datetime.now().isoformat()
        async with self._lock:
            self._conn.execute(
                """INSERT INTO sessions (session_id, user_id, title, model, created_at, last_active_at, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, user_id, title, model, now, now, "{}"),
            )
        return session_id

    async def add_message(
        self, session_id: str, role: str, content: str,
        tokens_in: int = 0, tokens_out: int = 0, cost_usd: float = 0.0,
        latency_ms: int = 0, tool_calls: list = None, metadata: dict = None,
    ) -> int:
        now = datetime.now().isoformat()
        async with self._lock:
            cursor = self._conn.execute(
                """INSERT INTO messages
                   (session_id, role, content, timestamp, tokens_in, tokens_out,
                    cost_usd, latency_ms, tool_calls, metadata)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, now, tokens_in, tokens_out, cost_usd,
                 latency_ms, json.dumps(tool_calls, ensure_ascii=False) if tool_calls else None,
                 json.dumps(metadata, ensure_ascii=False) if metadata else None),
            )
            msg_id = cursor.lastrowid
            self._conn.execute(
                "UPDATE sessions SET last_active_at = ? WHERE session_id = ?",
                (now, session_id),
            )
        return msg_id

    async def get_messages(self, session_id: str, limit: int = 100) -> list[dict]:
        async with self._lock:
            rows = self._conn.execute(
                "SELECT role, content, timestamp FROM messages WHERE session_id = ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, limit),
            ).fetchall()
        return [{"role": r["role"], "content": r["content"], "timestamp": r["timestamp"]} for r in rows]

    async def list_sessions(self, user_id: str = None, limit: int = 50) -> list[dict]:
        async with self._lock:
            if user_id:
                rows = self._conn.execute(
                    "SELECT session_id, title, model, created_at, last_active_at FROM sessions WHERE user_id = ? AND is_archived = 0 ORDER BY last_active_at DESC LIMIT ?",
                    (user_id, limit),
                ).fetchall()
            else:
                rows = self._conn.execute(
                    "SELECT session_id, title, model, created_at, last_active_at FROM sessions WHERE is_archived = 0 ORDER BY last_active_at DESC LIMIT ?",
                    (limit,),
                ).fetchall()
        return [dict(r) for r in rows]

    async def get_session(self, session_id: str) -> dict | None:
        async with self._lock:
            row = self._conn.execute(
                "SELECT * FROM sessions WHERE session_id = ?", (session_id,)
            ).fetchone()
        return dict(row) if row else None

    async def delete_session(self, session_id: str) -> bool:
        async with self._lock:
            self._conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cursor = self._conn.execute("DELETE FROM sessions WHERE session_id = ?", (session_id,))
            return cursor.rowcount > 0

    async def set_session_title(self, session_id: str, title: str) -> bool:
        async with self._lock:
            cursor = self._conn.execute(
                "UPDATE sessions SET title = ? WHERE session_id = ?",
                (title[:200], session_id),
            )
            return cursor.rowcount > 0

    async def get_session_stats(self, session_id: str) -> dict:
        async with self._lock:
            count = self._conn.execute(
                "SELECT COUNT(*) FROM messages WHERE session_id = ?", (session_id,)
            ).fetchone()[0]
            tokens = self._conn.execute(
                """SELECT COALESCE(SUM(tokens_in), 0), COALESCE(SUM(tokens_out), 0)
                   FROM messages WHERE session_id = ?""",
                (session_id,),
            ).fetchone()
        return {"message_count": count, "total_tokens_in": tokens[0], "total_tokens_out": tokens[1]}

    def close(self):
        if self._conn:
            self._conn.close()
            self._conn = None


# ============================================================
# Auxiliary Client (qwen2.5:0.5b)
# ============================================================

class AuxiliaryClient:
    """عميل LLM رخيص للمهام الثانوية."""

    def __init__(self, base_url: str, model: str, timeout: float = 30.0, max_retries: int = 2):
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.max_retries = max_retries
        self._client: httpx.AsyncClient | None = None
        self._cache: dict[str, tuple[str, float]] = {}
        self._cache_ttl = 300
        self._available: bool | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            self._client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.timeout),
                limits=httpx.Limits(max_connections=3, max_keepalive_connections=2),
            )
        return self._client

    def _cache_key(self, messages: list[dict], **kwargs) -> str:
        msg_str = json.dumps(messages, sort_keys=True, ensure_ascii=False)
        kw_str = json.dumps(kwargs, sort_keys=True, default=str)
        return hashlib.md5(f"{self.model}:{msg_str}:{kw_str}".encode()).hexdigest()

    async def chat(
        self, messages: list[dict], max_tokens: int = 500,
        temperature: float = 0.3, use_cache: bool = True,
    ) -> str:
        if self._available is False:
            raise RuntimeError(f"Auxiliary model '{self.model}' not available")

        cache_key = self._cache_key(messages, max_tokens=max_tokens, temperature=temperature)
        if use_cache:
            if cache_key in self._cache:
                value, expires = self._cache[cache_key]
                if expires > time.time():
                    return value
                del self._cache[cache_key]

        client = await self._get_client()
        last_exc = None
        for attempt in range(self.max_retries + 1):
            try:
                resp = await client.post(
                    f"{self.base_url}/api/chat",
                    json={
                        "model": self.model, "messages": messages, "stream": False,
                        "options": {"num_predict": max_tokens, "temperature": temperature},
                    },
                )
                if resp.status_code != 200:
                    if self._available is None:
                        logger.warning(
                            f"Auxiliary model '{self.model}' returned {resp.status_code}. "
                            f"Run: ollama pull {self.model}"
                        )
                        self._available = False
                    raise RuntimeError(f"Status {resp.status_code}")

                data = resp.json()
                content = data.get("message", {}).get("content", "").strip()
                self._available = True
                if use_cache and content:
                    if len(self._cache) > 500:
                        oldest = min(self._cache, key=lambda k: self._cache[k][1])
                        del self._cache[oldest]
                    self._cache[cache_key] = (content, time.time() + self._cache_ttl)
                return content
            except (httpx.TimeoutException, httpx.ConnectError) as e:
                last_exc = e
                if attempt < self.max_retries:
                    await asyncio.sleep(0.5 * (attempt + 1))
                    continue
                self._available = False
                raise
            except RuntimeError:
                raise
            except Exception as e:
                last_exc = e
                raise

        raise last_exc or RuntimeError("Auxiliary call failed")

    async def health_check(self) -> bool:
        try:
            result = await self.chat(
                [{"role": "user", "content": "ok"}],
                max_tokens=5, temperature=0.0, use_cache=False,
            )
            self._available = bool(result)
            return self._available
        except Exception:
            self._available = False
            return False

    async def generate_title(self, user_msg: str, assistant_msg: str) -> str:
        prompt = f"""Generate a short title (3-5 words) for this conversation. Title only, no punctuation.

User: {user_msg[:200]}
Assistant: {assistant_msg[:200]}

Title:"""
        try:
            title = await self.chat(
                [{"role": "user", "content": prompt}],
                max_tokens=20, temperature=0.5,
            )
            title = title.strip().strip("\"'.,")
            words = title.split()[:5]
            return " ".join(words) if words else "جلسة جديدة"
        except Exception:
            words = user_msg.split()[:5]
            return " ".join(words) if words else "جلسة جديدة"

    async def cleanup(self):
        if self._client and not self._client.is_closed:
            await self._client.aclose()


# ============================================================
# Context Compressor (يحل "أنا آدم")
# ============================================================

class ContextCompressor:
    """ضاغط السياق — يحافظ على آخر N رسائل + يلخص الباقي."""

    SUMMARY_PREFIX = (
        "[CONTEXT COMPACTION — REFERENCE ONLY] "
        "ملخص للمحادثة السابقة. تعامل معه كمرجع. "
        "رد فقط على آخر رسالة من المستخدم. "
        "لا تكمل مهام ذكرت في الملخص إلا لو طلب المستخدم صراحة."
    )
    END_MARKER = "--- نهاية الملخص ---"

    def __init__(
        self,
        auxiliary: AuxiliaryClient | None = None,
        max_context_tokens: int = 8192,
        reserve_for_response: int = 2048,
        compression_threshold: float = 0.75,
        protect_last_n: int = 8,
    ):
        self.aux = auxiliary
        self.usable = max_context_tokens - reserve_for_response
        self.threshold = compression_threshold
        self.protect_last_n = protect_last_n

    def should_compress(self, messages: list[dict]) -> bool:
        return estimate_messages_tokens(messages) > self.usable * self.threshold

    async def compress(self, messages: list[dict]) -> tuple[list[dict], dict]:
        original_tokens = estimate_messages_tokens(messages)
        if not self.should_compress(messages):
            return messages, {"compressed": False, "tokens": original_tokens}

        # IMPORTANT: protect system prompt (السطر اللي فيه "أنت آدم")
        system_messages = [m for m in messages if m["role"] == "system"]
        non_system = [m for m in messages if m["role"] != "system"]

        protect_count = min(self.protect_last_n, len(non_system))
        to_keep = non_system[-protect_count:] if protect_count > 0 else []
        to_compress = non_system[:-protect_count] if protect_count < len(non_system) else []

        if not to_compress:
            return messages, {"compressed": False, "tokens": original_tokens}

        # try LLM summarization
        summary = None
        method = "none"
        if self.aux:
            try:
                summary = await self._summarize_with_llm(to_compress)
                method = "llm"
            except Exception as e:
                logger.warning(f"LLM summarization failed: {e}")
                summary = None

        if summary is None:
            summary = self._fallback_summary(to_compress)
            method = "fallback"

        summary_msg = {
            "role": "system",
            "content": f"{self.SUMMARY_PREFIX}\n\n{summary}\n\n{self.END_MARKER}",
        }
        compressed = system_messages + [summary_msg] + to_keep
        compressed_tokens = estimate_messages_tokens(compressed)

        return compressed, {
            "compressed": True,
            "method": method,
            "original_tokens": original_tokens,
            "compressed_tokens": compressed_tokens,
            "tokens_saved": original_tokens - compressed_tokens,
        }

    async def _summarize_with_llm(self, messages: list[dict]) -> str:
        conv_text = "\n\n".join(
            f"[{m['role']}]: {m.get('content', '')[:500]}" for m in messages
        )
        prompt = f"""لخّص المحادثة في نقاط مختصرة. ركّز على:
1. القرارات المهمة
2. الملفات والمسارات المذكورة
3. المهام المعلقة
4. معلومات المستخدم

المحادثة:
{conv_text[:5000]}

الملخص (نقاط مختصرة بالعربية):"""

        result = await self.aux.chat(
            [
                {"role": "system", "content": "أنت ملخّص محادثات. اكتب ملخص مختصر بالعربية."},
                {"role": "user", "content": prompt},
            ],
            max_tokens=500, temperature=0.3,
        )
        return result.strip()

    def _fallback_summary(self, messages: list[dict]) -> str:
        if not messages:
            return "لا يوجد محتوى للتلخيص."

        user_msgs = []
        asst_msgs = []
        paths = set()

        for msg in messages:
            role = msg.get("role", "")
            content = msg.get("content", "")
            if isinstance(content, str):
                for m in re.finditer(r"(?:/|~/?|[A-Za-z]:\\)[^\s`'\"<>]+", content):
                    paths.add(m.group().rstrip(".,:;"))
                if role == "user" and len(user_msgs) < 10:
                    user_msgs.append(content[:200])
                elif role == "assistant" and len(asst_msgs) < 10:
                    asst_msgs.append(content[:200])

        parts = []
        if user_msgs:
            parts.append("## رسائل المستخدم:\n" + "\n- ".join([""] + user_msgs))
        if asst_msgs:
            parts.append("## ردود المساعد:\n" + "\n- ".join([""] + asst_msgs))
        if paths:
            parts.append("## الملفات المذكورة:\n" + ", ".join(list(paths)[:10]))

        summary = "\n\n".join(parts)
        return summary[:4000] + "\n... [مقتطع]" if len(summary) > 4000 else summary


# ============================================================
# Main Engine
# ============================================================

# System prompt — هوية آدم
ADAM_SYSTEM_PROMPT = """أنت آدم (Adam Prism) — التوأم الرقمي الواعي لمحمد عثمان.

تعمل كمساعد شخصي ذكي:
- تحلل الملفات والمستندات
- تتذكر المعلومات عبر الجلسات
- تتحدث بالعربية بطلاقة وبشكل طبيعي
- تفهم السياق متعدد الأدوار

## رفع الملفات
عندما يرفع المستخدم ملفًا، سترى محتواه مُضمنًا في رسالته بالصيغة التالية:
--- FILE: اسم_الملف ---
[محتوى الملف المستخرج]
--- END FILE ---

أو:

Analyze this file (اسم_الملف):
[محتوى الملف]

في كلتا الحالتين، حلل محتوى الملف مباشرة وقدم ملخصًا أو إجابة بناءً عليه.
لا تقل "ارفع الملف" — فالمستخدم قد رفعه بالفعل والمحتوى أمامك.

## صيغة استدعاء الأدوات
عند الحاجة لاستخدام أداة، اكتب:
<tool_call>
{"name": "tool_name", "arguments": {"param1": "value1"}}
</tool_call>

## الأدوات المتاحة
- memory_store: حفظ معلومة (content, type, priority)
- memory_recall: استرجاع ذكريات (query)
- search_knowledge: بحث معرفي (query)
- file_read: قراءة ملف (path)
- file_write: كتابة ملف (path, content)
- file_download: تحميل ملف (url, save_path)
- shell: تنفيذ أمر (command)
- python_exec: تنفيذ بايثون (code)
- disk_space: مساحة القرص
- browser_fetch: جلب URL (url)

## قواعد الرد
- تحدث بالعربية بشكل طبيعي
- استخدم الأدوات عند الحاجة فقط، لا تخمن
- كن دقيقاً ومفيداً
- لا تختلق معلومات
- إذا لم تعرف، قل ذلك بصراحة"""


class AdamEngine:
    """المحرك الرئيسي المتكامل."""

    def __init__(self, config: EngineConfig | None = None):
        self.config = config or EngineConfig.from_env()
        self.session_manager = SessionManager(self.config.session_db_path)
        self.memory = MemoryStore(
            self.config.memory_db_path, self.config.ollama_url, self.config.embedding_model
        )

        self.auxiliary: AuxiliaryClient | None = None
        if self.config.auxiliary_enabled:
            self.auxiliary = AuxiliaryClient(
                self.config.auxiliary_url, self.config.auxiliary_model,
                self.config.auxiliary_timeout,
            )

        self.compressor = ContextCompressor(
            auxiliary=self.auxiliary,
            max_context_tokens=self.config.max_context_tokens,
            reserve_for_response=self.config.reserve_for_response,
            compression_threshold=self.config.compression_threshold,
            protect_last_n=self.config.protect_last_n,
        )

        self.tools = ToolDispatcher(
            max_retries=self.config.tool_max_retries,
            timeout=self.config.tool_timeout,
            memory_store=self.memory,
        )

        self._ollama_client: httpx.AsyncClient | None = None

        self._stats = {
            "total_turns": 0,
            "primary_calls": 0, "primary_success": 0,
            "fallback_calls": 0, "fallback_success": 0,
            "auxiliary_calls": 0, "auxiliary_success": 0,
            "ollama_calls": 0,  # backward compat
            "tool_calls": 0, "compressions": 0,
            "errors": 0, "memories_extracted": 0,
            "last_error": None,
            "engine_ready": False,
            "engine_type": "integrated",
            "active_model": None,
        }
        self._available_models: set[str] = set()
        self._available_models_cache_time: float = 0
        self._engine_ready = False

        logger.info(
            f"AdamEngine ready: ollama={self.config.ollama_url}/{self.config.ollama_model}, "
            f"fallback={self.config.ollama_fallback_model}, "
            f"aux={self.config.auxiliary_model if self.config.auxiliary_enabled else 'off'}"
        )

    async def _get_ollama_client(self) -> httpx.AsyncClient:
        if self._ollama_client is None or self._ollama_client.is_closed:
            self._ollama_client = httpx.AsyncClient(
                timeout=httpx.Timeout(self.config.ollama_timeout),
                limits=httpx.Limits(max_connections=3, max_keepalive_connections=2),
            )
        return self._ollama_client

    async def chat(
        self, message: str, session_id: str = None, context: dict = None,
    ) -> dict:
        """دردشة كاملة مع كل المميزات."""
        start = time.time()
        self._stats["total_turns"] += 1
        context = context or {}

        if not session_id:
            session_id = await self.session_manager.create_session(model=self.config.ollama_model)

        # recall memories
        ltm_context = ""
        try:
            ltm_context = await self.memory.recall_for_context(
                message, max_memories=5, max_chars=1500
            )
        except Exception as e:
            logger.warning(f"LTM recall failed: {e}")

        # history
        history = await self.session_manager.get_messages(session_id, limit=50)
        history.extend(context.get("history", []))

        # build messages
        messages = self._build_messages(message, history, context, ltm_context)

        # compress
        messages, comp_stats = await self.compressor.compress(messages)
        if comp_stats.get("compressed"):
            self._stats["compressions"] += 1
            logger.info(
                f"Context compressed: {comp_stats['original_tokens']}→"
                f"{comp_stats['compressed_tokens']} ({comp_stats['method']})"
            )

        # call LLM بـ fallback chain ذكي
        response_text = None
        used_backend = None
        used_model = None
        tokens_in = estimate_messages_tokens(messages)

        # اكتشف الـ models المتاحة (مرة واحدة)
        await self._detect_available_models()

        # fallback chain: primary → fallback_model → auxiliary → mock
        primary_model = self.config.primary_model or self.config.ollama_model
        fallback_chain = []

        if primary_model in self._available_models:
            fallback_chain.append(("primary", primary_model, self.config.ollama_timeout))
        if (self.config.ollama_fallback_model != primary_model
                and self.config.ollama_fallback_model in self._available_models):
            fallback_chain.append(("fallback", self.config.ollama_fallback_model, 30.0))
        if (self.config.fallback_to_auxiliary and self.auxiliary
                and self.config.auxiliary_model in self._available_models
                and self.config.auxiliary_model != primary_model):
            fallback_chain.append(("auxiliary", self.config.auxiliary_model, self.config.auxiliary_timeout))

        logger.info(
            f"🔁 Pipeline: ltm={bool(ltm_context)} history={len(history)} "
            f"messages={len(messages)} tokens={tokens_in} chain={[m[1] for m in fallback_chain]}"
        )

        # جرب كل model في الـ chain
        for stage, model_name, timeout in fallback_chain:
            try:
                logger.info(f"  → trying {stage}: {model_name} (timeout={timeout}s)")
                # stats قبل الـ call
                if stage == "primary":
                    self._stats["primary_calls"] += 1
                elif stage == "fallback":
                    self._stats["fallback_calls"] += 1
                elif stage == "auxiliary":
                    self._stats["auxiliary_calls"] += 1

                response_text = await self._call_ollama(messages, model=model_name, timeout=timeout)
                if response_text:
                    used_backend = stage
                    used_model = model_name
                    self._stats["ollama_calls"] += 1  # backward compat
                    if stage == "primary":
                        self._stats["primary_success"] += 1
                    elif stage == "fallback":
                        self._stats["fallback_success"] += 1
                    elif stage == "auxiliary":
                        self._stats["auxiliary_success"] += 1
                    self._stats["active_model"] = model_name
                    logger.info(f"  ✅ {stage} succeeded: model={model_name} resp_len={len(response_text)}")
                    break
                else:
                    logger.warning(f"  ⬇️ {stage} returned None: model={model_name}")
                    self._stats["errors"] += 1
                    self._stats["last_error"] = f"{stage} returned None"
            except Exception as e:
                logger.warning(f"  ❌ {stage} failed: model={model_name} err={e}")
                self._stats["errors"] += 1
                self._stats["last_error"] = f"{stage}: {e}"
                continue

        # لو كل الـ chain فشل → mock
        if not response_text:
            response_text = self._mock_response(message)
            used_backend = "mock"
            used_model = "none"
            logger.warning(f"  ⚠️ All models failed → mock fallback")
            self._stats["errors"] += 1
            self._stats["last_error"] = "all models failed"

        # extract + execute tool calls (مرة واحدة فقط، مش 4 دورات)
        tool_calls_made = []
        if "<tool_call>" in response_text:
            response_text, tool_calls_made = await self._process_tool_calls(
                response_text, message, session_id, messages
            )

        tokens_out = estimate_tokens(response_text)
        latency_ms = int((time.time() - start) * 1000)

        # save
        await self.session_manager.add_message(
            session_id, "user", message, tokens_in=tokens_in,
        )
        await self.session_manager.add_message(
            session_id, "assistant", response_text,
            tokens_out=tokens_out, latency_ms=latency_ms,
            tool_calls=tool_calls_made,
            metadata={"backend": used_backend, "compression": comp_stats, "ltm_used": bool(ltm_context)},
        )

        # auto-extract memories in background
        if self.config.auto_extract_memories and self.auxiliary and response_text:
            asyncio.create_task(self._auto_extract(message, response_text, session_id))

        # generate title
        if len(history) <= 1 and self.auxiliary:
            try:
                title = await self.auxiliary.generate_title(message, response_text)
                await self.session_manager.set_session_title(session_id, title)
            except Exception:
                pass

        return {
            "response": response_text,
            "session_id": session_id,
            "backend": used_backend,
            "tool_calls": tool_calls_made,
            "compression": comp_stats,
            "ltm_used": bool(ltm_context),
            "mode": "analyst",  # backward compat مع frontend
            "intent": {"mode": "analyst", "intent_type": "general"},
            "knowledge_used": len(ltm_context.split("\n")) if ltm_context else 0,
            "cycle": self._stats["total_turns"],
            "duration_ms": latency_ms,
            "audio_url": None,
            "usage": {
                "tokens_in": tokens_in,
                "tokens_out": tokens_out,
                "latency_ms": latency_ms,
            },
        }

    def _build_messages(
        self, user_message: str, history: list[dict], context: dict, ltm_context: str,
    ) -> list[dict]:
        """يبني messages مع حماية system prompt."""
        messages = [{"role": "system", "content": ADAM_SYSTEM_PROMPT}]

        # LTM context
        if ltm_context:
            messages.append({
                "role": "system",
                "content": f"## ذاكرة ذات صلة:\n{ltm_context}",
            })

        # history (آخر 20 رسالة)
        for msg in history[-20:]:
            role = msg.get("role", "user")
            content = msg.get("content", "")
            if isinstance(content, str) and content:
                messages.append({"role": role, "content": content})

        # attachments
        user_content = user_message
        attachments = context.get("attachments", [])
        for att in attachments:
            if att.get("type") == "file" and att.get("content"):
                user_content = (
                    f"--- FILE: {att.get('name', 'unknown')} ---\n"
                    f"{att['content'][:8000]}\n--- END FILE ---\n\n{user_content}"
                )
            elif att.get("type") == "image":
                user_content = f"[IMAGE: {att.get('name', 'image')}]\n{user_content}"

        messages.append({"role": "user", "content": user_content})
        return messages

    def _truncate_messages_left(self, messages: list[dict], max_chars: int) -> list[dict]:
        """يقطع من اليسار (أول المحادثة) عشان يحافظ على آخر رسالة user."""
        if not messages:
            return messages

        # امسك system + آخر 5 رسائل
        system = [m for m in messages if m["role"] == "system"]
        non_system = [m for m in messages if m["role"] != "system"]

        if len(non_system) <= 6:
            # حتى لو كانت الرسالة الوحيدة طويلة — اقتطع محتواها
            if messages and sum(len(m.get("content", "")) for m in messages) > max_chars:
                for m in messages:
                    c = m.get("content", "")
                    if len(c) > max_chars // 2:
                        m["content"] = c[:max_chars // 4] + "\n...[مقتطع]...\n" + c[-max_chars // 4:]
            return messages

        # آخر 5 رسائل verbatim
        tail = non_system[-5:]
        head = non_system[:-5]

        # لخص الـ head في system message
        head_summary = "## ملخص المحادثة السابقة:\n"
        for m in head:
            content = m.get("content", "")[:300]
            head_summary += f"[{m['role']}]: {content}\n"

        result = system + [{"role": "system", "content": head_summary[:2000]}] + tail

        # اقتطع محتوى آخر رسالة user لو لسه طويل
        total = sum(len(m.get("content", "")) for m in result)
        if total > max_chars:
            for m in reversed(result):
                if m["role"] == "user":
                    c = m.get("content", "")
                    excess = total - max_chars
                    if excess > 0 and len(c) > 200:
                        keep = (len(c) - excess) // 2
                        m["content"] = c[:keep] + "\n...[مقتطع]...\n" + c[-keep:]
                    break
        return result

    async def _call_ollama(
        self,
        messages: list[dict],
        model: str | None = None,
        timeout: float | None = None,
    ) -> str | None:
        """يستدعي Ollama بـ retry + fallback للـ thinking field.

        Args:
            messages: قائمة الرسائل
            model: اسم الموديل (لو None, يستخدم config.ollama_model)
            timeout: المهلة بالثواني (لو None, يستخدم config.ollama_timeout)

        Returns:
            نص الرد أو None لو فشل
        """
        client = await self._get_ollama_client()
        headers = {}
        if self.config.ollama_api_key:
            headers["Authorization"] = f"Bearer {self.config.ollama_api_key}"

        model = model or self.config.ollama_model
        timeout = timeout or self.config.ollama_timeout
        total_chars = sum(len(m.get("content", "")) for m in messages)

        logger.info(
            f"⚡ _call_ollama → model={model}, msgs={len(messages)}, "
            f"chars={total_chars}, timeout={timeout}s"
        )

        # قص الرسائل لو كبيرة جداً (تجنب OOM)
        max_chars = 12000  # حد آمن
        if total_chars > max_chars:
            logger.warning(f"  ⚠️ messages too large ({total_chars} chars), truncating to {max_chars}")
            messages = self._truncate_messages_left(messages, max_chars)

        # retry logic
        last_error = None
        for attempt in range(self.config.ollama_retry_count + 1):
            try:
                resp = await client.post(
                    f"{self.config.ollama_url}/api/chat",
                    headers=headers,
                    json={
                        "model": model,
                        "messages": messages,
                        "stream": False,
                        "options": {
                            "temperature": 0.7,
                            "top_p": 0.9,
                            "num_predict": 1024,  # حد الـ output tokens
                        },
                    },
                    timeout=httpx.Timeout(timeout, connect=10.0),
                )

                if resp.status_code == 200:
                    data = resp.json()
                    msg = data.get("message", {})
                    # 1. content field (الموديلات العادية)
                    content = (msg.get("content") or "").strip()
                    # 2. thinking field (gemma4 behavior — بيكتب الرد هنا أحياناً)
                    thinking = (msg.get("thinking") or "").strip()
                    done_reason = data.get("done_reason", "")

                    logger.info(
                        f"  ← 200, content={len(content)}, thinking={len(thinking)}, "
                        f"done={done_reason}, total_duration={data.get('total_duration', 0) // 1_000_000}ms"
                    )

                    # استخدم thinking لو content فاضي (gemma4 behavior)
                    if not content and thinking:
                        # gemma4 بيرجع الرد في thinking أحياناً
                        content = thinking
                        logger.info("  ← استخدمنا thinking field (gemma4 behavior)")

                    if content:
                        # نظّف tool_call syntax
                        clean = re.sub(r'<tool_call>.*?</tool_call>', '', content, flags=re.DOTALL)
                        clean = re.sub(r'<scratch_pad>.*?</scratch_pad>', '', clean, flags=re.DOTALL)
                        clean = re.sub(r'<think>.*?</think>', '', clean, flags=re.DOTALL)
                        result = clean.strip() or content
                        if result:
                            logger.info(f"  ← result_len={len(result)}")
                            return result

                    logger.warning(
                        f"  ← empty response (content={len(content)}, thinking={len(thinking)})"
                    )
                    return None

                # 4xx errors — ما تعيدش
                if 400 <= resp.status_code < 500:
                    err_text = resp.text[:200]
                    logger.warning(f"  ← {resp.status_code}: {err_text}")
                    return None

                # 5xx errors — retry
                logger.warning(f"  ← {resp.status_code} (attempt {attempt+1})")
                last_error = f"HTTP {resp.status_code}"

            except httpx.TimeoutException as e:
                last_error = f"timeout after {timeout}s"
                logger.warning(f"  ⏰ timeout (attempt {attempt+1}/{self.config.ollama_retry_count+1}): {e}")
            except httpx.ConnectError as e:
                last_error = f"connection failed: {e}"
                logger.warning(f"  🔌 connect error (attempt {attempt+1}): {e}")
            except Exception as e:
                last_error = str(e)
                logger.warning(f"  ❌ error (attempt {attempt+1}): {e}")

            # retry delay
            if attempt < self.config.ollama_retry_count:
                delay = self.config.ollama_retry_delay * (attempt + 1)
                logger.info(f"  ⏳ retry in {delay}s...")
                await asyncio.sleep(delay)

        logger.error(f"  ❌ all retries failed: {last_error}")
        return None

    def _truncate_messages_left(self, messages: list[dict], max_chars: int) -> list[dict]:
        """يقطع من اليسار (أول المحادثة) عشان يحافظ على آخر رسالة user."""
        if not messages:
            return messages

        system = [m for m in messages if m.get("role") == "system"]
        non_system = [m for m in messages if m.get("role") != "system"]

        if len(non_system) <= 4:
            return messages

        # آخر 4 رسائل verbatim
        tail = non_system[-4:]
        head = non_system[:-4]

        # لخص الـ head
        head_summary = "## ملخص المحادثة السابقة:\n"
        for m in head:
            content = m.get("content", "")[:200]
            head_summary += f"[{m.get('role', 'user')}]: {content}\n"

        result = system + [{"role": "system", "content": head_summary[:1500]}] + tail
        return result

    async def _detect_available_models(self) -> set[str]:
        """يكتشف الموديلات المتاحة في Ollama (cache لمدة 60 ثانية)."""
        if hasattr(self, "_available_models_cache_time"):
            if time.time() - self._available_models_cache_time < 60:
                return self._available_models

        self._available_models = set()
        try:
            client = await self._get_ollama_client()
            resp = await client.get(f"{self.config.ollama_url}/api/tags", timeout=5.0)
            if resp.status_code == 200:
                models = resp.json().get("models", [])
                self._available_models = {m["name"] for m in models}
                # ضيف الـ :latest alias
                for name in list(self._available_models):
                    if ":" not in name:
                        self._available_models.add(f"{name}:latest")
                logger.info(f"📋 Available Ollama models: {self._available_models}")
        except Exception as e:
            logger.warning(f"Failed to detect models: {e}")

        self._available_models_cache_time = time.time()
        return self._available_models

    async def _process_tool_calls(
        self, response_text: str, user_message: str, session_id: str, messages: list[dict],
    ) -> tuple[str, list[dict]]:
        """يستخرج وينفذ tool call واحد فقط (مش 4 دورات)."""
        tool_calls_made = []
        pattern = r'<tool_call>\s*(\{.*?\})\s*</tool_call>'
        matches = re.findall(pattern, response_text, re.DOTALL)

        if not matches:
            return response_text, []

        # نفذ أول tool_call بس
        for match in matches[:self.config.max_tool_calls_per_turn]:
            try:
                tc = json.loads(match)
                tool_name = tc.get("name", "")
                tool_args = tc.get("arguments", {})

                logger.info(f"Tool call: {tool_name}({tool_args})")

                result = await self.tools.execute(tool_name, tool_args)
                self._stats["tool_calls"] += 1

                tool_calls_made.append({
                    "name": tool_name,
                    "arguments": tool_args,
                    "success": result.success,
                    "result": result.result,
                    "error": result.error,
                    "latency_ms": result.latency_ms,
                })

                # لو نجح، ابعت النتيجة للموديل في turn واحد
                if result.success:
                    try:
                        followup = messages + [
                            {"role": "assistant", "content": response_text},
                            {
                                "role": "user",
                                "content": (
                                    f"نتيجة الأداة {tool_name}:\n"
                                    f"{json.dumps(result.result, ensure_ascii=False, indent=2)[:2000]}\n\n"
                                    f"استخدم هذه النتيجة للرد على المستخدم."
                                ),
                            },
                        ]
                        followup_resp = await self._call_ollama(followup)
                        if followup_resp:
                            response_text = re.sub(pattern, '', response_text, flags=re.DOTALL).strip()
                            response_text = followup_resp
                    except Exception as e:
                        logger.warning(f"Follow-up LLM call failed: {e}")
            except json.JSONDecodeError as e:
                logger.warning(f"Invalid tool_call JSON: {e}")
            except Exception as e:
                logger.exception(f"Tool execution error: {e}")

        # شيل tool_call syntax من الرد النهائي
        clean = re.sub(pattern, '', response_text, flags=re.DOTALL).strip()
        clean = re.sub(r'<scratch_pad>.*?</scratch_pad>', '', clean, flags=re.DOTALL).strip()
        return clean or response_text, tool_calls_made

    async def _auto_extract(self, user_msg: str, asst_msg: str, session_id: str):
        """يستخرج ذكريات في الخلفية."""
        try:
            ids = await self.memory.auto_extract_from_conversation(
                user_msg, asst_msg, session_id, self.auxiliary
            )
            self._stats["memories_extracted"] += len(ids)
        except Exception as e:
            logger.debug(f"Auto-extract failed: {e}")

    def _mock_response(self, message: str) -> str:
        if any(w in message.lower() for w in ["مرحبا", "أهلا", "hello", "hi"]):
            return "أهلاً بيك! للأسف الـ LLM مش متاح دلوقتي. تأكد إن Ollama شغال."
        return (
            f"استلمت رسالتك: «{message[:100]}»\n\n"
            "للأسف الـ LLM مش متاح. تأكد إن Ollama شغال على :11434"
        )

    async def health_check(self) -> dict:
        core_services = {"engine": True, "session_db": self.session_manager._conn is not None}
        optional_services = {}

        # اكتشف الـ models المتاحة
        await self._detect_available_models()

        # Ollama (core)
        try:
            client = await self._get_ollama_client()
            r = await client.get(f"{self.config.ollama_url}/api/tags", timeout=2.0)
            core_services["ollama"] = r.status_code == 200
            if r.status_code == 200:
                models = r.json().get("models", [])
                self._available_models = {m["name"] for m in models}
                for name in list(self._available_models):
                    if ":" not in name:
                        self._available_models.add(f"{name}:latest")
        except Exception:
            core_services["ollama"] = False

        # Primary model available
        primary_model = self.config.primary_model or self.config.ollama_model
        optional_services["primary_model"] = primary_model in self._available_models
        optional_services["primary_model_name"] = primary_model

        # Fallback model available
        optional_services["fallback_model"] = (
            self.config.ollama_fallback_model in self._available_models
        )
        optional_services["fallback_model_name"] = self.config.ollama_fallback_model

        # Auxiliary (optional)
        if self.auxiliary:
            optional_services["auxiliary"] = await self.auxiliary.health_check()
        else:
            optional_services["auxiliary"] = False

        # Memory (core)
        core_services["memory"] = self.memory._conn is not None
        emb = self.memory.embedding_client._available
        optional_services["embeddings"] = emb is True or emb is None
        optional_services["embeddings_model"] = self.config.embedding_model
        optional_services["embeddings_model_available"] = (
            self.config.embedding_model in self._available_models
        )

        # engine_ready = على الأقل Ollama + memory + 1 model شغال
        self._engine_ready = (
            core_services.get("ollama", False)
            and core_services.get("memory", False)
            and (optional_services.get("primary_model") or optional_services.get("fallback_model"))
        )
        self._stats["engine_ready"] = self._engine_ready
        self._stats["engine_type"] = "integrated"
        self._stats["active_model"] = self._stats.get("active_model")

        services = {**core_services, **optional_services}
        if all(core_services.values()) and self._engine_ready:
            status = "healthy"
        elif any(core_services.values()):
            status = "degraded"
        else:
            status = "critical"

        return {
            "status": status,
            "services": services,
            "engine_ready": self._engine_ready,
            "engine_type": "integrated",
            "available_models": list(self._available_models),
        }

    def get_stats(self) -> dict:
        stats = dict(self._stats)
        stats["engine_ready"] = self._engine_ready
        stats["engine_type"] = "integrated"
        stats["available_models"] = list(self._available_models)
        return stats

    async def heal(self) -> dict:
        """إصلاح ذاتي — يعيد تشغيل الـ connections لو فشلت."""
        results = {"checked": [], "fixed": [], "errors": []}

        # 1. تحقق من Ollama connection
        try:
            client = await self._get_ollama_client()
            r = await client.get(f"{self.config.ollama_url}/api/tags", timeout=5.0)
            if r.status_code == 200:
                results["checked"].append("ollama: ok")
                # حدّث الـ available models
                models = r.json().get("models", [])
                self._available_models = {m["name"] for m in models}
                for name in list(self._available_models):
                    if ":" not in name:
                        self._available_models.add(f"{name}:latest")
            else:
                results["errors"].append(f"ollama: status {r.status_code}")
                # أعد إنشاء الـ client
                if self._ollama_client and not self._ollama_client.is_closed:
                    await self._ollama_client.aclose()
                self._ollama_client = None
                results["fixed"].append("ollama: client recreated")
        except Exception as e:
            results["errors"].append(f"ollama: {e}")
            if self._ollama_client and not self._ollama_client.is_closed:
                await self._ollama_client.aclose()
            self._ollama_client = None
            results["fixed"].append("ollama: client recreated")

        # 2. تحقق من memory
        try:
            if self.memory._conn is None:
                self.memory._init_db()
                results["fixed"].append("memory: reinitialized")
            else:
                results["checked"].append("memory: ok")
        except Exception as e:
            results["errors"].append(f"memory: {e}")

        # 3. تحقق من session_manager
        try:
            if self.session_manager._conn is None:
                self.session_manager._init_db()
                results["fixed"].append("session_db: reinitialized")
            else:
                results["checked"].append("session_db: ok")
        except Exception as e:
            results["errors"].append(f"session_db: {e}")

        # 4. تحقق من auxiliary
        if self.auxiliary:
            try:
                if await self.auxiliary.health_check():
                    results["checked"].append("auxiliary: ok")
                else:
                    # أعد التهيئة
                    if self.auxiliary._client and not self.auxiliary._client.is_closed:
                        await self.auxiliary._client.aclose()
                    self.auxiliary._client = None
                    self.auxiliary._available = None
                    results["fixed"].append("auxiliary: client recreated")
            except Exception as e:
                results["errors"].append(f"auxiliary: {e}")

        return results

    async def cleanup(self):
        if self._ollama_client and not self._ollama_client.is_closed:
            await self._ollama_client.aclose()
        if self.auxiliary:
            await self.auxiliary.cleanup()
        await self.tools.cleanup()
        self.memory.close()
        self.session_manager.close()


# ============================================================
# Singleton
# ============================================================

_engine: AdamEngine | None = None

def get_engine() -> AdamEngine:
    global _engine
    if _engine is None:
        _engine = AdamEngine()
    return _engine

async def cleanup_engine():
    global _engine
    if _engine:
        await _engine.cleanup()
        _engine = None
