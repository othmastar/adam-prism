"""
Adam Memory Store — Persistent SQLite Memory
=============================================
خفيف، SQLite، يدعم tags + priority + full-text search
مستوحى من Kimi Eternal Memory لكن بدون over-engineering
"""

import json
import sqlite3
import time
import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from pathlib import Path


MEMORY_DB = os.environ.get("ADAM_MEMORY_DB",
    "/mnt/Workspace/adam_v8_output/.adam_memory/adam_memory.db")


def _ensure_db():
    os.makedirs(os.path.dirname(MEMORY_DB), exist_ok=True)
    conn = sqlite3.connect(MEMORY_DB)
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


def store(content: str, tags: str = "", priority: int = 3, source: str = "adam") -> int:
    _ensure_db()
    now = time.time()
    conn = sqlite3.connect(MEMORY_DB)
    cur = conn.execute(
        "INSERT INTO memories (content, tags, priority, source, created_at, accessed_at) VALUES (?, ?, ?, ?, ?, ?)",
        (content.strip(), tags.strip(), min(max(priority, 1), 5), source, now, now)
    )
    mem_id = cur.lastrowid
    conn.commit()
    conn.close()
    return mem_id


def search(query: str, limit: int = 10) -> List[Dict[str, Any]]:
    _ensure_db()
    conn = sqlite3.connect(MEMORY_DB)
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


def recall(memory_id: int) -> Optional[Dict[str, Any]]:
    _ensure_db()
    conn = sqlite3.connect(MEMORY_DB)
    conn.row_factory = sqlite3.Row
    row = conn.execute("SELECT * FROM memories WHERE id = ?", (memory_id,)).fetchone()
    if row:
        conn.execute("UPDATE memories SET access_count = access_count + 1, accessed_at = ? WHERE id = ?",
                     (time.time(), memory_id))
        conn.commit()
    conn.close()
    return dict(row) if row else None


def reflect(days: int = 1) -> Dict[str, Any]:
    _ensure_db()
    cutoff = time.time() - (days * 86400)
    conn = sqlite3.connect(MEMORY_DB)
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


def stats() -> Dict[str, Any]:
    _ensure_db()
    conn = sqlite3.connect(MEMORY_DB)
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
        "db_path": MEMORY_DB,
    }
