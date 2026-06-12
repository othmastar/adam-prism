"""
Adam Prism - API Server — HARDENED v2
======================================
خادم API يربط كل الموديولات ويوفر الواجهة للـ Web UI والـ Telegram.
يعمل على FastAPI مع WebSocket support.

[SECURITY FIXES v2]
1. رفض التشغيل بمفتاح API افتراضي في الإنتاج
2. حماية نقاط webhook من تجاوز المصادقة (ترتيب صحيح)
3. حماية WebSocket بالمصادقة (token parameter)
4. تقييد إضافة خوادم MCP بالمسؤول فقط (ADAM_ADMIN_KEY)
5. تحديد عدد الوكلاء الفرعيين
6. [NEW] Rate limiting لكل نقاط API
7. [NEW] تأكيد مفتاح المسؤول لإضافة MCP
8. [NEW] تحديد حجم طلبات API
9. [NEW] تسجيل أمني شامل
"""

import json
import os
import sqlite3
import logging
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, Optional, List

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse, JSONResponse
from adam.api.diagnostic import router as diagnostic_router
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from pydantic import BaseModel
from adam.api.chat_store import ChatStore
from adam.core.voice import VoicePipeline, int16_to_float32, resample_audio
from adam.core.permissions import log_permission

logger = logging.getLogger("adam_prism.api")

# ═══════════════════════════════════════
# Models
# ═══════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    context: Optional[Any] = None
    voice: bool = True  # رد صوتي دائم

class ToolRecord(BaseModel):
    name: str
    params: Dict = {}
    success: bool = False
    error: Optional[str] = None

class ChatResponse(BaseModel):
    response: str
    mode: str = "communicator"
    intent: Optional[Dict] = None
    knowledge_used: int = 0
    tool_calls_made: int = 0
    tools_used: List[str] = []
    tool_records: List[ToolRecord] = []
    errors: List[str] = []
    cycle: int = 0
    duration_ms: Optional[int] = None
    reason: Optional[str] = None
    audio_url: Optional[str] = None  # رابط الاستماع للرد
    permission_pending: Optional[Dict] = None  # طلب صلاحية معلّق (Phase 1b)

class SearchRequest(BaseModel):
    query: str
    collection: str = "knowledge"
    top_k: int = 3

class SummarizeRequest(BaseModel):
    text: str
    source: str = "manual"
    title: str = "Untitled"
    max_length: int = 500

class ActionRequest(BaseModel):
    action: str
    params: Dict = {}

# متغير عام لوقت بدء التشغيل
_start_time: Optional[datetime] = None

def _qdrant_url(engine):
    if engine and engine.config:
        return engine.config.get("qdrant_url", "http://localhost:6333")
    return os.environ.get("QDRANT_URL", "http://localhost:6333")

def _ollama_url(engine):
    if engine and engine.config:
        return engine.config.get("ollama_base", "http://localhost:11434")
    return os.environ.get("OLLAMA_URL", "http://localhost:11434")

def _lora_url(engine):
    if engine and engine.config:
        return engine.config.get("lora_server_url", "http://localhost:8080")
    return os.environ.get("LORA_URL", "http://localhost:8080")

def _qdrant_client(engine):
    from urllib.parse import urlparse
    pu = urlparse(_qdrant_url(engine))
    from qdrant_client import QdrantClient
    return QdrantClient(host=pu.hostname or "localhost", port=pu.port or 6333)


# ═══════════════════════════════════════════════════════
# [NEW] Rate Limiter — حماية من إساءة الاستخدام
# ═══════════════════════════════════════════════════════

class RateLimiter:
    """Rate limiter بسيط في الذاكرة — لكل IP"""

    def __init__(self, max_requests: int = 60, window_seconds: int = 60):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: Dict[str, List[float]] = {}

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        if key not in self._requests:
            self._requests[key] = [now]
            return True
        # حذف الطلبات القديمة
        self._requests[key] = [t for t in self._requests[key] if now - t < self.window_seconds]
        if len(self._requests[key]) >= self.max_requests:
            return False
        self._requests[key].append(now)
        return True

    def get_remaining(self, key: str) -> int:
        now = time.time()
        if key not in self._requests:
            return self.max_requests
        self._requests[key] = [t for t in self._requests[key] if now - t < self.window_seconds]
        return max(0, self.max_requests - len(self._requests[key]))


# ═══════════════════════════════════════════════════════

