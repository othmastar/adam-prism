"""
[PHASE3] Adam Prism Python SDK — production-grade client
Adds retry logic, connection pooling, rate limiting, async streaming.
"""
from __future__ import annotations

import asyncio
import json
import os
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, Iterator, List, Optional, Union

import httpx

from .errors import (
    APIError,
    ConnectionError,
    NotFoundError,
    RateLimitError,
    ServiceUnavailableError,
    TimeoutError,
)


# Default configuration constants
DEFAULT_TIMEOUT = 30.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_RETRY_BACKOFF = 0.5
DEFAULT_POOL_CONNECTIONS = 10
DEFAULT_POOL_MAXSIZE = 20
DEFAULT_RATE_LIMIT_PER_SEC = 50


class _TokenBucket:
    """[PHASE3] Simple token bucket for client-side rate limiting"""

    def __init__(self, rate: float = DEFAULT_RATE_LIMIT_PER_SEC):
        self.rate = rate
        self.tokens = rate
        self.last_update = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self, tokens: int = 1) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_update
            self.tokens = min(self.rate, self.tokens + elapsed * self.rate)
            self.last_update = now
            if self.tokens < tokens:
                wait = (tokens - self.tokens) / self.rate
                await asyncio.sleep(wait)
                self.tokens = 0
            else:
                self.tokens -= tokens


