"""
[PHASE3] Database layer for Adam Prism.
Supports SQLite (default, single-process) and PostgreSQL (production, multi-worker).

Uses SQLAlchemy 2.0 core (not ORM) for performance and simplicity.
Graceful fallback: if PostgreSQL is unavailable, uses SQLite.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger("adam_prism.storage")


def get_database_url() -> str:
    """Get the database URL from environment, with sensible default."""
    url = os.environ.get("ADAM_DATABASE_URL", "").strip()
    if url:
        return url
    # Default to SQLite in user data dir
    data_dir = os.environ.get(
        "ADAM_DATA_DIR",
        str(Path.home() / ".local" / "share" / "adam"),
    )
    Path(data_dir).mkdir(parents=True, exist_ok=True)
    return f"sqlite:///{data_dir}/adam.db"


def is_postgres(url: str) -> bool:
    return url.startswith(("postgresql://", "postgres://"))


_engine = None


def get_engine():
    """Lazy-init global SQLAlchemy engine."""
    global _engine
    if _engine is not None:
        return _engine

    from sqlalchemy import create_engine
    from sqlalchemy.engine import Engine

    url = get_database_url()
    kwargs: dict[str, Any] = {"pool_pre_ping": True, "future": True}

    if is_postgres(url):
        # PostgreSQL: connection pooling for multi-worker
        kwargs.update({
            "pool_size": int(os.environ.get("ADAM_DB_POOL_SIZE", "10")),
            "max_overflow": int(os.environ.get("ADAM_DB_MAX_OVERFLOW", "20")),
            "pool_timeout": 30,
            "pool_recycle": 3600,
        })
        logger.info(f"Using PostgreSQL: {url.split('@')[-1]}")
    else:
        # SQLite: only allow one connection at a time
        kwargs["connect_args"] = {"check_same_thread": False}
        logger.info(f"Using SQLite: {url}")

    _engine = create_engine(url, **kwargs)
    return _engine


@contextmanager
def get_connection() -> Iterator[Any]:
    """[PHASE3] Context manager for database connections."""
    engine = get_engine()
    conn = engine.connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """[PHASE3] Initialize database schema. Idempotent (CREATE IF NOT EXISTS)."""
    engine = get_engine()
    with engine.begin() as conn:
        from sqlalchemy import text

        if is_postgres(get_database_url()):
            # PostgreSQL DDL
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id VARCHAR(64) PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT 'New Conversation',
                    created_at TIMESTAMP DEFAULT NOW(),
                    updated_at TIMESTAMP DEFAULT NOW(),
                    user_id VARCHAR(64),
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id BIGSERIAL PRIMARY KEY,
                    session_id VARCHAR(64) NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
                    role VARCHAR(32) NOT NULL,
                    content TEXT NOT NULL,
                    mode VARCHAR(32),
                    metadata JSONB DEFAULT '{}'::jsonb,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session
                    ON chat_messages(session_id, created_at)
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id VARCHAR(64) PRIMARY KEY,
                    email VARCHAR(255) UNIQUE,
                    username VARCHAR(64) UNIQUE,
                    password_hash TEXT,
                    role VARCHAR(32) DEFAULT 'user',
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT NOW(),
                    last_login TIMESTAMP,
                    metadata JSONB DEFAULT '{}'::jsonb
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id BIGSERIAL PRIMARY KEY,
                    key_hash VARCHAR(128) UNIQUE NOT NULL,
                    user_id VARCHAR(64) REFERENCES users(id) ON DELETE CASCADE,
                    name VARCHAR(64),
                    scopes JSONB DEFAULT '[]'::jsonb,
                    created_at TIMESTAMP DEFAULT NOW(),
                    expires_at TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active BOOLEAN DEFAULT TRUE
                )
            """))
        else:
            # SQLite DDL
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_sessions (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL DEFAULT 'New Conversation',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    user_id TEXT,
                    metadata TEXT DEFAULT '{}'
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS chat_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    role TEXT NOT NULL,
                    content TEXT NOT NULL,
                    mode TEXT,
                    metadata TEXT DEFAULT '{}',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (session_id) REFERENCES chat_sessions(id) ON DELETE CASCADE
                )
            """))
            conn.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_chat_messages_session
                    ON chat_messages(session_id, created_at)
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT UNIQUE,
                    username TEXT UNIQUE,
                    password_hash TEXT,
                    role TEXT DEFAULT 'user',
                    is_active INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_login TIMESTAMP,
                    metadata TEXT DEFAULT '{}'
                )
            """))
            conn.execute(text("""
                CREATE TABLE IF NOT EXISTS api_keys (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    key_hash TEXT UNIQUE NOT NULL,
                    user_id TEXT,
                    name TEXT,
                    scopes TEXT DEFAULT '[]',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP,
                    last_used TIMESTAMP,
                    is_active INTEGER DEFAULT 1,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                )
            """))
    logger.info("Database schema initialized")