def create_app(engine=None, channel_manager=None) -> FastAPI:
    """إنشاء تطبيق FastAPI مع كل المسارات"""

    app = FastAPI(
        title="Adam Prism API",
        description="واجهة برمجة التطبيقات لآدم بريزم - التوأم الرقمي الشخصي",
        version="1.0.0"
    )

    # ═══════════════════════════════════════════════════════
    # [FIX] المصادقة — تفعيلها أولاً قبل أي مسارات
    # ═══════════════════════════════════════════════════════
    import hmac as _hmac
    _api_key = os.environ.get("ADAM_API_KEY", "adam-prism-change-me")

    # [FIX v2] مفتاح المسؤول — لإضافة خوادم MCP وعمليات حساسة
    _admin_key = os.environ.get("ADAM_ADMIN_KEY", "")

    # [FIX] في وضع الإنتاج، نرفض المفتاح الافتراضي
    _is_production = os.environ.get("ADAM_PRODUCTION", "0") == "1"
    if _is_production and _api_key == "adam-prism-change-me":
        raise RuntimeError(
            "SECURITY: ADAM_API_KEY not set in production mode! "
            "Set a strong API key via environment variable ADAM_API_KEY before starting."
        )

    # [FIX v2] في وضع الإنتاج، لازم يكون فيه مفتاح مسؤول
    if _is_production and not _admin_key:
        raise RuntimeError(
            "SECURITY: ADAM_ADMIN_KEY not set in production mode! "
            "Set an admin key via environment variable ADAM_ADMIN_KEY before starting."
        )

    if _api_key == "adam-prism-change-me":
        logger.warning("=" * 60)
        logger.warning("ADAM_API_KEY not set — using default key!")
        logger.warning("Anyone can access your API with the default key!")
        logger.warning("Set ADAM_API_KEY environment variable to a strong secret!")
        logger.warning("=" * 60)

    if not _admin_key:
        logger.warning("ADAM_ADMIN_KEY not set — MCP admin operations disabled!")

    # [NEW] Rate limiter
    _rate_limiter = RateLimiter(
        max_requests=int(os.environ.get("ADAM_RATE_LIMIT", "60")),
        window_seconds=60
    )

    # المسارات العامة — فقط الصفحة الرئيسية والوثائق
    _public_paths = {"/", "/api/status", "/docs", "/openapi.json", "/redoc"}

    # [NEW] الحد الأقصى لحجم طلب API
    _max_request_size = int(os.environ.get("ADAM_MAX_REQUEST_SIZE", str(10 * 1024 * 1024)))  # 10MB default

    @app.middleware("http")
    async def _check_api_key(request: Request, call_next):
        # نقاط مسموحة بدون مفتاح — الصفحة الرئيسية والوثائق فقط
        if request.url.path in _public_paths:
            return await call_next(request)

        # [NEW] Rate limiting
        client_ip = request.client.host if request.client else "unknown"
        if not _rate_limiter.is_allowed(client_ip):
            logger.warning(f"Rate limit exceeded for IP: {client_ip}")
            return JSONResponse(
                status_code=429,
                content={"detail": "Too many requests — slow down"}
            )

        # المصادقة
        auth = request.headers.get("Authorization", "")
        expected = f"Bearer {_api_key}"
        if _hmac.compare_digest(auth.encode(), expected.encode()):
            return await call_next(request)
        return JSONResponse(status_code=403, content={"detail": "Unauthorized — provide Bearer token in Authorization header"})

    # [NEW] Middleware لتحديد حجم الطلب
    @app.middleware("http")
    async def _limit_request_size(request: Request, call_next):
        if request.method in ("POST", "PUT", "PATCH"):
            content_length = request.headers.get("content-length")
            if content_length and int(content_length) > _max_request_size:
                return JSONResponse(
                    status_code=413,
                    content={"detail": f"Request too large (max: {_max_request_size // 1024 // 1024}MB)"}
                )
        return await call_next(request)

    logger.info("API Key authentication enabled")
    logger.info(f"Rate limiter: {os.environ.get('ADAM_RATE_LIMIT', '60')} req/min")

    # [FIX] CORS — تقييد أصل الإنتاج
    cors_origins = os.environ.get("CORS_ORIGINS", "*")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins.split(",") if cors_origins != "*" else ["*"],
        allow_credentials=cors_origins != "*",
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ═══════════════════════════════════════════════════════
    # نقاط webhook — الآن بعد المصادقة، محمية تلقائياً
    # ═══════════════════════════════════════════════════════

    # Mount channel webhook routes
    if channel_manager:
        try:
            routes = channel_manager.get_webhook_routes()
            for route in routes:
                path = route["path"]
                method = route["method"].lower()
                handler = route["handler"]
                if method == "get":
                    app.get(path)(handler)
                elif method == "post":
                    app.post(path)(handler)
            if routes:
                logger.info(f"Mounted {len(routes)} channel webhook routes (PROTECTED by auth)")
        except Exception as e:
            logger.warning(f"Channel route mounting failed: {e}")
    else:
        # Still attempt to find and mount webchat widget
        try:
            from adam.channels.bulk import WebChatChannel
            wc = WebChatChannel({})
            for route in wc.get_webhook_routes():
                path, method = route["path"], route["method"].lower()
                handler = route["handler"]
                if method == "post":
                    app.post(path)(handler)
                elif method == "get":
                    app.get(path)(handler)
            logger.info("WebChat widget mounted at /chat/webhook and /chat/widget (PROTECTED by auth)")
        except Exception:
            pass

    # Serve static UI files
    import os as _os
    _static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "web-ui", "public")
    if _os.path.isdir(_static_dir):
        try:
            from fastapi.staticfiles import StaticFiles
            app.mount("/ui", StaticFiles(directory=_static_dir, html=True), name="ui")
        except Exception as e:
            logger.warning(f"فشل تحميل الملفات الثابتة: {e}")

    # Diagnostic & Orchestrator routes
    try:
        app.include_router(diagnostic_router)
    except Exception as e:
        logger.warning(f"فشل تحميل مسارات التشخيص: {e}")

    # Chat history store
    chat_store = ChatStore()

    # ═══════════════════════════════════════
    # Routes
    # ═══════════════════════════════════════

    @app.get("/")
    async def root():
        """الصفحة الرئيسية"""
        return {
            "name": "Adam Prism",
            "version": "1.0.0",
            "status": "running",
            "endpoints": {
                "chat": "/api/chat",
                "status": "/api/status",
                "search": "/api/knowledge/search",
                "summarize": "/api/pipeline/summarize",
                "action": "/api/tools/action",
                "notebook": "/api/notebook/{date}",
                "ws": "/ws/chat"
            }
        }

    @app.get("/api/status")
    async def get_status():
        """حالة النظام"""
        if engine:
            status = await engine.get_status()
            status["inference_mode"] = engine.inference_mode
            status["lora_server_url"] = engine.lora_server_url
            return status
        return {"status": "engine_not_attached"}

    @app.post("/api/chat", response_model=ChatResponse)
    async def chat(request: ChatRequest):
        """إرسال رسالة والحصول على رد مع رد صوتي"""
        if not engine:
            raise HTTPException(status_code=503, detail="المحرك غير متصل")

        # Normalize context: string → Dict, None → empty Dict
        ctx = request.context
        if ctx is None:
            ctx = {}
        elif isinstance(ctx, str):
            ctx = {"history": ctx}
        elif not isinstance(ctx, dict):
            ctx = {}

        # [FIX v2] تحديد طول الرسالة
        if len(request.message) > 10000:
            raise HTTPException(status_code=400, detail="الرسالة طويلة جداً (الحد: 10000 حرف)")

        result = await engine.chat(request.message, ctx)
        response = ChatResponse(**result)

        # التحقق من وجود طلب صلاحية معلّق
        if hasattr(engine, 'permission') and engine.permission.pending_request:
            response.permission_pending = engine.permission.pending_request

        # توليد رد صوتي إذا طُلب
        if request.voice and result.get("response"):
            try:
                pipeline = get_voice_pipeline()
                reply_text = result["response"]

                # تحميل TTS إذا لم يكن محمّلاً
                if not pipeline.tts.available:
                    await pipeline.load_tts()

                if pipeline.tts.available:
                    synthesis = await pipeline.process_text(reply_text, "ar")
                    if synthesis.audio:
                        filename = f"reply_{int(datetime.now().timestamp())}.mp3"
                        audio_path = await pipeline.save_audio(synthesis.audio, filename)
                        response.audio_url = f"/api/voice/audio/{filename}"

                    # تفريغ TTS من VRAM بعد الانتهاء
                    await pipeline.unload_tts()
            except Exception as e:
                logger.warning(f"فشل توليد الصوت للرد: {e}")

        return response

    # ═══════════════════════════════════════
    # Chat History - REST API
    # ═══════════════════════════════════════

    class CreateSessionRequest(BaseModel):
        title: str = "New Conversation"
        first_message: Optional[str] = None

    class UpdateSessionRequest(BaseModel):
        title: str

    class AddMessageRequest(BaseModel):
        role: str
        content: str
        mode: Optional[str] = None
        metadata: Optional[Dict] = None

    class ChatSearchRequest(BaseModel):
        query: str
        limit: int = 20

    @app.get("/api/chat/sessions")
    async def list_sessions(limit: int = 50, offset: int = 0):
        """قائمة جلسات المحادثة"""
        sessions = chat_store.list_sessions(limit, offset)
        return {"sessions": sessions, "total": len(sessions)}

    @app.post("/api/chat/sessions")
    async def create_session(req: CreateSessionRequest):
        """إنشاء جلسة جديدة (اختيارياً مع أول رسالة)"""
        session = chat_store.create_session(req.title)
        if req.first_message:
            chat_store.add_message(session["id"], "user", req.first_message, metadata={"title_generated": True})
        return session

    @app.get("/api/chat/sessions/{session_id}")
    async def get_session(session_id: str):
        """جلب جلسة مع رسائلها"""
        session = chat_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        messages = chat_store.list_messages(session_id)
        session["messages"] = messages
        return session

    @app.patch("/api/chat/sessions/{session_id}")
    async def update_session(session_id: str, req: UpdateSessionRequest):
        """تحديث عنوان الجلسة"""
        ok = chat_store.update_session(session_id, req.title)
        if not ok:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "updated"}

    @app.delete("/api/chat/sessions/{session_id}")
    async def delete_session(session_id: str):
        """حذف جلسة"""
        ok = chat_store.delete_session(session_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Session not found")
        return {"status": "deleted"}

    @app.get("/api/chat/sessions/{session_id}/messages")
    async def list_messages(session_id: str):
        """جلب رسائل جلسة معينة"""
        session = chat_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        messages = chat_store.list_messages(session_id)
        return {"messages": messages, "count": len(messages)}

    @app.post("/api/chat/sessions/{session_id}/messages")
    async def add_message(session_id: str, req: AddMessageRequest):
        """إضافة رسالة إلى جلسة"""
        session = chat_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        msg = chat_store.add_message(session_id, req.role, req.content, req.mode, req.metadata)
        return msg

    @app.post("/api/chat/sessions/{session_id}/sync")
    async def sync_session(session_id: str, messages: List[Dict]):
        """مزامنة كل رسائل جلسة دفعة واحدة (يحل محل القديم)"""
        session = chat_store.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        # حذف القديم وإعادة الإدراج
        with sqlite3.connect(str(chat_store.db_path)) as conn:
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
        for msg in messages:
            chat_store.add_message(
                session_id,
                msg.get("role", "user"),
                msg.get("content", ""),
                msg.get("mode"),
                msg.get("metadata"),
            )
        saved = chat_store.list_messages(session_id)
        return {"messages": saved, "count": len(saved)}

    @app.post("/api/chat/search")
    async def search_chat_history(req: ChatSearchRequest):
        """البحث النصي الكامل في تاريخ المحادثات عبر FTS5"""
        results = chat_store.search_messages(req.query, req.limit)
        return {"results": results, "count": len(results)}

    # ═══════════════════════════════════════
    # Knowledge Search
    # ═══════════════════════════════════════

    @app.post("/api/knowledge/search")
    async def search_knowledge(request: SearchRequest):
        """البحث في القاعدة المعرفية"""
        if engine and engine.knowledge:
            results = await engine.knowledge.search(
                request.query, request.collection, request.top_k, score_threshold=0.0
            )
            return {"results": results, "count": len(results)}
        raise HTTPException(status_code=503, detail="القاعدة المعرفية غير متصلة")

    @app.get("/api/knowledge/collections")
    async def list_collections():
        """عرض كل المجموعات في Qdrant مع عدد النقاط"""
        try:
            qdrant = _qdrant_client(engine)
            cols = qdrant.get_collections().collections
            result = []
            total = 0
            for c in cols:
                pts = qdrant.count(c.name)
                result.append({
                    "name": c.name,
                    "points": pts.count,
                })
                total += pts.count
            return {"collections": result, "total": total}
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Qdrant غير متصل: {e}")

    # ═══════════════════════════════════════
    # Add Knowledge to Qdrant
    # ═══════════════════════════════════════

    @app.post("/api/knowledge/add")
    async def add_knowledge(request: Request):
        """إضافة معرفة جديدة لـ Qdrant"""
        try:
            body = await request.json()
            texts = body.get("texts", [])
            if not texts:
                raise HTTPException(status_code=400, detail="texts array مطلوب")
            # [FIX v2] تحديد عدد النصوص المضافة
            if len(texts) > 100:
                raise HTTPException(status_code=400, detail="عدد النصوص كبير جداً (الحد: 100)")
            results = []
            for text in texts:
                if engine and engine.knowledge:
                    ok = await engine.knowledge.store(
                        collection=body.get("collection", "knowledge"),
                        text=text,
                        metadata=body.get("metadata", {}),
                    )
                    results.append(ok)
            return {"added": sum(1 for r in results if r), "total": len(results)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ═══════════════════════════════════════
    # Summarize
    # ═══════════════════════════════════════

    @app.post("/api/pipeline/summarize")
    async def summarize_text(request: SummarizeRequest):
        """تلخيص نص"""
        if not engine:
            raise HTTPException(status_code=503, detail="المحرك غير متصل")
        try:
            if engine.pipeline and hasattr(engine.pipeline, 'summarize'):
                summary = await engine.pipeline.summarize(request.text, request.max_length)
            else:
                summary = request.text[:request.max_length]
            return {"summary": summary, "source": request.source, "title": request.title}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ═══════════════════════════════════════
    # Tools — Execute Action
    # ═══════════════════════════════════════

    @app.post("/api/tools/action")
    async def execute_tool_action(request: ActionRequest):
        """تنفيذ إجراء عبر مدير الأدوات"""
        if not engine or not engine.tools:
            raise HTTPException(status_code=503, detail="مدير الأدوات غير متصل")
        try:
            result = await engine.tools.execute_action({"type": request.action, **request.params})
            return result
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ═══════════════════════════════════════
    # Tools — List Available
    # ═══════════════════════════════════════

    @app.get("/api/tools/available")
    async def list_available_tools():
        """عرض الأدوات المتاحة مع صلاحياتها"""
        from adam.security.guard import TOOL_REGISTRY
        tools = []
        for name, perm in TOOL_REGISTRY.items():
            tools.append({
                "name": name,
                "max_calls": perm.max_calls_per_session,
                "requires_confirmation": perm.requires_confirmation,
            })
        # إضافة أدوات MCP
        if engine and engine.tools:
            mcp_tools = engine.tools.get_mcp_tools()
            for t in mcp_tools:
                tools.append({
                    "name": t["name"],
                    "type": "mcp",
                    "server": t["server"],
                })
        return {"tools": tools, "count": len(tools)}

    # ═══════════════════════════════════════
    # MCP — إضافة خادم [FIX v2] حماية بمفتاح المسؤول
    # ═══════════════════════════════════════

    @app.post("/api/mcp/add-server")
    async def add_mcp_server(request: Request):
        """إضافة خادم MCP — يتطلب مفتاح المسؤول"""
        if not _admin_key:
            raise HTTPException(status_code=403, detail="ADAM_ADMIN_KEY not configured — MCP additions disabled")

        # [FIX v2] التحقق من مفتاح المسؤول
        admin_auth = request.headers.get("X-Admin-Key", "")
        if not _hmac.compare_digest(admin_auth.encode(), _admin_key.encode()):
            logger.warning(f"MCP add-server attempt with invalid admin key from {request.client.host if request.client else 'unknown'}")
            raise HTTPException(status_code=403, detail="Invalid admin key — X-Admin-Key header required")

        if not engine or not engine.tools:
            raise HTTPException(status_code=503, detail="مدير الأدوات غير متصل")

        try:
            body = await request.json()
            name = body.get("name", "")
            command = body.get("command", "")
            args = body.get("args", [])
            env = body.get("env")

            if not name or not command:
                raise HTTPException(status_code=400, detail="name و command مطلوبين")

            await engine.tools.add_mcp_server(name, command, args, env)
            return {"status": "ok", "message": f"خادم MCP '{name}' تمت إضافته"}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/mcp/tools")
    async def list_mcp_tools():
        """عرض أدوات MCP المتاحة"""
        if engine and engine.tools:
            return {"tools": engine.tools.get_mcp_tools()}
        return {"tools": []}

    # ═══════════════════════════════════════
    # Notebook
    # ═══════════════════════════════════════

    @app.get("/api/notebook/{date}")
    async def get_notebook(date: str):
        """قراءة صفحة النوت بوك لتاريخ معين"""
        if not engine or not engine.notebook:
            raise HTTPException(status_code=503, detail="النوت بوك غير متاح")
        try:
            content = engine.notebook.read_section(f"daily/{date}")
            return {"date": date, "content": content}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/notebook/profile")
    async def update_notebook_profile(request: Request):
        """تحديث ملف المستخدم في النوت بوك"""
        if not engine or not engine.notebook:
            raise HTTPException(status_code=503, detail="النوت بوك غير متاح")
        try:
            body = await request.json()
            engine.notebook.update_user_profile(body)
            return {"status": "ok"}
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ═══════════════════════════════════════
    # Diagnostics
    # ═══════════════════════════════════════

    @app.get("/api/diagnostics")
    async def get_diagnostics():
        """فحص شامل لكل المكونات"""
        if not engine:
            return {"status": "engine_not_attached"}

        diag = {
            "status": "running",
            "cycle_count": engine.cycle_count,
            "model": engine.model_name,
            "inference_mode": engine.inference_mode,
            "session_id": engine.session_id,
            "subsystems": {},
            "security": {},
        }

        # فحص كل موديول
        for name in ["memory", "ethics", "security", "notebook", "knowledge",
                      "eyes", "tools", "pipeline", "scheduler", "plugins",
                      "subagents", "trace_recorder", "meta_learner",
                      "continuous_learner", "platform_discord"]:
            obj = getattr(engine, name, None)
            diag["subsystems"][name] = obj is not None and not isinstance(obj, type(None))

        # معلومات الأمان
        if hasattr(engine, 'security_guard'):
            diag["security"] = engine.security_guard.get_stats()

        # معلومات البنية التحتية
        if hasattr(engine, 'metrics'):
            diag["metrics"] = engine.metrics.dump()
        if hasattr(engine, 'cache'):
            diag["cache"] = engine.cache.stats()

        return diag

    # ═══════════════════════════════════════
    # Security Stats
    # ═══════════════════════════════════════

    @app.get("/api/security/stats")
    async def get_security_stats():
        """إحصائيات الأمان"""
        if not engine or not hasattr(engine, 'security_guard'):
            return {"error": "security not available"}
        return engine.security_guard.get_stats()

    @app.get("/api/security/audit")
    async def get_audit_log(limit: int = 50):
        """سجل التدقيق الأمني"""
        if not engine or not hasattr(engine, 'security_guard'):
            return {"entries": []}
        return {"entries": engine.security_guard.get_audit_log(limit)}

    # ═══════════════════════════════════════
    # Memory Routes
    # ═══════════════════════════════════════

    @app.get("/api/memory/stats")
    async def get_memory_stats():
        """إحصائيات الذاكرة"""
        if engine and hasattr(engine, 'memory'):
            try:
                if hasattr(engine.memory, 'stats'):
                    return engine.memory.stats()
            except Exception:
                pass
        return {"status": "unavailable"}

    @app.post("/api/memory/store")
    async def store_memory(request: Request):
        """تخزين ذكرى جديد"""
        if not engine:
            raise HTTPException(status_code=503, detail="المحرك غير متصل")
        try:
            body = await request.json()
            content = body.get("content", "")
            tags = body.get("tags", "")
            if not content:
                raise HTTPException(status_code=400, detail="content مطلوب")
            # [FIX v2] تحديد طول المحتوى
            if len(content) > 5000:
                raise HTTPException(status_code=400, detail="المحتوى طويل جداً (الحد: 5000 حرف)")
            from adam.memory import store as memory_store
            mem_id = memory_store.store(content, tags)
            return {"status": "ok", "id": mem_id}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/memory/search")
    async def search_memory(request: Request):
        """البحث في الذاكرة"""
        if not engine:
            raise HTTPException(status_code=503, detail="المحرك غير متصل")
        try:
            body = await request.json()
            query = body.get("query", "")
            limit = body.get("limit", 10)
            if not query:
                raise HTTPException(status_code=400, detail="query مطلوب")
            from adam.memory import store as memory_store
            results = memory_store.search(query, limit)
            return {"results": results, "count": len(results)}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/memory/reflect")
    async def reflect_memory(request: Request):
        """تأمل في الذكريات"""
        if not engine:
            raise HTTPException(status_code=503, detail="المحرك غير متصل")
        try:
            body = await request.json()
            days = body.get("days", 1)
            from adam.memory import store as memory_store
            return memory_store.reflect(days)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ═══════════════════════════════════════
    # Skills
    # ═══════════════════════════════════════

    @app.get("/api/skills")
    async def list_skills():
        """عرض المهارات المتاحة"""
        if engine and hasattr(engine, 'skills'):
            try:
                return {"skills": engine.skills.list_skills()}
            except Exception:
                pass
        return {"skills": []}

    # ═══════════════════════════════════════
    # Scheduler
    # ═══════════════════════════════════════

    @app.get("/api/scheduler/jobs")
    async def list_scheduled_jobs():
        if not engine or not engine.scheduler:
            return {"jobs": []}
        return {"jobs": engine.scheduler.list_jobs()}

    @app.post("/api/scheduler/interval")
    async def add_interval_job(req: dict):
        if not engine or not engine.scheduler:
            raise HTTPException(status_code=503, detail="Scheduler غير متاح")
        job_id = req.get("id", "")
        seconds = req.get("seconds", 0)
        action = req.get("action", "")
        name = req.get("name", "")
        if not job_id or not seconds or not action:
            raise HTTPException(status_code=400, detail="id, seconds, action مطلوبين")
        async def _run():
            await engine.execute_action({"type": action, **req.get("params", {})})
        engine.scheduler.add_interval(job_id, seconds, _run, name=name or job_id)
        return {"status": "ok", "job_id": job_id}

    @app.post("/api/scheduler/once")
    async def add_once_job(req: dict):
        if not engine or not engine.scheduler:
            raise HTTPException(status_code=503, detail="Scheduler غير متاح")
        job_id = req.get("id", "")
        run_at = req.get("run_at", "")
        action = req.get("action", "")
        name = req.get("name", "")
        if not job_id or not run_at or not action:
            raise HTTPException(status_code=400, detail="id, run_at, action مطلوبين")
        from datetime import datetime
        run_dt = datetime.fromisoformat(run_at)
        async def _run():
            await engine.execute_action({"type": action, **req.get("params", {})})
        engine.scheduler.add_once(job_id, run_dt, _run, name=name or job_id)
        return {"status": "ok", "job_id": job_id}

    @app.delete("/api/scheduler/jobs/{job_id}")
    async def remove_scheduled_job(job_id: str):
        if not engine or not engine.scheduler:
            raise HTTPException(status_code=503, detail="Scheduler غير متاح")
        ok = engine.scheduler.remove(job_id)
        if not ok:
            raise HTTPException(status_code=404, detail="المهمة مش موجودة")
        return {"status": "removed", "job_id": job_id}

    # ─── Plugin Routes ───────────────────────────────────
    @app.get("/api/plugins")
    async def list_plugins():
        if not engine or not engine.plugins:
            return {"plugins": []}
        return {"plugins": engine.plugins.list_plugins()}

    @app.post("/api/plugins/load")
    async def load_plugin(req: dict):
        if not engine or not engine.plugins:
            raise HTTPException(status_code=503, detail="Plugin system غير متاح")
        path = req.get("path", "")
        if not path:
            raise HTTPException(status_code=400, detail="path مطلوب")
        engine.plugins.load_from_dir(path)
        return {"status": "ok", "plugins": engine.plugins.list_plugins()}

    @app.delete("/api/plugins/{plugin_name}")
    async def unload_plugin(plugin_name: str):
        if not engine or not engine.plugins:
            raise HTTPException(status_code=503, detail="Plugin system غير متاح")
        ok = await engine.plugins.unload(plugin_name)
        if not ok:
            raise HTTPException(status_code=404, detail="Plugin مش موجود")
        return {"status": "removed", "plugin": plugin_name}

    # ─── Subagent Routes ────────────────────────────────
    @app.get("/api/subagents")
    async def list_subagents():
        if not engine or not engine.subagents:
            return {"subagents": []}
        return {"subagents": engine.subagents.list_sessions()}

    @app.post("/api/subagents/spawn")
    async def spawn_subagent(req: dict):
        if not engine or not engine.subagents:
            raise HTTPException(status_code=503, detail="Subagent system غير متاح")
        name = req.get("name", "subagent")
        config = req.get("config", {})
        try:
            session = engine.subagents.spawn(name=name, config=config)
            return {"status": "spawned", "subagent": session.get_status()}
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

    @app.post("/api/subagents/{subagent_id}/chat")
    async def chat_subagent(subagent_id: str, req: dict):
        if not engine or not engine.subagents:
            raise HTTPException(status_code=503, detail="Subagent system غير متاح")
        session = engine.subagents.get(subagent_id)
        if not session:
            raise HTTPException(status_code=404, detail="Subagent مش موجود")
        message = req.get("message", "")
        if not message:
            raise HTTPException(status_code=400, detail="message مطلوب")
        result = await session.chat(message)
        return result

    @app.delete("/api/subagents/{subagent_id}")
    async def remove_subagent(subagent_id: str):
        if not engine or not engine.subagents:
            raise HTTPException(status_code=503, detail="Subagent system غير متاح")
        ok = engine.subagents.remove(subagent_id)
        if not ok:
            raise HTTPException(status_code=404, detail="Subagent مش موجود")
        return {"status": "removed", "subagent_id": subagent_id}

    # ─── Platform Routes ────────────────────────────────
    @app.get("/api/channels")
    async def list_channels():
        if channel_manager:
            return {"channels": channel_manager.list_channels()}
        return {"channels": []}

    # ─── WebSocket ──────────────────────────────────────
    # [FIX] WebSocket authentication — التحقق من token
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        # [FIX] التحقق من المصادقة عبر query parameter
        token = websocket.query_params.get("token", "")
        expected_token = _api_key
        if not token or not _hmac.compare_digest(token.encode(), expected_token.encode()):
            await websocket.close(code=4001, reason="Unauthorized — provide token query parameter")
            return

        await websocket.accept()
        logger.info("WebSocket connected (authenticated)")

        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                except json.JSONDecodeError:
                    await websocket.send_json({"error": "Invalid JSON"})
                    continue

                if not engine:
                    await websocket.send_json({"error": "المحرك غير متصل"})
                    continue

                message = msg.get("message", "")
                ctx = msg.get("context", {})
                if not message:
                    await websocket.send_json({"error": "مفيش رسالة"})
                    continue

                # [FIX v2] تحديد طول رسالة WebSocket
                if len(message) > 10000:
                    await websocket.send_json({"error": "الرسالة طويلة جداً (الحد: 10000 حرف)"})
                    continue

                result = await engine.chat(message, ctx or {})
                await websocket.send_json(result)

        except WebSocketDisconnect:
            logger.info("WebSocket disconnected")
        except Exception as e:
            logger.error(f"WebSocket error: {e}")
            try:
                await websocket.close(code=1011, reason=str(e))
            except Exception:
                pass

    # ─── Voice Pipeline ─────────────────────────────────
    _voice_pipeline: Optional[VoicePipeline] = None

    def get_voice_pipeline() -> VoicePipeline:
        nonlocal _voice_pipeline
        if _voice_pipeline is None:
            _voice_pipeline = VoicePipeline()
        return _voice_pipeline

    @app.get("/api/voice/audio/{filename}")
    async def get_audio(filename: str):
        """خدمة ملفات الصوت"""
        import os as _oso
        _audio_dir = _oso.path.join(_oso.path.dirname(_oso.path.dirname(__file__)), "audio_output")
        filepath = _oso.path.join(_audio_dir, filename)

        # [FIX] منع traversal attack — التأكد إن الملف جوه المجلد
        real_dir = _oso.path.realpath(_audio_dir)
        real_file = _oso.path.realpath(filepath)
        if not real_file.startswith(real_dir):
            raise HTTPException(status_code=403, detail="مسار غير مصرح به")

        # [FIX v2] منع أسماء الملفات الخطرة
        if ".." in filename or filename.startswith("/"):
            raise HTTPException(status_code=403, detail="اسم ملف غير صالح")

        if not _oso.path.exists(filepath):
            raise HTTPException(status_code=404, detail="الملف مش موجود")
        from fastapi.responses import FileResponse
        return FileResponse(filepath, media_type="audio/mpeg")

    @app.post("/api/voice/synthesize")
    async def synthesize_voice(req: dict):
        """تحويل نص لكلام"""
        text = req.get("text", "")
        lang = req.get("lang", "ar")
        if not text:
            raise HTTPException(400, "النص مطلوب")
        # [FIX v2] تحديد طول النص
        if len(text) > 5000:
            raise HTTPException(400, "النص طويل جداً (الحد: 5000 حرف)")
        try:
            pipeline = get_voice_pipeline()
            if not pipeline.tts.available:
                await pipeline.load_tts()
            if not pipeline.tts.available:
                raise HTTPException(503, "TTS مش متاح")
            synthesis = await pipeline.process_text(text, lang)
            if synthesis.audio:
                filename = f"synth_{int(datetime.now().timestamp())}.mp3"
                audio_path = await pipeline.save_audio(synthesis.audio, filename)
                return {"success": True, "audio_url": f"/api/voice/audio/{filename}"}
            return {"success": False, "error": "فشل التوليد"}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(500, f"فشل تحويل الصوت: {e}")

    # ─── Start/Stop ─────────────────────────────────────
    @app.on_event("startup")
    async def on_startup():
        global _start_time
        _start_time = datetime.now()
        logger.info("Adam Prism API started")

    @app.on_event("shutdown")
    async def on_shutdown():
        if channel_manager:
            try:
                await channel_manager.shutdown()
            except Exception:
                pass
        logger.info("Adam Prism API stopped")

    return app
