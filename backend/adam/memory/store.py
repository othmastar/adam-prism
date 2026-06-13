"""
Adam Memory Store — Persistent SQLite Memory — HARDENED v3
============================================================
خفيف، SQLite، يدعم tags + priority + full-text search
مستوحى من Kimi Eternal Memory لكن بدون over-engineering

[FIX v2 — BUG FIX]
- Wrapped module-level functions in a MemoryStore class for better testability
- Module-level functions still available as backward-compatible aliases
- Class-based approach allows dependency injection and mocking in tests

[FIX v3 — PERFORMANCE & RELIABILITY]
- Single persistent SQLite connection with WAL mode in __init__
- Reuse connection across all methods instead of opening new ones each time
- Added close() method for proper cleanup
"""

import os
import sqlite3
import time
from typing import Any

# Default database path (module-level for backward compatibility)
MEMORY_DB = os.environ.get("ADAM_MEMORY_DB",
    os.path.join(os.getcwd(), ".adam_memory", "adam_memory.db"))


class MemoryStore:
    """
    مخزن الذاكرة المستمر — SQLite

    يمكن إنشاء عدة نسخ بمسارات مختلفة (للاختبار مثلاً)
    أو استخدام النسخة الافتراضية عبر الدوال على مستوى الموديول

    Usage:
        store = MemoryStore()  # default path
        store = MemoryStore(db_path="/tmp/test_memory.db")  # custom path

        mem_id = store.store("معلومة مهمة", tags="مهم", priority=5)
        results = store.search("معلومة")
    """

    def __init__(self, db_path: str | None = None):
        self.db_path = db_path or MEMORY_DB
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self._conn = sqlite3.connect(self.db_path)
        self._conn.execute("PRAGMA journal_mode=WAL")
        self._conn.execute("PRAGMA foreign_keys=ON")
        self._ensure_db()

    def close(self):
        """Close the persistent database connection"""
        if self._conn:
            self._conn.close()
            self._conn = None

    def _ensure_db(self):
        """إنشاء الجدول إن لم يكن موجوداً"""
        if self._conn is None:
            self._conn = sqlite3.connect(self.db_path)
            self._conn.execute("PRAGMA journal_mode=WAL")
            self._conn.execute("PRAGMA foreign_keys=ON")
        self._conn.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                tags TEXT DEFAULT '',
                priority INTEGER DEFAULT 3,
                source TEXT DEFAULT 'adam',
                created_at REAL NOT NULL,
                accessed_at REAL NOT NULL,
                access_count INTEGER DEFAULT 0
            )
        """)
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories(tags)")
        self._conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_priority ON memories(priority)")
        self._conn.commit()

    def store(self, content: str, tags: str = "", priority: int = 3, source: str = "adam") -> int:
        """تخزين ذكرى جديد"""
        now = time.time()
        cur = self._conn.execute(
            "INSERT INTO memories (content, tags, priority, source, created_at, accessed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (content.strip(), tags.strip(), min(max(priority, 1), 5), source, now, now)
        )
        mem_id = cur.lastrowid
        self._conn.commit()
        return mem_id

    def search(self, query: str, limit: int = 10) -> list[dict[str, Any]]:
        """البحث في الذاكرة"""
        self._conn.row_factory = sqlite3.Row

        keywords = query.strip().split()
        if not keywords:
            return []

        conditions = []
        params_list = []
        for kw in keywords:
            conditions.append("(content LIKE ? OR tags LIKE ?)")
            params_list.extend([f"%{kw}%", f"%{kw}%"])

        sql = f"SELECT * FROM memories WHERE {' AND '.join(conditions)} ORDER BY priority DESC, access_count DESC, accessed_at DESC LIMIT ?"
        params_list.append(limit)

        rows = self._conn.execute(sql, params_list).fetchall()
        results = [dict(r) for r in rows]

        # Update access stats
        ids = [r["id"] for r in rows]
        if ids:
            self._conn.execute(
                f"UPDATE memories SET access_count = access_count + 1, accessed_at = ? WHERE id IN ({','.join('?'*len(ids))})",
                [time.time(), *ids]
            )
            self._conn.commit()

        self._conn.row_factory = None
        return results

    def recall(self, memory_id: int) -> dict[str, Any] | None:
        """استرجاع ذكرى بالمعرف"""
        self._conn.row_factory = sqlite3.Row
        row = self._conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if row:
            self._conn.execute("UPDATE memories SET access_count = access_count + 1, accessed_at = ? WHERE id = ?",
                         (time.time(), memory_id))
            self._conn.commit()
        self._conn.row_factory = None
        return dict(row) if row else None

    def reflect(self, days: int = 1) -> dict[str, Any]:
        """تأمل في الذكريات"""
        cutoff = time.time() - (days * 86400)
        self._conn.row_factory = sqlite3.Row

        recent = self._conn.execute(
            "SELECT * FROM memories WHERE created_at > ? ORDER BY priority DESC, created_at DESC",
            (cutoff,)
        ).fetchall()

        top = self._conn.execute(
            "SELECT * FROM memories ORDER BY access_count DESC, priority DESC LIMIT 10"
        ).fetchall()

        self._conn.row_factory = None

        return {
            "recent_count": len(recent),
            "recent": [dict(r) for r in recent[:5]],
            "most_accessed": [dict(r) for r in top],
            "period_days": days,
        }

    def stats(self) -> dict[str, Any]:
        """إحصائيات الذاكرة"""
        total = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        by_priority = {}
        for row in self._conn.execute("SELECT priority, COUNT(*) as cnt FROM memories GROUP BY priority ORDER BY priority DESC"):
            by_priority[f"p{row[0]}"] = row[1]
        oldest = self._conn.execute("SELECT MIN(created_at) FROM memories").fetchone()[0]
        newest = self._conn.execute("SELECT MAX(created_at) FROM memories").fetchone()[0]
        return {
            "total": total,
            "by_priority": by_priority,
            "oldest": oldest,
            "newest": newest,
            "db_path": self.db_path,
        }

    def delete(self, memory_id: int) -> bool:
        """حذف ذكرى بالمعرف"""
        cur = self._conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        self._conn.commit()
        return cur.rowcount > 0

    def clear(self) -> int:
        """حذف كل الذكريات — يرجع عدد المحذوفات"""
        count = self._conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        self._conn.execute("DELETE FROM memories")
        self._conn.commit()
        return count


# ═══════════════════════════════════════════════════════
# Module-level singleton for backward compatibility
# الدوال على مستوى الموديول — للتوافق مع الكود القديم
# ═══════════════════════════════════════════════════════

_default_store = MemoryStore()


def _ensure_db():
    """إنشاء الجدول إن لم يكن موجوداً (backward compat)"""
    _default_store._ensure_db()


def store(content: str, tags: str = "", priority: int = 3, source: str = "adam") -> int:
    """تخزين ذكرى جديد (backward compat)"""
    return _default_store.store(content, tags, priority, source)


def search(query: str, limit: int = 10) -> list[dict[str, Any]]:
    """البحث في الذاكرة (backward compat)"""
    return _default_store.search(query, limit)


def recall(memory_id: int) -> dict[str, Any] | None:
    """استرجاع ذكرى بالمعرف (backward compat)"""
    return _default_store.recall(memory_id)


def reflect(days: int = 1) -> dict[str, Any]:
    """تأمل في الذكريات (backward compat)"""
    return _default_store.reflect(days)


def stats() -> dict[str, Any]:
    """إحصائيات الذاكرة (backward compat)"""
    return _default_store.stats()
