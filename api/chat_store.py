"""
Adam Prism - Chat History Store
================================
تخزين واسترجاع تاريخ المحادثات باستخدام SQLite.
"""

import json
import sqlite3
import logging
import time
import uuid
from pathlib import Path
from typing import Optional, List, Dict, Any

logger = logging.getLogger("adam_prism.chat_store")

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "chat_history.db"


class ChatStore:
    """
    تخزين واسترجاع تاريخ المحادثات.
    
    الجدوال:
    - sessions: جلسات المحادثة (id, title, created_at, updated_at)
    - messages: الرسائل (id, session_id, role, content, mode, metadata, timestamp)
    """

    def __init__(self, db_path: str | Path = DB_PATH):
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_db()

    def _get_conn(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_db(self):
        with self._get_conn() as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT 'New Conversation',
                    created_at REAL NOT NULL,
                    updated_at REAL NOT NULL
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id TEXT PRIMARY KEY,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL CHECK(role IN ('user', 'assistant', 'system')),
                    content TEXT NOT NULL DEFAULT '',
                    mode TEXT,
                    metadata TEXT DEFAULT '{}',
                    timestamp REAL NOT NULL,
                    FOREIGN KEY (session_id) REFERENCES sessions(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_session
                    ON messages(session_id, timestamp);
                CREATE INDEX IF NOT EXISTS idx_sessions_updated
                    ON sessions(updated_at DESC);
                CREATE INDEX IF NOT EXISTS idx_messages_timestamp
                    ON messages(timestamp DESC);
            """)

            # Full-Text Search table for message content
            conn.executescript("""
                CREATE VIRTUAL TABLE IF NOT EXISTS messages_fts USING fts5(
                    content, session_id, role,
                    tokenize='unicode61'
                );
            """)
        logger.info(f"✅ Chat store initialized at {self.db_path}")

    # ── Sessions ──────────────────────────────────────────

    def list_sessions(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """قائمة الجلسات مرتبة حسب آخر تحديث"""
        with self._get_conn() as conn:
            rows = conn.execute(
                "SELECT id, title, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ? OFFSET ?",
                (limit, offset)
            ).fetchall()
            return [dict(r) for r in rows]

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """جلب جلسة معينة"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT id, title, created_at, updated_at FROM sessions WHERE id = ?",
                (session_id,)
            ).fetchone()
            return dict(row) if row else None

    def create_session(self, title: str = "New Conversation") -> Dict[str, Any]:
        """إنشاء جلسة جديدة"""
        session_id = str(uuid.uuid4())
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                "INSERT INTO sessions (id, title, created_at, updated_at) VALUES (?, ?, ?, ?)",
                (session_id, title, now, now)
            )
        return {"id": session_id, "title": title, "created_at": now, "updated_at": now}

    def update_session(self, session_id: str, title: str) -> bool:
        """تحديث عنوان الجلسة"""
        with self._get_conn() as conn:
            cur = conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, time.time(), session_id)
            )
            return cur.rowcount > 0

    def delete_session(self, session_id: str) -> bool:
        """حذف جلسة وكل رسائلها"""
        with self._get_conn() as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            cur = conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            return cur.rowcount > 0

    def touch_session(self, session_id: str):
        """تحديث time stamp فقط"""
        with self._get_conn() as conn:
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (time.time(), session_id)
            )

    # ── Messages ──────────────────────────────────────────

    def list_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """جلب كل رسائل جلسة مرتبة حسب timestamp"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT id, session_id, role, content, mode, metadata, timestamp
                   FROM messages WHERE session_id = ?
                   ORDER BY timestamp ASC""",
                (session_id,)
            ).fetchall()
            result = []
            for r in rows:
                msg = dict(r)
                try:
                    msg["metadata"] = json.loads(msg["metadata"])
                except (json.JSONDecodeError, TypeError):
                    msg["metadata"] = {}
                result.append(msg)
            return result

    def add_message(
        self,
        session_id: str,
        role: str,
        content: str,
        mode: Optional[str] = None,
        metadata: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        """إضافة رسالة إلى جلسة"""
        msg_id = str(uuid.uuid4())
        now = time.time()
        with self._get_conn() as conn:
            conn.execute(
                """INSERT INTO messages (id, session_id, role, content, mode, metadata, timestamp)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (msg_id, session_id, role, content, mode,
                 json.dumps(metadata or {}, ensure_ascii=False), now)
            )
            conn.execute(
                "INSERT OR IGNORE INTO messages_fts (rowid, content, session_id, role) VALUES (?, ?, ?, ?)",
                (msg_id, content, session_id, role)
            )
            conn.execute(
                "UPDATE sessions SET updated_at = ? WHERE id = ?",
                (now, session_id)
            )
        return {
            "id": msg_id,
            "session_id": session_id,
            "role": role,
            "content": content,
            "mode": mode,
            "metadata": metadata or {},
            "timestamp": now,
        }

    def search_messages(self, query: str, limit: int = 20) -> List[Dict[str, Any]]:
        """البحث في محتوى الرسائل باستخدام FTS"""
        with self._get_conn() as conn:
            rows = conn.execute(
                """SELECT m.id, m.session_id, m.role, m.content, m.mode, m.metadata, m.timestamp
                   FROM messages_fts f
                   JOIN messages m ON m.id = f.rowid
                   WHERE messages_fts MATCH ?
                   ORDER BY rank
                   LIMIT ?""",
                (query, limit)
            ).fetchall()
            result = []
            for r in rows:
                msg = dict(r)
                try:
                    msg["metadata"] = json.loads(msg["metadata"])
                except (json.JSONDecodeError, TypeError):
                    msg["metadata"] = {}
                result.append(msg)
            return result

    def get_message_count(self, session_id: str) -> int:
        """عدد الرسائل في جلسة"""
        with self._get_conn() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM messages WHERE session_id = ?",
                (session_id,)
            ).fetchone()
            return row["cnt"] if row else 0
