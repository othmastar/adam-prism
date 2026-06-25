"""
Adam Prism — Session Search (FTS5)
====================================
الطبقة الثانية من الذاكرة: بحث نصي كامل في كل الجلسات.
مستوحى من Hermes Agent — "Session Search" layer.

الميزات:
- SQLite + FTS5 بحث نصي كامل فوري (~20ms)
- تخزين كل الجلسات (CLI + messaging + API)
- ثلاثة أنماط بحث: discovery, scroll, browse
- Session lineage: تتبع علاقات الجلسات (parent/child)
- بدون تكلفة tokens — بحث DB بحت
"""

import json
import logging
import os
import sqlite3
import time
from pathlib import Path

logger = logging.getLogger("adam_prism.memory.session_search")

class SessionSearch:
    """
    بحث نصي كامل في كل الجلسات السابقة.

    مثل Hermes — الذاكرة الحلقية (Episodic Memory):
    "هل تحدثنا عن X الأسبوع الماضي؟" → بحث فوري بدون LLM.
    """

    DEFAULT_DB_PATH = os.environ.get(
        "ADAM_SESSION_DB",
        os.path.expanduser("~/.adam/sessions/state.db")
    )

    def __init__(self, config: dict = None):
        cfg = config or {}
        self.db_path = Path(cfg.get("db_path", self.DEFAULT_DB_PATH))
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.db_path))
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._ensure_tables()

    def _ensure_tables(self):
        """إنشاء الجداول و FTS5 index"""
        # جدول الجلسات
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS sessions (
                session_id TEXT PRIMARY KEY,
                platform TEXT DEFAULT 'cli',
                model TEXT DEFAULT '',
                started_at REAL NOT NULL,
                ended_at REAL,
                message_count INTEGER DEFAULT 0,
                parent_session_id TEXT,
                summary TEXT DEFAULT '',
                tags TEXT DEFAULT ''
            )
        """)

        # جدول الرسائل مع FTS5
        self._conn.execute("""
            CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                session_id,
                role,
                content,
                timestamp,
                tokenize='unicode61'
            )
        """)

        # فهرس للرسائل العادية
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                session_id TEXT NOT NULL,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                timestamp REAL NOT NULL,
                metadata TEXT DEFAULT '{}',
                FOREIGN KEY (session_id) REFERENCES sessions(session_id)
            )
        """)
        self._conn.execute(
            "CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, timestamp)"
        )
        self._conn.commit()

    def close(self):
        """إغلاق الاتصال"""
        if self._conn:
            self._conn.close()
            self._conn = None

    # ─── إدارة الجلسات ───────────────────────────────

    def create_session(self, session_id: str, platform: str = "cli",
                       model: str = "", parent_id: str = None) -> str:
        """إنشاء جلسة جديدة"""
        self._conn.execute(
            "INSERT OR REPLACE INTO sessions (session_id, platform, model, started_at, parent_session_id) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, platform, model, time.time(), parent_id)
        )
        self._conn.commit()
        return session_id

    def end_session(self, session_id: str, summary: str = "", tags: str = ""):
        """إنهاء جلسة"""
        self._conn.execute(
            "UPDATE sessions SET ended_at = ?, summary = ?, tags = ? WHERE session_id = ?",
            (time.time(), summary, tags, session_id)
        )
        self._conn.commit()

    def add_message(self, session_id: str, role: str, content: str,
                    metadata: dict = None):
        """إضافة رسالة لجلسة"""
        now = time.time()

        # إدراج في جدول الرسائل
        self._conn.execute(
            "INSERT INTO messages (session_id, role, content, timestamp, metadata) "
            "VALUES (?, ?, ?, ?, ?)",
            (session_id, role, content, now, json.dumps(metadata or {}, ensure_ascii=False))
        )

        # إدراج في FTS5
        self._conn.execute(
            "INSERT INTO messages_fts (session_id, role, content, timestamp) "
            "VALUES (?, ?, ?, ?)",
            (session_id, role, content, str(now))
        )

        # تحديث عداد الرسائل
        self._conn.execute(
            "UPDATE sessions SET message_count = message_count + 1 WHERE session_id = ?",
            (session_id,)
        )
        self._conn.commit()

    # ─── البحث ────────────────────────────────────────

    def search(self, query: str, limit: int = 10) -> list[dict]:
        """
        بحث نصي كامل عبر كل الجلسات (Discovery mode).
        ~20ms مع FTS5.
        """
        if not query.strip():
            return []

        try:
            # FTS5 search مع ترتيب بالصلة
            results = self._conn.execute("""
                SELECT
                    m.session_id,
                    m.role,
                    m.content,
                    m.timestamp,
                    s.platform,
                    s.model,
                    s.started_at,
                    snippet(messages_fts, 2, '>>>', '<<<', '...', 30) as highlight
                FROM messages_fts mfs
                JOIN messages m ON m.content = mfs.content AND m.session_id = mfs.session_id
                JOIN sessions s ON s.session_id = m.session_id
                WHERE messages_fts MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit)).fetchall()

            return [
                {
                    "session_id": r[0],
                    "role": r[1],
                    "content": r[2][:500],
                    "timestamp": r[3],
                    "platform": r[4],
                    "model": r[5],
                    "started_at": r[6],
                    "highlight": r[7],
                }
                for r in results
            ]
        except Exception as e:
            logger.warning(f"خطأ في بحث الجلسات: {e}")
            # Fallback: بحث LIKE
            return self._fallback_search(query, limit)

    def _fallback_search(self, query: str, limit: int = 10) -> list[dict]:
        """بحث بديل (LIKE) لو FTS5 فشل"""
        keywords = query.strip().split()[:5]
        if not keywords:
            return []

        conditions = " AND ".join(["m.content LIKE ?" for _ in keywords])
        params = [f"%{kw}%" for kw in keywords] + [limit]

        results = self._conn.execute(f"""
            SELECT m.session_id, m.role, m.content, m.timestamp, s.platform, s.model
            FROM messages m
            JOIN sessions s ON s.session_id = m.session_id
            WHERE {conditions}
            ORDER BY m.timestamp DESC
            LIMIT ?
        """, params).fetchall()

        return [
            {
                "session_id": r[0], "role": r[1], "content": r[2][:500],
                "timestamp": r[3], "platform": r[4], "model": r[5],
            }
            for r in results
        ]

    def scroll(self, session_id: str, direction: str = "after",
               reference_timestamp: float = None, limit: int = 20) -> list[dict]:
        """
        التنقل داخل جلسة محددة (Scroll mode).
        direction: "after" | "before"
        """
        if reference_timestamp is None:
            # أول رسالة في الجلسة
            ref = 0 if direction == "after" else time.time()
        else:
            ref = reference_timestamp

        if direction == "after":
            rows = self._conn.execute(
                "SELECT id, role, content, timestamp, metadata FROM messages "
                "WHERE session_id = ? AND timestamp > ? ORDER BY timestamp ASC LIMIT ?",
                (session_id, ref, limit)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT id, role, content, timestamp, metadata FROM messages "
                "WHERE session_id = ? AND timestamp < ? ORDER BY timestamp DESC LIMIT ?",
                (session_id, ref, limit)
            ).fetchall()

        return [
            {
                "id": r[0], "role": r[1], "content": r[2],
                "timestamp": r[3], "metadata": json.loads(r[4]) if r[4] else {},
            }
            for r in rows
        ]

    def browse(self, limit: int = 20, platform: str = None) -> list[dict]:
        """
        استعراض الجلسات السابقة (Browse mode).
        """
        if platform:
            rows = self._conn.execute(
                "SELECT session_id, platform, model, started_at, ended_at, "
                "message_count, summary, tags FROM sessions "
                "WHERE platform = ? ORDER BY started_at DESC LIMIT ?",
                (platform, limit)
            ).fetchall()
        else:
            rows = self._conn.execute(
                "SELECT session_id, platform, model, started_at, ended_at, "
                "message_count, summary, tags FROM sessions "
                "ORDER BY started_at DESC LIMIT ?",
                (limit,)
            ).fetchall()

        return [
            {
                "session_id": r[0], "platform": r[1], "model": r[2],
                "started_at": r[3], "ended_at": r[4], "message_count": r[5],
                "summary": r[6], "tags": r[7],
            }
            for r in rows
        ]

    # ─── الإحصائيات ──────────────────────────────────

    def get_stats(self) -> dict:
        """إحصائيات الجلسات"""
        total_sessions = self._conn.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
        total_messages = self._conn.execute("SELECT COUNT(*) FROM messages").fetchone()[0]
        platforms = self._conn.execute(
            "SELECT platform, COUNT(*) FROM sessions GROUP BY platform"
        ).fetchall()

        return {
            "total_sessions": total_sessions,
            "total_messages": total_messages,
            "by_platform": {p[0]: p[1] for p in platforms},
            "db_path": str(self.db_path),
        }

    def get_session_summary(self, session_id: str) -> dict | None:
        """ملخص جلسة محددة"""
        row = self._conn.execute(
            "SELECT session_id, platform, model, started_at, ended_at, "
            "message_count, summary, tags, parent_session_id FROM sessions "
            "WHERE session_id = ?",
            (session_id,)
        ).fetchone()

        if not row:
            return None

        return {
            "session_id": row[0], "platform": row[1], "model": row[2],
            "started_at": row[3], "ended_at": row[4], "message_count": row[5],
            "summary": row[6], "tags": row[7], "parent_session_id": row[8],
        }