class AdamPrismClient:
    """[PHASE3] Production-grade Python client for the Adam Prism API.
    Features: sync+async, retry with backoff, connection pooling, rate limiting,
    true streaming for chat.
    """

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = DEFAULT_TIMEOUT,
        *,
        api_key: Optional[str] = None,
        max_retries: int = DEFAULT_MAX_RETRIES,
        retry_backoff: float = DEFAULT_RETRY_BACKOFF,
        pool_connections: int = DEFAULT_POOL_CONNECTIONS,
        pool_maxsize: int = DEFAULT_POOL_MAXSIZE,
        rate_limit_per_sec: Optional[float] = DEFAULT_RATE_LIMIT_PER_SEC,
    ):
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._max_retries = max_retries
        self._retry_backoff = retry_backoff
        self._headers: Dict[str, str] = {
            "Content-Type": "application/json",
            "User-Agent": "adam-prism-client/1.0",
        }
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

        # [PHASE3] Connection pooling - one client per type, reused across calls
        limits = httpx.Limits(
            max_keepalive_connections=pool_connections,
            max_connections=pool_maxsize,
            keepalive_expiry=30.0,
        )
        self._sync_client: Optional[httpx.Client] = httpx.Client(
            base_url=self.base_url,
            headers=self._headers,
            timeout=timeout,
            limits=limits,
            follow_redirects=True,
        )
        self._async_client: Optional[httpx.AsyncClient] = None
        self._async_limits = limits

        # [PHASE3] Client-side rate limiting
        self._rate_limit = rate_limit_per_sec
        self._token_bucket = _TokenBucket(rate=rate_limit_per_sec) if rate_limit_per_sec else None

    # ── Lifecycle ───────────────────────────────────────────────

    def close(self):
        if self._sync_client and not self._sync_client.is_closed:
            self._sync_client.close()
        if self._async_client and not self._async_client.is_closed:
            # Async close needs to be called from async context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    loop.create_task(self._async_client.aclose())
                else:
                    loop.run_until_complete(self._async_client.aclose())
            except Exception:
                pass

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        await self.aclose()

    async def aclose(self):
        if self._async_client and not self._async_client.is_closed:
            await self._async_client.aclose()

    def _get_async(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(
                base_url=self.base_url,
                headers=self._headers,
                timeout=self._timeout,
                limits=self._async_limits,
                follow_redirects=True,
            )
        return self._async_client

    # ── Retry / Error handling ─────────────────────────────────

    def _raise_on_error(self, resp: httpx.Response) -> None:
        if resp.status_code < 400:
            return
        try:
            body = resp.json()
        except Exception:
            body = {"detail": resp.text}
        detail = body.get("detail", "") if isinstance(body, dict) else str(body)
        if resp.status_code == 404:
            raise NotFoundError(detail, body)
        elif resp.status_code == 429:
            raise RateLimitError(detail, body)
        elif resp.status_code == 503:
            raise ServiceUnavailableError(detail, body)
        else:
            raise APIError(resp.status_code, detail, body)

    def _should_retry(self, resp: httpx.Response) -> bool:
        # Retry on 5xx and 429
        return resp.status_code >= 500 or resp.status_code == 429

    def _request_with_retry(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = self._sync_client.request(method, path, **kwargs)
                if self._should_retry(resp) and attempt < self._max_retries:
                    wait = self._retry_backoff * (2 ** attempt)
                    time.sleep(wait)
                    continue
                return resp
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exc = e
                if attempt < self._max_retries:
                    time.sleep(self._retry_backoff * (2 ** attempt))
                    continue
                raise ConnectionError(str(e)) from e
        if last_exc:
            raise ConnectionError(str(last_exc))
        raise APIError(0, "Max retries exceeded", {})

    async def _arequest_with_retry(
        self, method: str, path: str, **kwargs
    ) -> httpx.Response:
        last_exc: Optional[Exception] = None
        for attempt in range(self._max_retries + 1):
            # [PHASE3] Apply client-side rate limiting
            if self._token_bucket:
                await self._token_bucket.acquire()
            try:
                resp = await self._get_async().request(method, path, **kwargs)
                if self._should_retry(resp) and attempt < self._max_retries:
                    wait = self._retry_backoff * (2 ** attempt)
                    await asyncio.sleep(wait)
                    continue
                return resp
            except (httpx.ConnectError, httpx.TimeoutException) as e:
                last_exc = e
                if attempt < self._max_retries:
                    await asyncio.sleep(self._retry_backoff * (2 ** attempt))
                    continue
                raise ConnectionError(str(e)) from e
        if last_exc:
            raise ConnectionError(str(last_exc))
        raise APIError(0, "Max retries exceeded", {})

    # ════════════════════════════════════════════════════════════
    # Chat
    # ════════════════════════════════════════════════════════════

    def chat(
        self,
        message: str,
        context: Optional[Any] = None,
        voice: bool = False,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"message": message, "voice": voice}
        if context is not None:
            body["context"] = context
        resp = self._request_with_retry("POST", "/api/chat", json=body)
        self._raise_on_error(resp)
        return resp.json()

    async def chat_async(
        self,
        message: str,
        context: Optional[Any] = None,
        voice: bool = False,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"message": message, "voice": voice}
        if context is not None:
            body["context"] = context
        resp = await self._arequest_with_retry("POST", "/api/chat", json=body)
        self._raise_on_error(resp)
        return resp.json()

    def chat_stream(
        self,
        message: str,
        context: Optional[Any] = None,
    ) -> Iterator[Dict[str, Any]]:
        """[PHASE3] True streaming via SSE /api/engine/stream.
        Falls back to non-streaming chat if stream is unavailable.
        """
        try:
            # Try streaming endpoint first
            body: Dict[str, Any] = {"message": message, "context": context or {}}
            with self._sync_client.stream(
                "POST", "/api/engine/stream", json=body, timeout=self._timeout
            ) as resp:
                self._raise_on_error(resp)
                buffer = ""
                for line in resp.iter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
        except (APIError, httpx.HTTPError):
            # Fallback: return non-streaming response
            result = self.chat(message, context, voice=False)
            yield result

    async def chat_stream_async(
        self,
        message: str,
        context: Optional[Any] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """[PHASE3] Async streaming via SSE"""
        try:
            body: Dict[str, Any] = {"message": message, "context": context or {}}
            client = self._get_async()
            async with client.stream(
                "POST", "/api/engine/stream", json=body, timeout=self._timeout
            ) as resp:
                self._raise_on_error(resp)
                async for line in resp.aiter_lines():
                    if line.startswith("data: "):
                        try:
                            data = json.loads(line[6:])
                            yield data
                        except json.JSONDecodeError:
                            continue
        except (APIError, httpx.HTTPError):
            result = await self.chat_async(message, context, voice=False)
            yield result

    # ════════════════════════════════════════════════════════════
    # Status / Health
    # ════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/status")
        self._raise_on_error(resp)
        return resp.json()

    async def get_status_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/status")
        self._raise_on_error(resp)
        return resp.json()

    def get_system_health(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/engine/health")
        self._raise_on_error(resp)
        return resp.json()

    async def get_system_health_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/engine/health")
        self._raise_on_error(resp)
        return resp.json()

    def get_diagnostics(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/engine/diagnostics")
        self._raise_on_error(resp)
        return resp.json()

    async def get_diagnostics_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/engine/diagnostics")
        self._raise_on_error(resp)
        return resp.json()

    def get_metrics(self) -> str:
        """[PHASE3] Returns Prometheus metrics text format"""
        resp = self._request_with_retry("GET", "/metrics")
        self._raise_on_error(resp)
        return resp.text

    # ════════════════════════════════════════════════════════════
    # Knowledge Base
    # ════════════════════════════════════════════════════════════

    def search_knowledge(
        self,
        query: str,
        collection: str = "knowledge",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        resp = self._request_with_retry(
            "POST", "/api/knowledge/search",
            json={"query": query, "collection": collection, "top_k": top_k},
        )
        self._raise_on_error(resp)
        return resp.json()

    async def search_knowledge_async(
        self,
        query: str,
        collection: str = "knowledge",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        resp = await self._arequest_with_retry(
            "POST", "/api/knowledge/search",
            json={"query": query, "collection": collection, "top_k": top_k},
        )
        self._raise_on_error(resp)
        return resp.json()

    def add_knowledge(self, text: str, collection: str = "knowledge") -> Dict[str, Any]:
        resp = self._request_with_retry(
            "POST", "/api/knowledge/add",
            json={"texts": [text], "collection": collection},
        )
        self._raise_on_error(resp)
        return resp.json()

    async def add_knowledge_async(
        self, text: str, collection: str = "knowledge"
    ) -> Dict[str, Any]:
        resp = await self._arequest_with_retry(
            "POST", "/api/knowledge/add",
            json={"texts": [text], "collection": collection},
        )
        self._raise_on_error(resp)
        return resp.json()

    def upload_knowledge_file(
        self,
        filepath: Union[str, Path],
        collection: str = "knowledge",
    ) -> Dict[str, Any]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"الملف مش موجود: {path}")
        with open(path, "rb") as f:
            files = {"file": (path.name, f)}
            data = {"collection": collection}
            resp = self._request_with_retry(
                "POST", "/api/knowledge/upload", files=files, data=data
            )
        self._raise_on_error(resp)
        return resp.json()

    async def upload_knowledge_file_async(
        self,
        filepath: Union[str, Path],
        collection: str = "knowledge",
    ) -> Dict[str, Any]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"الملف مش موجود: {path}")
        with open(path, "rb") as f:
            files = {"file": (path.name, f.read())}
            data = {"collection": collection}
            resp = await self._arequest_with_retry(
                "POST", "/api/knowledge/upload", files=files, data=data
            )
        self._raise_on_error(resp)
        return resp.json()

    def list_collections(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/knowledge/collections")
        self._raise_on_error(resp)
        return resp.json()

    async def list_collections_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/knowledge/collections")
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Sessions
    # ════════════════════════════════════════════════════════════

    def list_sessions(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        resp = self._request_with_retry(
            "GET", "/api/chat/sessions",
            params={"limit": limit, "offset": offset},
        )
        self._raise_on_error(resp)
        return resp.json()

    async def list_sessions_async(
        self, limit: int = 50, offset: int = 0
    ) -> Dict[str, Any]:
        resp = await self._arequest_with_retry(
            "GET", "/api/chat/sessions",
            params={"limit": limit, "offset": offset},
        )
        self._raise_on_error(resp)
        return resp.json()

    def create_session(
        self,
        title: str = "New Conversation",
        first_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"title": title}
        if first_message is not None:
            body["first_message"] = first_message
        resp = self._request_with_retry("POST", "/api/chat/sessions", json=body)
        self._raise_on_error(resp)
        return resp.json()

    async def create_session_async(
        self,
        title: str = "New Conversation",
        first_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        body: Dict[str, Any] = {"title": title}
        if first_message is not None:
            body["first_message"] = first_message
        resp = await self._arequest_with_retry("POST", "/api/chat/sessions", json=body)
        self._raise_on_error(resp)
        return resp.json()

    def get_session(self, session_id: str) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", f"/api/chat/sessions/{session_id}")
        self._raise_on_error(resp)
        return resp.json()

    async def get_session_async(self, session_id: str) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", f"/api/chat/sessions/{session_id}")
        self._raise_on_error(resp)
        return resp.json()

    def delete_session(self, session_id: str) -> Dict[str, Any]:
        resp = self._request_with_retry("DELETE", f"/api/chat/sessions/{session_id}")
        self._raise_on_error(resp)
        return resp.json()

    async def delete_session_async(self, session_id: str) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("DELETE", f"/api/chat/sessions/{session_id}")
        self._raise_on_error(resp)
        return resp.json()

    def search_chat_history(self, query: str, limit: int = 20) -> Dict[str, Any]:
        resp = self._request_with_retry(
            "POST", "/api/chat/search",
            json={"query": query, "limit": limit},
        )
        self._raise_on_error(resp)
        return resp.json()

    async def search_chat_history_async(
        self, query: str, limit: int = 20
    ) -> Dict[str, Any]:
        resp = await self._arequest_with_retry(
            "POST", "/api/chat/search",
            json={"query": query, "limit": limit},
        )
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Skills / Plugins
    # ════════════════════════════════════════════════════════════

    def list_skills(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/skills/list")
        self._raise_on_error(resp)
        return resp.json()

    async def list_skills_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/skills/list")
        self._raise_on_error(resp)
        return resp.json()

    def load_skill(self, path: str) -> Dict[str, Any]:
        resp = self._request_with_retry("POST", "/api/skills/load", json={"path": path})
        self._raise_on_error(resp)
        return resp.json()

    async def load_skill_async(self, path: str) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("POST", "/api/skills/load", json={"path": path})
        self._raise_on_error(resp)
        return resp.json()

    def list_plugins(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/plugins")
        self._raise_on_error(resp)
        return resp.json()

    async def list_plugins_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/plugins")
        self._raise_on_error(resp)
        return resp.json()

    def load_plugin(self, path: str) -> Dict[str, Any]:
        resp = self._request_with_retry("POST", "/api/plugins/load", json={"path": path})
        self._raise_on_error(resp)
        return resp.json()

    async def load_plugin_async(self, path: str) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("POST", "/api/plugins/load", json={"path": path})
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Channels
    # ════════════════════════════════════════════════════════════

    def list_channels(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/channels")
        self._raise_on_error(resp)
        return resp.json()

    async def list_channels_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/channels")
        self._raise_on_error(resp)
        return resp.json()

    def get_channel(self, name: str) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", f"/api/channels/{name}")
        self._raise_on_error(resp)
        return resp.json()

    async def get_channel_async(self, name: str) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", f"/api/channels/{name}")
        self._raise_on_error(resp)
        return resp.json()

    def toggle_channel(self, name: str, enabled: bool) -> Dict[str, Any]:
        resp = self._request_with_retry(
            "POST", f"/api/channels/{name}", json={"enabled": enabled}
        )
        self._raise_on_error(resp)
        return resp.json()

    async def toggle_channel_async(self, name: str, enabled: bool) -> Dict[str, Any]:
        resp = await self._arequest_with_retry(
            "POST", f"/api/channels/{name}", json={"enabled": enabled}
        )
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Ollama
    # ════════════════════════════════════════════════════════════

    def list_ollama_models(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/ollama/models")
        self._raise_on_error(resp)
        return resp.json()

    async def list_ollama_models_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/ollama/models")
        self._raise_on_error(resp)
        return resp.json()

    def select_ollama_model(self, model: str) -> Dict[str, Any]:
        resp = self._request_with_retry("POST", "/api/ollama/select", json={"model": model})
        self._raise_on_error(resp)
        return resp.json()

    async def select_ollama_model_async(self, model: str) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("POST", "/api/ollama/select", json={"model": model})
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Memory / Notebook / Security
    # ════════════════════════════════════════════════════════════

    def get_memory_stats(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/memory/stats")
        self._raise_on_error(resp)
        return resp.json()

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/memory/stats")
        self._raise_on_error(resp)
        return resp.json()

    def get_notebook_stats(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/notebook/stats")
        self._raise_on_error(resp)
        return resp.json()

    async def get_notebook_stats_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/notebook/stats")
        self._raise_on_error(resp)
        return resp.json()

    def get_security_stats(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/security/stats")
        self._raise_on_error(resp)
        return resp.json()

    async def get_security_stats_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/security/stats")
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Scheduler
    # ════════════════════════════════════════════════════════════

    def list_scheduled_jobs(self) -> Dict[str, Any]:
        resp = self._request_with_retry("GET", "/api/scheduler/jobs")
        self._raise_on_error(resp)
        return resp.json()

    async def list_scheduled_jobs_async(self) -> Dict[str, Any]:
        resp = await self._arequest_with_retry("GET", "/api/scheduler/jobs")
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Voice
    # ════════════════════════════════════════════════════════════

    def transcribe_audio(self, filepath: Union[str, Path]) -> Dict[str, Any]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"الملف مش موجود: {path}")
        with open(path, "rb") as f:
            files = {"audio": (path.name, f, "audio/wav")}
            resp = self._request_with_retry(
                "POST", "/api/voice/transcribe", files=files
            )
        self._raise_on_error(resp)
        return resp.json()

    async def transcribe_audio_async(
        self, filepath: Union[str, Path]
    ) -> Dict[str, Any]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"الملف مش موجود: {path}")
        with open(path, "rb") as f:
            data = f.read()
        files = {"audio": (path.name, data, "audio/wav")}
        resp = await self._arequest_with_retry(
            "POST", "/api/voice/transcribe", files=files
        )
        self._raise_on_error(resp)
        return resp.json()
