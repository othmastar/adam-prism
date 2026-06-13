"""
Adam Memory Store — Persistent SQLite Memory — HARDENED v2
============================================================
خفيف، SQLite، يدعم tags + priority + full-text search
مستوحى من Kimi Eternal Memory لكن بدون over-engineering

[FIX v2 — BUG FIX]
- Wrapped module-level functions in a MemoryStore class for better testability
- Module-level functions still available as backward-compatible aliases
- Class-based approach allows dependency injection and mocking in tests
"""

import json
import sqlite3
import time
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


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
    
    def __init__(self, db_path: str = None):
        self.db_path = db_path or MEMORY_DB
        self._ensure_db()
    
    def _ensure_db(self):
        """إنشاء الجدول إن لم يكن موجوداً"""
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        conn = sqlite3.connect(self.db_path)
        conn.execute("""
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
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_tags ON memories(tags)")
        conn.execute("CREATE INDEX IF NOT EXISTS idx_memories_priority ON memories(priority)")
        conn.commit()
        conn.close()
    
    def store(self, content: str, tags: str = "", priority: int = 3, source: str = "adam") -> int:
        """تخزين ذكرى جديد"""
        self._ensure_db()
        now = time.time()
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute(
            "INSERT INTO memories (content, tags, priority, source, created_at, accessed_at) VALUES (?, ?, ?, ?, ?, ?)",
            (content.strip(), tags.strip(), min(max(priority, 1), 5), source, now, now)
        )
        mem_id = cur.lastrowid
        conn.commit()
        conn.close()
        return mem_id
    
    def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """البحث في الذاكرة"""
        self._ensure_db()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        keywords = query.strip().split()
        if not keywords:
            conn.close()
            return []

        conditions = []
        params_list = []
        for kw in keywords:
            conditions.append("(content LIKE ? OR tags LIKE ?)")
            params_list.extend([f"%{kw}%", f"%{kw}%"])

        sql = f"SELECT * FROM memories WHERE {' AND '.join(conditions)} ORDER BY priority DESC, access_count DESC, accessed_at DESC LIMIT ?"
        params_list.append(limit)

        rows = conn.execute(sql, params_list).fetchall()
        results = [dict(r) for r in rows]

        # Update access stats
        ids = [r["id"] for r in rows]
        if ids:
            conn.execute(
                f"UPDATE memories SET access_count = access_count + 1, accessed_at = ? WHERE id IN ({','.join('?'*len(ids))})",
                [time.time()] + ids
            )
            conn.commit()

        conn.close()
        return results
    
    def recall(self, memory_id: int) -> Optional[Dict[str, Any]]:
        """استرجاع ذكرى بالمعرف"""
        self._ensure_db()
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
        if row:
            conn.execute("UPDATE memories SET access_count = access_count + 1, accessed_at = ? WHERE id = ?",
                         (time.time(), memory_id))
            conn.commit()
        conn.close()
        return dict(row) if row else None
    
    def reflect(self, days: int = 1) -> Dict[str, Any]:
        """تأمل في الذكريات"""
        self._ensure_db()
        cutoff = time.time() - (days * 86400)
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row

        recent = conn.execute(
            "SELECT * FROM memories WHERE created_at > ? ORDER BY priority DESC, created_at DESC",
            (cutoff,)
        ).fetchall()

        top = conn.execute(
            "SELECT * FROM memories ORDER BY access_count DESC, priority DESC LIMIT 10"
        ).fetchall()

        conn.close()

        return {
            "recent_count": len(recent),
            "recent": [dict(r) for r in recent[:5]],
            "most_accessed": [dict(r) for r in top],
            "period_days": days,
        }
    
    def stats(self) -> Dict[str, Any]:
        """إحصائيات الذاكرة"""
        self._ensure_db()
        conn = sqlite3.connect(self.db_path)
        total = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        by_priority = {}
        for row in conn.execute("SELECT priority, COUNT(*) as cnt FROM memories GROUP BY priority ORDER BY priority DESC"):
            by_priority[f"p{row[0]}"] = row[1]
        oldest = conn.execute("SELECT MIN(created_at) FROM memories").fetchone()[0]
        newest = conn.execute("SELECT MAX(created_at) FROM memories").fetchone()[0]
        conn.close()
        return {
            "total": total,
            "by_priority": by_priority,
            "oldest": oldest,
            "newest": newest,
            "db_path": self.db_path,
        }
    
    def delete(self, memory_id: int) -> bool:
        """حذف ذكرى بالمعرف"""
        self._ensure_db()
        conn = sqlite3.connect(self.db_path)
        cur = conn.execute("DELETE FROM memories WHERE id = ?", (memory_id,))
        conn.commit()
        deleted = cur.rowcount > 0
        conn.close()
        return deleted
    
    def clear(self) -> int:
        """حذف كل الذكريات — يرجع عدد المحذوفات"""
        self._ensure_db()
        conn = sqlite3.connect(self.db_path)
        count = conn.execute("SELECT COUNT(*) FROM memories").fetchone()[0]
        conn.execute("DELETE FROM memories")
        conn.commit()
        conn.close()
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


def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    """البحث في الذاكرة (backward compat)"""
    return _default_store.search(query, limit)


def recall(memory_id: int) -> Optional[Dict[str, Any]]:
    """استرجاع ذكرى بالمعرف (backward compat)"""
    return _default_store.recall(memory_id)


def reflect(days: int = 1) -> Dict[str, Any]:
    """تأمل في الذكريات (backward compat)"""
    return _default_store.reflect(days)


def stats() -> Dict[str, Any]:
    """إحصائيات الذاكرة (backward compat)"""
    return _default_store.stats()
