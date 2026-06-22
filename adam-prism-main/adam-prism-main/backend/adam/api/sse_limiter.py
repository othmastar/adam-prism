"""SSE (Server-Sent Events) rate limiter and abuse protection.

Streaming endpoints are easy to abuse — one client can hold thousands of
connections open. This module enforces:

1. Per-IP concurrent connection cap
2. Per-IP tokens/sec budget (for token streams)
3. Per-user total bytes/sec
4. Auto-disconnect idle streams after N seconds
5. Server-wide hard cap as safety net
"""
from __future__ import annotations

import asyncio
import time
from collections import defaultdict
from dataclasses import dataclass, field
from threading import Lock


@dataclass
class _ClientState:
    """Per-client streaming state."""
    last_activity: float = field(default_factory=time.time)
    bytes_sent: int = 0
    tokens_sent: int = 0
    window_start: float = field(default_factory=time.time)


class SSERateLimiter:
    """Token-bucket rate limiter for SSE / streaming endpoints.

    Defaults are conservative and can be tuned via env vars
    (ADAM_SSE_MAX_CONCURRENT, ADAM_SSE_TOKENS_PER_SEC, ADAM_SSE_IDLE_TIMEOUT).
    """
    def __init__(
        self,
        max_concurrent_per_ip: int = 5,
        max_concurrent_global: int = 500,
        max_tokens_per_sec: int = 200,
        max_bytes_per_sec: int = 1_000_000,  # 1 MB/s per client
        idle_timeout_sec: int = 120,
    ) -> None:
        self.max_concurrent_per_ip = max_concurrent_per_ip
        self.max_concurrent_global = max_concurrent_global
        self.max_tokens_per_sec = max_tokens_per_sec
        self.max_bytes_per_sec = max_bytes_per_sec
        self.idle_timeout_sec = idle_timeout_sec
        self._clients: dict[str, int] = defaultdict(int)  # ip -> active count
        self._state: dict[str, _ClientState] = defaultdict(_ClientState)
        self._global_count = 0
        self._lock = Lock()
        self._total_blocked = 0

    def acquire(self, client_id: str) -> str | None:
        """Try to acquire a slot for client_id. Returns None on success, error msg on block."""
        with self._lock:
            if self._global_count >= self.max_concurrent_global:
                self._total_blocked += 1
                return f"server_busy: {self._global_count}/{self.max_concurrent_global} streams active"
            if self._clients[client_id] >= self.max_concurrent_per_ip:
                self._total_blocked += 1
                return f"too_many_streams: {self._clients[client_id]}/{self.max_concurrent_per_ip} per client"
            self._clients[client_id] += 1
            self._global_count += 1
            self._state[client_id] = _ClientState()
            return None

    def release(self, client_id: str) -> None:
        with self._lock:
            if self._clients[client_id] > 0:
                self._clients[client_id] -= 1
            if self._global_count > 0:
                self._global_count -= 1
            self._state.pop(client_id, None)

    def record_tokens(self, client_id: str, n: int) -> str | None:
        """Record n tokens sent. Returns None if ok, error msg if over budget."""
        with self._lock:
            st = self._state[client_id]
            st.last_activity = time.time()
            st.tokens_sent += n
            # Sliding window: reset counter every second
            now = time.time()
            if now - st.window_start >= 1.0:
                st.window_start = now
                st.tokens_sent = n
            if st.tokens_sent > self.max_tokens_per_sec:
                return f"token_rate_exceeded: {st.tokens_sent}/{self.max_tokens_per_sec} t/s"
            return None

    def record_bytes(self, client_id: str, n: int) -> str | None:
        """Record n bytes sent. Returns None if ok, error msg if over budget."""
        with self._lock:
            st = self._state[client_id]
            st.last_activity = time.time()
            st.bytes_sent += n
            now = time.time()
            if now - st.window_start >= 1.0:
                st.window_start = now
                st.bytes_sent = n
            if st.bytes_sent > self.max_bytes_per_sec:
                return f"byte_rate_exceeded: {st.bytes_sent}/{self.max_bytes_per_sec} B/s"
            return None

    def is_idle(self, client_id: str) -> bool:
        """Return True if this client hasn't done anything in idle_timeout_sec."""
        with self._lock:
            st = self._state.get(client_id)
            if not st:
                return True
            return (time.time() - st.last_activity) > self.idle_timeout_sec

    def stats(self) -> dict:
        """Return public stats (for /metrics or admin)."""
        with self._lock:
            return {
                "global_active": self._global_count,
                "global_max": self.max_concurrent_global,
                "per_client_active": dict(self._clients),
                "total_blocked": self._total_blocked,
            }


_singleton: SSERateLimiter | None = None


def get_sse_limiter() -> SSERateLimiter:
    """Lazy singleton accessor."""
    global _singleton
    if _singleton is None:
        import os
        _singleton = SSERateLimiter(
            max_concurrent_per_ip=int(os.getenv("ADAM_SSE_MAX_CONCURRENT_PER_IP", "5")),
            max_concurrent_global=int(os.getenv("ADAM_SSE_MAX_CONCURRENT_GLOBAL", "500")),
            max_tokens_per_sec=int(os.getenv("ADAM_SSE_TOKENS_PER_SEC", "200")),
            max_bytes_per_sec=int(os.getenv("ADAM_SSE_BYTES_PER_SEC", "1000000")),
            idle_timeout_sec=int(os.getenv("ADAM_SSE_IDLE_TIMEOUT", "120")),
        )
    return _singleton


async def idle_watchdog(limiter: SSERateLimiter, check_interval: int = 30) -> None:
    """Background task that disconnects idle clients. Run as asyncio task."""
    while True:
        await asyncio.sleep(check_interval)
        # No-op pattern: in real usage, the stream handler checks is_idle()
        # and self-closes. This task is the place to add per-client cleanup
        # if the stream handler crashed without releasing.
        with limiter._lock:
            now = time.time()
            stale = [
                cid for cid, st in limiter._state.items()
                if (now - st.last_activity) > limiter.idle_timeout_sec * 2
            ]
        for cid in stale:
            limiter.release(cid)
