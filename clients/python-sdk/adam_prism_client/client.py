"""
Adam Prism Client — Python SDK
================================
عميل متكامل (sync + async) للتفاعل مع خادم Adam Prism API.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, AsyncGenerator, Dict, List, Optional

import httpx

from .errors import APIError, ConnectionError, NotFoundError, ServiceUnavailableError, TimeoutError
from .models import (
    AddKnowledgeResponse,
    ChannelStatus,
    ChatResponse,
    ChatSearchResponse,
    CollectionsResponse,
    DiagnosticsResponse,
    KnowledgeSearchResponse,
    LoadPluginResponse,
    LoadSkillResponse,
    Metrics,
    OllamaModelsResponse,
    PluginsResponse,
    ScheduledJobsResponse,
    SelectOllamaModelResponse,
    Session,
    SessionListResponse,
    SkillsResponse,
    SystemHealth,
    SystemStatus,
    ToggleChannelResponse,
    TranscriptionResponse,
    UploadKnowledgeResponse,
)


class AdamPrismClient:
    """Python client for the Adam Prism API — يدعم المزامنة وعدم المزامنة."""

    def __init__(
        self,
        base_url: str = "http://localhost:8000",
        timeout: float = 30.0,
        *,
        api_key: Optional[str] = None,
    ):
        self.base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._headers: Dict[str, str] = {"Content-Type": "application/json"}
        if api_key:
            self._headers["Authorization"] = f"Bearer {api_key}"

        self._sync_client: Optional[httpx.Client] = None
        self._async_client: Optional[httpx.AsyncClient] = None

    # ── HTTP helpers ───────────────────────────────────────────

    def _get_sync(self) -> httpx.Client:
        if self._sync_client is None or self._sync_client.is_closed:
            self._sync_client = httpx.Client(base_url=self.base_url, headers=self._headers, timeout=self._timeout)
        return self._sync_client

    def _get_async(self) -> httpx.AsyncClient:
        if self._async_client is None or self._async_client.is_closed:
            self._async_client = httpx.AsyncClient(base_url=self.base_url, headers=self._headers, timeout=self._timeout)
        return self._async_client

    def _raise_on_error(self, resp: httpx.Response):
        if resp.status_code < 400:
            return
        try:
            body = resp.json()
        except Exception:
            body = {}
        if resp.status_code == 404:
            raise NotFoundError(body.get("detail", ""), body)
        elif resp.status_code == 503:
            raise ServiceUnavailableError(body.get("detail", ""), body)
        elif 500 <= resp.status_code < 600:
            raise APIError(resp.status_code, body.get("detail", ""), body)
        else:
            raise APIError(resp.status_code, body.get("detail", ""), body)

    def close(self):
        """Close all underlying HTTP clients."""
        if self._sync_client and not self._sync_client.is_closed:
            self._sync_client.close()
        if self._async_client and not self._async_client.is_closed:
            self._async_client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()

    async def __aenter__(self):
        return self

    async def __aexit__(self, *args):
        self.close()

    # ════════════════════════════════════════════════════════════
    # Chat
    # ════════════════════════════════════════════════════════════

    def chat(
        self,
        message: str,
        context: Optional[Any] = None,
        voice: bool = True,
    ) -> Dict[str, Any]:
        """إرسال رسالة واستقبال رد

        Args:
            message: نص الرسالة
            context: سياق إضافي (dict أو str)
            voice: توليد رد صوتي

        Returns:
            ChatResponse as dict
        """
        body: Dict[str, Any] = {"message": message, "voice": voice}
        if context is not None:
            body["context"] = context
        resp = self._get_sync().post("/api/chat", json=body)
        self._raise_on_error(resp)
        return resp.json()

    async def chat_async(
        self,
        message: str,
        context: Optional[Any] = None,
        voice: bool = True,
    ) -> Dict[str, Any]:
        """إرسال رسالة واستقبال رد — نسخة async"""
        body: Dict[str, Any] = {"message": message, "voice": voice}
        if context is not None:
            body["context"] = context
        resp = await self._get_async().post("/api/chat", json=body)
        self._raise_on_error(resp)
        return resp.json()

    def chat_stream(
        self,
        message: str,
        context: Optional[Any] = None,
        voice: bool = True,
    ):
        """بث الرد عبر SSE (engine status stream).

        ملاحظة: النسخة الحالية من API لا تدعم البث المباشر للـ chat.
        يتم إرجاع الرد كاملًا كخطوة أولى. فور توفر stream حقيقي سيتم التبديل.
        """
        result = self.chat(message, context, voice)
        yield result

    async def chat_stream_async(
        self,
        message: str,
        context: Optional[Any] = None,
        voice: bool = True,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """بث الرد — نسخة async"""
        result = await self.chat_async(message, context, voice)
        yield result

    # ════════════════════════════════════════════════════════════
    # Status
    # ════════════════════════════════════════════════════════════

    def get_status(self) -> Dict[str, Any]:
        """حالة النظام والمحرك"""
        resp = self._get_sync().get("/api/status")
        self._raise_on_error(resp)
        return resp.json()

    async def get_status_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/status")
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Knowledge Base
    # ════════════════════════════════════════════════════════════

    def search_knowledge(
        self,
        query: str,
        collection: str = "knowledge",
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """البحث في القاعدة المعرفية"""
        resp = self._get_sync().post(
            "/api/knowledge/search",
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
        resp = await self._get_async().post(
            "/api/knowledge/search",
            json={"query": query, "collection": collection, "top_k": top_k},
        )
        self._raise_on_error(resp)
        return resp.json()

    def add_knowledge(self, text: str, collection: str = "knowledge") -> Dict[str, Any]:
        """إضافة معرفة جديدة إلى Qdrant"""
        resp = self._get_sync().post(
            "/api/knowledge/add",
            json={"text": text, "collection": collection},
        )
        self._raise_on_error(resp)
        return resp.json()

    async def add_knowledge_async(self, text: str, collection: str = "knowledge") -> Dict[str, Any]:
        resp = await self._get_async().post(
            "/api/knowledge/add",
            json={"text": text, "collection": collection},
        )
        self._raise_on_error(resp)
        return resp.json()

    def upload_knowledge_file(
        self,
        filepath: str | Path,
        collection: str = "knowledge",
    ) -> Dict[str, Any]:
        """رفع ملف (PDF, DOCX, TXT, MD) إلى قاعدة المعرفة

        Args:
            filepath: المسار المحلي للملف
            collection: اسم المجموعة
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"الملف مش موجود: {path}")
        files = {"file": (path.name, path.read_bytes())}
        data = {"collection": collection}
        resp = self._get_sync().post("/api/knowledge/upload", files=files, data=data)
        self._raise_on_error(resp)
        return resp.json()

    async def upload_knowledge_file_async(
        self,
        filepath: str | Path,
        collection: str = "knowledge",
    ) -> Dict[str, Any]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"الملف مش موجود: {path}")
        files = {"file": (path.name, path.read_bytes())}
        data = {"collection": collection}
        resp = await self._get_async().post("/api/knowledge/upload", files=files, data=data)
        self._raise_on_error(resp)
        return resp.json()

    def list_collections(self) -> Dict[str, Any]:
        """عرض كل المجموعات في Qdrant"""
        resp = self._get_sync().get("/api/knowledge/collections")
        self._raise_on_error(resp)
        return resp.json()

    async def list_collections_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/knowledge/collections")
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Sessions
    # ════════════════════════════════════════════════════════════

    def list_sessions(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        """قائمة جلسات المحادثة"""
        resp = self._get_sync().get("/api/chat/sessions", params={"limit": limit, "offset": offset})
        self._raise_on_error(resp)
        return resp.json()

    async def list_sessions_async(self, limit: int = 50, offset: int = 0) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/chat/sessions", params={"limit": limit, "offset": offset})
        self._raise_on_error(resp)
        return resp.json()

    def create_session(
        self,
        title: str = "New Conversation",
        first_message: Optional[str] = None,
    ) -> Dict[str, Any]:
        """إنشاء جلسة جديدة"""
        body: Dict[str, Any] = {"title": title}
        if first_message is not None:
            body["first_message"] = first_message
        resp = self._get_sync().post("/api/chat/sessions", json=body)
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
        resp = await self._get_async().post("/api/chat/sessions", json=body)
        self._raise_on_error(resp)
        return resp.json()

    def get_session(self, session_id: str) -> Dict[str, Any]:
        """جلب جلسة مع رسائلها"""
        resp = self._get_sync().get(f"/api/chat/sessions/{session_id}")
        self._raise_on_error(resp)
        return resp.json()

    async def get_session_async(self, session_id: str) -> Dict[str, Any]:
        resp = await self._get_async().get(f"/api/chat/sessions/{session_id}")
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Chat History Search
    # ════════════════════════════════════════════════════════════

    def search_chat_history(self, query: str, limit: int = 20) -> Dict[str, Any]:
        """البحث النصي في تاريخ المحادثات"""
        resp = self._get_sync().post(
            "/api/chat/search",
            json={"query": query, "limit": limit},
        )
        self._raise_on_error(resp)
        return resp.json()

    async def search_chat_history_async(self, query: str, limit: int = 20) -> Dict[str, Any]:
        resp = await self._get_async().post(
            "/api/chat/search",
            json={"query": query, "limit": limit},
        )
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Skills
    # ════════════════════════════════════════════════════════════

    def list_skills(self) -> Dict[str, Any]:
        """جلب كل المهارات المتاحة"""
        resp = self._get_sync().get("/api/skills/list")
        self._raise_on_error(resp)
        return resp.json()

    async def list_skills_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/skills/list")
        self._raise_on_error(resp)
        return resp.json()

    def load_skill(self, path: str) -> Dict[str, Any]:
        """تحميل وتشغيل مهارة"""
        resp = self._get_sync().post("/api/skills/load", json={"path": path})
        self._raise_on_error(resp)
        return resp.json()

    async def load_skill_async(self, path: str) -> Dict[str, Any]:
        resp = await self._get_async().post("/api/skills/load", json={"path": path})
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Plugins
    # ════════════════════════════════════════════════════════════

    def list_plugins(self) -> Dict[str, Any]:
        """جلب كل الإضافات"""
        resp = self._get_sync().get("/api/plugins")
        self._raise_on_error(resp)
        return resp.json()

    async def list_plugins_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/plugins")
        self._raise_on_error(resp)
        return resp.json()

    def load_plugin(self, path: str) -> Dict[str, Any]:
        """تحميل إضافة من مسار"""
        resp = self._get_sync().post("/api/plugins/load", json={"path": path})
        self._raise_on_error(resp)
        return resp.json()

    async def load_plugin_async(self, path: str) -> Dict[str, Any]:
        resp = await self._get_async().post("/api/plugins/load", json={"path": path})
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Channels
    # ════════════════════════════════════════════════════════════

    def list_channels(self) -> Dict[str, Any]:
        """حالة كل القنوات"""
        resp = self._get_sync().get("/api/channels")
        self._raise_on_error(resp)
        return resp.json()

    async def list_channels_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/channels")
        self._raise_on_error(resp)
        return resp.json()

    def get_channel(self, name: str) -> Dict[str, Any]:
        """حالة قناة معينة"""
        resp = self._get_sync().get(f"/api/channels/{name}")
        self._raise_on_error(resp)
        return resp.json()

    async def get_channel_async(self, name: str) -> Dict[str, Any]:
        resp = await self._get_async().get(f"/api/channels/{name}")
        self._raise_on_error(resp)
        return resp.json()

    def toggle_channel(self, name: str, enabled: bool) -> Dict[str, Any]:
        """تشغيل/إيقاف قناة"""
        resp = self._get_sync().post(f"/api/channels/{name}", json={"enabled": enabled})
        self._raise_on_error(resp)
        return resp.json()

    async def toggle_channel_async(self, name: str, enabled: bool) -> Dict[str, Any]:
        resp = await self._get_async().post(f"/api/channels/{name}", json={"enabled": enabled})
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # System
    # ════════════════════════════════════════════════════════════

    def get_system_health(self) -> Dict[str, Any]:
        """مؤشرات صحة النظام"""
        resp = self._get_sync().get("/api/engine/health")
        self._raise_on_error(resp)
        return resp.json()

    async def get_system_health_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/engine/health")
        self._raise_on_error(resp)
        return resp.json()

    def get_metrics(self) -> Dict[str, Any]:
        """مؤشرات الأداء الداخلية"""
        resp = self._get_sync().get("/api/metrics")
        self._raise_on_error(resp)
        return resp.json()

    async def get_metrics_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/metrics")
        self._raise_on_error(resp)
        return resp.json()

    def get_diagnostics(self) -> Dict[str, Any]:
        """تشخيص ذاتي شامل"""
        resp = self._get_sync().get("/api/engine/diagnostics")
        self._raise_on_error(resp)
        return resp.json()

    async def get_diagnostics_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/engine/diagnostics")
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Ollama
    # ════════════════════════════════════════════════════════════

    def list_ollama_models(self) -> Dict[str, Any]:
        """جلب كل الموديلات المتاحة في Ollama"""
        resp = self._get_sync().get("/api/ollama/models")
        self._raise_on_error(resp)
        return resp.json()

    async def list_ollama_models_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/ollama/models")
        self._raise_on_error(resp)
        return resp.json()

    def select_ollama_model(self, model: str) -> Dict[str, Any]:
        """تبديل الموديل النشط في Ollama"""
        resp = self._get_sync().post("/api/ollama/select", json={"model": model})
        self._raise_on_error(resp)
        return resp.json()

    async def select_ollama_model_async(self, model: str) -> Dict[str, Any]:
        resp = await self._get_async().post("/api/ollama/select", json={"model": model})
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Voice
    # ════════════════════════════════════════════════════════════

    def transcribe_audio(self, filepath: str | Path) -> Dict[str, Any]:
        """نسخ صوت إلى نص

        Args:
            filepath: المسار المحلي للملف الصوتي (16kHz WAV preferred)
        """
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"الملف مش موجود: {path}")
        files = {"audio": (path.name, path.read_bytes(), "audio/wav")}
        resp = self._get_sync().post("/api/voice/transcribe", files=files)
        self._raise_on_error(resp)
        return resp.json()

    async def transcribe_audio_async(self, filepath: str | Path) -> Dict[str, Any]:
        path = Path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"الملف مش موجود: {path}")
        files = {"audio": (path.name, path.read_bytes(), "audio/wav")}
        resp = await self._get_async().post("/api/voice/transcribe", files=files)
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Memory / Notebook / Security Stats
    # ════════════════════════════════════════════════════════════

    def get_memory_stats(self) -> Dict[str, Any]:
        """إحصائيات الذاكرة"""
        resp = self._get_sync().get("/api/memory/stats")
        self._raise_on_error(resp)
        return resp.json()

    async def get_memory_stats_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/memory/stats")
        self._raise_on_error(resp)
        return resp.json()

    def get_notebook_stats(self) -> Dict[str, Any]:
        """إحصائيات الدفتر"""
        resp = self._get_sync().get("/api/notebook/stats")
        self._raise_on_error(resp)
        return resp.json()

    async def get_notebook_stats_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/notebook/stats")
        self._raise_on_error(resp)
        return resp.json()

    def get_security_stats(self) -> Dict[str, Any]:
        """إحصائيات الأمن"""
        resp = self._get_sync().get("/api/security/stats")
        self._raise_on_error(resp)
        return resp.json()

    async def get_security_stats_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/security/stats")
        self._raise_on_error(resp)
        return resp.json()

    # ════════════════════════════════════════════════════════════
    # Scheduler
    # ════════════════════════════════════════════════════════════

    def list_scheduled_jobs(self) -> Dict[str, Any]:
        """قائمة المهام المجدولة"""
        resp = self._get_sync().get("/api/scheduler/jobs")
        self._raise_on_error(resp)
        return resp.json()

    async def list_scheduled_jobs_async(self) -> Dict[str, Any]:
        resp = await self._get_async().get("/api/scheduler/jobs")
        self._raise_on_error(resp)
        return resp.json()
