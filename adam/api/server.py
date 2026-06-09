"""
Adam Prism - API Server
=======================
خادم API يربط كل الموديولات ويوفر الواجهة للـ Web UI والـ Telegram.
يعمل على FastAPI مع WebSocket support.
"""

import json
import sqlite3
import logging
import asyncio
from datetime import datetime
from typing import Dict, Any, Optional, List

import httpx
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException, Request, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, HTMLResponse
from pydantic import BaseModel
from api.chat_store import ChatStore
from core.voice_pipeline import VoicePipeline, int16_to_float32, resample_audio
from core.permissions import log_permission

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

def create_app(engine=None, channel_manager=None) -> FastAPI:
    """إنشاء تطبيق FastAPI مع كل المسارات"""

    app = FastAPI(
        title="Adam Prism API",
        description="واجهة برمجة التطبيقات لآدم بريزم - التوأم الرقمي الشخصي",
        version="1.0.0"
    )

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
                logger.info(f"🌐 Mounted {len(routes)} channel webhook routes")
        except Exception as e:
            logger.warning(f"⚠️ Channel route mounting failed: {e}")
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
            logger.info("🌐 WebChat widget mounted at /chat/webhook and /chat/widget")
        except Exception:
            pass
    
    # CORS - السماح بالوصول من أي جهاز
    cors_origins = os.environ.get("CORS_ORIGINS", "*")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins.split(",") if cors_origins != "*" else ["*"],
        allow_credentials=cors_origins != "*",
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Serve static UI files
    import os as _os
    _static_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "web-ui", "public")
    if _os.path.isdir(_static_dir):
        try:
            from fastapi.staticfiles import StaticFiles
            app.mount("/ui", StaticFiles(directory=_static_dir, html=True), name="ui")
        except Exception as e:
            logger.warning(f"فشل تحميل الملفات الثابتة: {e}")
    
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
            from qdrant_client import QdrantClient
            qdrant = QdrantClient(host="localhost", port=6333)
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
            text = body.get("text", "").strip()
            collection = body.get("collection", "knowledge")
            # جمع الأسماء المتوقعة: knowledge → adam_knowledge (لتوافق MemorySystem)
            qdrant_collection = {"knowledge": "adam_knowledge", "conversations": "adam_conversations", "patterns": "adam_patterns"}.get(collection, collection)
            metadata = body.get("metadata", {})
            if not text:
                raise HTTPException(400, "النص مطلوب")
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            qdrant = QdrantClient(host="localhost", port=6333)
            cols = [c.name for c in qdrant.get_collections().collections]
            if qdrant_collection not in cols:
                qdrant.create_collection(qdrant_collection, vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE))
                logger.info(f"✅ Created new Qdrant collection: {qdrant_collection}")
            try:
                async with httpx.AsyncClient(timeout=30) as c:
                    resp = await c.post("http://localhost:11434/api/embeddings", json={"model": "nomic-embed-text", "prompt": text})
                    if resp.status_code == 200:
                        vec = resp.json().get("embedding", [])
                    else:
                        raise ValueError(f"Ollama embed returned {resp.status_code}")
            except Exception as e:
                raise HTTPException(503, f"تعذر الحصول على embedding (Ollama غير متصل؟): {e}")
            point_id = qdrant.count(qdrant_collection).count + 1
            qdrant.upsert(qdrant_collection, points=[models.PointStruct(id=point_id, vector=vec, payload={"text": text, **metadata})])
            return {"success": True, "collection": collection, "qdrant_collection": qdrant_collection, "id": point_id, "text_preview": text[:100]}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"فشل الإضافة: {e}")

    # ═══════════════════════════════════════
    # Upload File to Knowledge Base
    # ═══════════════════════════════════════

    @app.post("/api/knowledge/upload")
    async def upload_knowledge_file(
        file: UploadFile = File(...),
        collection: str = Form("knowledge"),
    ):
        """رفع ملف (PDF, DOCX, TXT, MD) إلى قاعدة المعرفة"""
        import os, tempfile, logging as log
        log = logger.getChild("upload")

        # Size limit (default 50MB)
        MAX_UPLOAD = 50 * 1024 * 1024
        content = await file.read()
        if len(content) > MAX_UPLOAD:
            raise HTTPException(413, f"الملف كبير جداً ({len(content)//1024//1024}MB). الحد 50MB.")

        # Validate extension
        ext = os.path.splitext(file.filename or "")[1].lower()
        if ext not in (".pdf", ".docx", ".txt", ".md"):
            raise HTTPException(400, f"الصيغة {ext} مش مدعومة. استخدم PDF, DOCX, TXT, MD")

        # Save temp file
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=ext)
        try:
            tmp.write(content)
            tmp.close()

            # Extract text
            text = ""
            if ext == ".pdf":
                import fitz
                doc = fitz.open(tmp.name)
                for page in doc:
                    text += page.get_text()
                doc.close()
            elif ext == ".docx":
                import docx
                d = docx.Document(tmp.name)
                text = "\n".join(p.text for p in d.paragraphs)
            elif ext in (".txt", ".md"):
                text = content.decode("utf-8", errors="replace")

            if not text.strip():
                raise HTTPException(400, "مفيش نص قابل للاستخراج من الملف")

            # Chunk large texts
            chunks = []
            if len(text) > 2000:
                words = text.split()
                chunk_size = 300
                for i in range(0, len(words), chunk_size):
                    chunks.append(" ".join(words[i:i+chunk_size]))
            else:
                chunks = [text]

            # Add to Qdrant — resolve collection name for MemorySystem compatibility
            qdrant_collection = {"knowledge": "adam_knowledge", "conversations": "adam_conversations", "patterns": "adam_patterns"}.get(collection, collection)
            from qdrant_client import QdrantClient
            from qdrant_client.http import models
            qdrant = QdrantClient(host="localhost", port=6333)
            cols = [c.name for c in qdrant.get_collections().collections]
            if qdrant_collection not in cols:
                qdrant.create_collection(qdrant_collection, vectors_config=models.VectorParams(size=768, distance=models.Distance.COSINE))

            async def embed_chunk(chunk: str) -> list:
                async with httpx.AsyncClient(timeout=30) as c:
                    resp = await c.post("http://localhost:11434/api/embeddings", json={"model": "nomic-embed-text", "prompt": chunk})
                    if resp.status_code == 200:
                        return resp.json().get("embedding", [])
                    raise ValueError(f"Ollama embed returned {resp.status_code}")

            ids = []
            base_id = qdrant.count(qdrant_collection).count + 1
            for i, chunk in enumerate(chunks):
                vec = await embed_chunk(chunk)
                if not vec:
                    continue
                point_id = base_id + i
                qdrant.upsert(qdrant_collection, points=[models.PointStruct(
                    id=point_id, vector=vec,
                    payload={"text": chunk, "source": file.filename, "chunk": i, "total_chunks": len(chunks)}
                )])
                ids.append(point_id)

            log.info(f"📄 Uploaded {file.filename} → {qdrant_collection} ({len(chunks)} chunks)")

            return {
                "success": True,
                "filename": file.filename,
                "collection": collection,
                "qdrant_collection": qdrant_collection,
                "chunks": len(chunks),
                "ids": [str(x) for x in ids],
                "total_chars": len(text),
            }

        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"فشل رفع الملف: {e}")
        finally:
            if os.path.exists(tmp.name):
                os.unlink(tmp.name)

    @app.get("/api/knowledge/recent")
    async def recent_knowledge(limit: int = 10):
        """آخر الإضافات لقاعدة المعرفة عبر scroll في كل المجموعات"""
        try:
            from qdrant_client import QdrantClient
            qdrant = QdrantClient(host="localhost", port=6333)
            recent = []
            for c in qdrant.get_collections().collections:
                try:
                    pts = qdrant.scroll(c.name, limit=5, with_payload=True, with_vectors=False)[0]
                    for pt in pts:
                        text = (pt.payload or {}).get("text", "")[:100]
                        recent.append({
                            "collection": c.name,
                            "text": text,
                            "id": str(pt.id),
                        })
                except Exception:
                    pass
            recent = recent[:limit]
            return {"recent": recent, "count": len(recent)}
        except Exception as e:
            raise HTTPException(status_code=503, detail=f"Qdrant غير متصل: {e}")
    
    @app.post("/api/pipeline/summarize")
    async def summarize_document(request: SummarizeRequest):
        """تلخيص مستند عبر LoRA server"""
        if not engine:
            raise HTTPException(status_code=503, detail="المحرك غير متصل")
        try:
            summary_prompt = f"لخص النص التالي بطريقة منظمة مختصرة:\n{request.text[:4000]}"
            async with httpx.AsyncClient(timeout=120) as c:
                resp = await c.post("http://localhost:8080/chat", json={
                    "messages": [{"role": "user", "content": summary_prompt}],
                    "max_tokens": 300
                })
                if resp.status_code == 200:
                    summary_text = resp.json().get("response", "")
                else:
                    summary_text = ""
            return {"master_summary": summary_text.strip(), "stats": {"input_chars": len(request.text)}}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=f"فشل التلخيص: {e}")
    
    @app.post("/api/tools/action")
    async def execute_action(request: ActionRequest):
        """تنفيذ فعل على الحاسوب"""
        if engine and engine.tools:
            action_dict = {"type": request.action, "params": request.params}
            result = await engine.tools.execute_action(action_dict)
            return result
        raise HTTPException(status_code=503, detail="أدوات الحاسوب غير متصلة")
    
    # ═══════════════════════════════════════
    # Permission System — صلاحيات المستخدم (Phase 1b)
    # ═══════════════════════════════════════

    class PermissionRequest(BaseModel):
        session_id: str = ""
        approve: bool = True
        level: Optional[str] = None  # "once", "session", "always"

    class PermissionStatusRequest(BaseModel):
        session_id: str

    @app.get("/api/permissions/pending/{session_id}")
    async def get_pending_permission(session_id: str):
        """الاستعلام عن طلب صلاحية معلّق"""
        if not engine or not hasattr(engine, 'permission'):
            raise HTTPException(status_code=503, detail="نظام الصلاحيات غير متصل")
        if engine.permission.pending_request:
            return {"pending": True, "request": engine.permission.pending_request}
        return {"pending": False, "request": None}

    @app.post("/api/permissions/respond")
    async def respond_permission(req: PermissionRequest):
        """الرد على طلب صلاحية معلّق"""
        if not engine or not hasattr(engine, 'permission'):
            raise HTTPException(status_code=503, detail="نظام الصلاحيات غير متصل")
        pending = engine.permission.pending_request
        if not pending:
            raise HTTPException(status_code=404, detail="لا يوجد طلب صلاحية معلّق")
        category = pending.get("category", "")
        level = req.level or pending.get("level", "once")
        if req.approve:
            engine.permission.grant(category, level)
            log_permission("granted", pending.get("tool", ""), category, pending.get("reason", ""), level, "granted")
            if hasattr(engine, 'learner'):
                engine.learner.record_decision(pending.get("tool", ""), category, "granted")
            return {"status": "granted", "category": category, "level": level}
        else:
            engine.permission.deny(category)
            log_permission("denied", pending.get("tool", ""), category, pending.get("reason", ""), level, "denied")
            if hasattr(engine, 'learner'):
                engine.learner.record_decision(pending.get("tool", ""), category, "denied")
            return {"status": "denied", "category": category}
    
    @app.get("/api/notebook/stats")
    async def get_notebook_stats():
        """إحصائيات النوته"""
        if engine and engine.notebook:
            method = getattr(engine.notebook, 'get_stats', None)
            if method:
                result = method()
                if result is None:
                    return {}
                return result
            return {}
        raise HTTPException(status_code=503, detail="النوته غير متصلة")
    
    @app.get("/api/notebook/{date}")
    async def get_notebook(date: str):
        """قراءة ملاحظات يوم معين"""
        if engine and engine.notebook:
            method = getattr(engine.notebook, 'get_daily_note', None)
            if method:
                result = method(date)
                if result is None:
                    return {"date": date, "content": ""}
                return {"date": date, "content": result}
            return {"date": date, "content": ""}
        raise HTTPException(status_code=503, detail="النوته غير متصلة")
    
    @app.get("/api/memory/stats")
    async def get_memory_stats():
        """إحصائيات الذاكرة"""
        if engine and engine.memory:
            return engine.memory.get_stats()
        raise HTTPException(status_code=503, detail="الذاكرة غير متصلة")

    @app.get("/api/metrics")
    async def get_metrics():
        """مؤشرات الأداء الداخلية"""
        if not engine:
            return {"error": "engine not available"}
        return engine.metrics.dump()
    
    @app.get("/api/engine/diagnostics")
    async def get_diagnostics():
        """تشخيص ذاتي للنظام — health check شامل"""
        if not engine:
            return {"error": "engine not available"}
        results = []
        checks = []
        checks.append(("Engine Status", engine.is_running if hasattr(engine, 'is_running') else True))
        checks.append(("Ollama Connected", engine.ollama_base is not None if hasattr(engine, 'ollama_base') else False))
        checks.append(("Memory System", engine.memory is not None if hasattr(engine, 'memory') else False))
        checks.append(("Ethics Gate", engine.ethics is not None if hasattr(engine, 'ethics') else False))
        checks.append(("Pipeline", engine.pipeline is not None if hasattr(engine, 'pipeline') else False))
        checks.append(("Tools", engine.tools is not None if hasattr(engine, 'tools') else False))
        checks.append(("Notebook", engine.notebook is not None if hasattr(engine, 'notebook') else False))
        checks.append(("Security", engine.security is not None if hasattr(engine, 'security') else False))
        checks.append(("Trace Recorder", engine.trace_recorder is not None if hasattr(engine, 'trace_recorder') else False))
        for name, ok in checks:
            results.append({"check": name, "status": "pass" if ok else "fail"})
        passed = sum(1 for r in results if r["status"] == "pass")
        failed = sum(1 for r in results if r["status"] == "fail")
        return {
            "status": "healthy" if failed == 0 else "degraded",
            "timestamp": datetime.now().isoformat(),
            "checks": results,
            "summary": {"passed": passed, "failed": failed, "total": len(results)},
        }

    class UpdateSettingsRequest(BaseModel):
        inference_mode: Optional[str] = None
        lora_server_url: Optional[str] = None
        model_name: Optional[str] = None

    @app.post("/api/settings/update")
    async def update_settings(req: UpdateSettingsRequest):
        """تحديث إعدادات المحرك في وقت التشغيل"""
        if not engine:
            raise HTTPException(status_code=503, detail="المحرك غير متصل")
        if req.inference_mode:
            engine.set_inference_mode(req.inference_mode, req.lora_server_url)
        if req.model_name:
            engine.model_name = req.model_name
        if req.lora_server_url and not req.inference_mode:
            engine.lora_server_url = req.lora_server_url
        return {
            "status": "updated",
            "inference_mode": engine.inference_mode,
            "model_name": engine.model_name,
            "lora_server_url": engine.lora_server_url,
        }

    @app.post("/api/engine/heal")
    async def heal_system():
        """تصليح ذاتي شامل — يكتشف ويعالج كل الموديولات المتعطلة"""
        if not engine:
            raise HTTPException(status_code=503, detail="المحرك غير متصل")

        actions = []
        subsystems = [
            ("ollama_base", "Ollama"),
            ("memory", "Memory"),
            ("ethics", "Ethics"),
            ("pipeline", "Pipeline"),
            ("tools", "Tools"),
            ("notebook", "Notebook"),
            ("security", "Security"),
            ("trace_recorder", "Trace Recorder"),
        ]
        for attr, name in subsystems:
            try:
                is_healthy = getattr(engine, attr, None) is not None
                if not is_healthy:
                    if hasattr(engine, '_heal_failed_subsystem'):
                        action = await engine._heal_failed_subsystem(attr)
                        if action:
                            actions.append(f"{name}: {action}")
                        else:
                            actions.append(f"{name}: فشل الإصلاح")
            except Exception as e:
                actions.append(f"{name}: خطأ — {e}")

        try:
            # Browser health check
            if engine.eyes and hasattr(engine.eyes, 'is_healthy'):
                try:
                    healthy = await asyncio.wait_for(engine.eyes.is_healthy(), timeout=10)
                    if not healthy:
                        await engine.eyes.restart()
                        actions.append("Browser: restarted")
                except asyncio.TimeoutError:
                    await engine.eyes.restart()
                    actions.append("Browser: restarted (timeout)")
        except Exception as e:
            actions.append(f"Browser: {e}")

        try:
            # تنظيف cache الذاكرة
            import gc
            before = gc.get_count()
            gc.collect()
            after = gc.get_count()
            actions.append(f"GC: {before}→{after}")
        except Exception as e:
            actions.append(f"GC: {e}")

        try:
            # إعادة تعيين pipeline logs لو متوقفة
            if hasattr(engine, 'get_pipeline_log'):
                log = engine.get_pipeline_log(1)
                if not log:
                    engine._pipeline_log = []
                    actions.append("Pipeline log reset")
        except Exception as e:
            actions.append(f"Pipeline: {e}")

        return {
            "status": "healed" if len(actions) > 0 else "no_action_needed",
            "timestamp": datetime.now().isoformat(),
            "actions_taken": actions,
        }

    # ─── Scheduler Routes ─────────────────────────────────
    @app.get("/api/scheduler/jobs")
    async def list_scheduled_jobs():
        if not engine or not engine.scheduler:
            raise HTTPException(status_code=503, detail="Scheduler غير متاح")
        return {"jobs": engine.scheduler.list_jobs()}

    @app.post("/api/scheduler/cron")
    async def add_cron_job(req: dict):
        if not engine or not engine.scheduler:
            raise HTTPException(status_code=503, detail="Scheduler غير متاح")
        job_id = req.get("id", "")
        cron = req.get("cron", "")
        action = req.get("action", "")
        name = req.get("name", "")
        if not job_id or not cron or not action:
            raise HTTPException(status_code=400, detail="id, cron, action مطلوبين")
        async def _run():
            await engine.execute_action({"type": action, **req.get("params", {})})
        engine.scheduler.add_cron(job_id, cron, _run, name=name or job_id)
        return {"status": "ok", "job_id": job_id}

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
        session = engine.subagents.spawn(name=name, config=config)
        return {"status": "spawned", "subagent": session.get_status()}

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
            return {"channels": channel_manager.get_status()}
        return {"channels": {}}

    @app.get("/api/channels/{name}")
    async def get_channel(name: str):
        if channel_manager and name in channel_manager.channels:
            return channel_manager.channels[name].get_status()
        raise HTTPException(status_code=404, detail=f"Channel '{name}' غير موجود")

    @app.post("/api/channels/{name}")
    async def toggle_channel(name: str, req: Request):
        data = await req.json()
        enabled = data.get("enabled", False)
        if channel_manager and name in channel_manager.channels:
            ch = channel_manager.channels[name]
            if enabled and not ch.running:
                ch.running = True
            elif not enabled and ch.running:
                ch.stop()
            return {"status": "ok", "running": ch.running}
        raise HTTPException(status_code=404, detail=f"Channel '{name}' غير موجود")

    @app.get("/api/platforms")
    async def list_platforms():
        if not engine:
            return {"platforms": {}}
        platforms = {}
        if engine.platform_discord:
            platforms["discord"] = engine.platform_discord.get_status()
        return {"platforms": platforms}

    @app.post("/api/platforms/discord/start")
    async def start_discord_bot():
        if not engine or not engine.platform_discord:
            raise HTTPException(status_code=503, detail="Discord bot غير متاح")
        ok = await engine.platform_discord.start()
        if not ok:
            raise HTTPException(status_code=500, detail="فشل تشغيل البوت — تأكد من token")
        return {"status": "started"}

    @app.post("/api/platforms/discord/stop")
    async def stop_discord_bot():
        if not engine or not engine.platform_discord:
            raise HTTPException(status_code=503, detail="Discord bot غير متاح")
        await engine.platform_discord.stop()
        return {"status": "stopped"}

    @app.get("/api/security/stats")
    async def get_security_stats():
        """إحصائيات الأمن"""
        if engine and engine.security:
            return engine.security.get_security_stats()
        raise HTTPException(status_code=503, detail="الأمن غير متصل")
    
    @app.get("/api/eyes/chat/{source}")
    async def list_chats(source: str):
        """قائمة المحادثات المتاحة من مصدر معين"""
        # سيتم التوسيع لاحقاً
        return {"source": source, "chats": []}
    
    # ═══════════════════════════════════════
    # Pipeline Log - سجل خطوات المعالجة
    # ═══════════════════════════════════════
    
    @app.get("/api/engine/pipeline-log")
    async def get_pipeline_log(limit: int = 50):
        """آخر خطوات المعالجة"""
        if not engine:
            return {"steps": []}
        return {"steps": engine.get_pipeline_log(limit)}
    
    # ═══════════════════════════════════════
    # SSE - بث مباشر لحالة المعالجة
    # ═══════════════════════════════════════
    
    @app.get("/api/engine/stream")
    async def stream_engine_status(request: Request):
        """بث مباشر لتحديثات المحرك عبر Server-Sent Events"""
        if not engine:
            return {"error": "engine not available"}
        
        queue: asyncio.Queue = asyncio.Queue()
        
        async def step_callback(step_info):
            await queue.put(step_info)
        
        engine.on_step(step_callback)
        
        async def event_generator():
            try:
                while True:
                    if await request.is_disconnected():
                        break
                    try:
                        step = await asyncio.wait_for(queue.get(), timeout=10.0)
                        yield f"data: {json.dumps(step, ensure_ascii=False)}\n\n"
                    except asyncio.TimeoutError:
                        yield f"data: {json.dumps({'type': 'keepalive', 'timestamp': datetime.now().isoformat()}, ensure_ascii=False)}\n\n"
            finally:
                pass
        
        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",
            }
        )
    
    # ═══════════════════════════════════════
    # System Health - صحة النظام
    # ═══════════════════════════════════════
    
    @app.get("/api/engine/health")
    async def get_system_health():
        """مؤشرات صحة النظام"""
        import os
        health = {
            "api": "running",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": (datetime.now() - _start_time).total_seconds() if _start_time else None,
            "engine": {
                "session_id": engine.session_id if engine else None,
                "model": engine.model_name if engine else None,
                "inference_mode": engine.inference_mode if engine else None,
                "active_mode": engine.active_mode if engine else None,
                "cycle_count": engine.cycle_count if engine else 0,
                "conversation_length": len(engine.conversation_history) if engine else 0,
                "tools_available": engine.tools is not None if engine else False,
                "eyes_available": engine.eyes is not None if engine else False,
            },
            "system": {
                "cpu_percent": None,
                "memory_percent": None,
            }
        }
        # Tool usage stats
        if engine and engine.tools:
            actions = engine.tools.action_log if hasattr(engine.tools, 'action_log') else []
            success_count = sum(1 for a in actions if a.get("success"))
            total_count = len(actions)
            health["engine"]["tool_actions_total"] = total_count
            health["engine"]["tool_actions_ok"] = success_count
            health["engine"]["tool_actions_fail"] = total_count - success_count
        # Trace recorder stats
        if engine and engine.trace_recorder:
            stats = engine.trace_recorder.get_stats()
            health["trace_recorder"] = stats
        try:
            import psutil
            health["system"]["cpu_percent"] = psutil.cpu_percent(interval=0.5)
            health["system"]["memory_percent"] = psutil.virtual_memory().percent
        except ImportError:
            pass
        
        # Ollama health
        if engine:
            try:
                client = await engine.shared_clients.get("ollama", engine.ollama_base, timeout=3.0)
                r = await client.get("/api/tags")
                if r.status_code == 200:
                    data = r.json()
                    health["ollama"] = {
                        "connected": True,
                        "models": [m["name"] for m in data.get("models", [])]
                    }
                else:
                    health["ollama"] = {"connected": False}
            except Exception:
                health["ollama"] = {"connected": False}
        
        # Qdrant health
        if engine:
            try:
                client = await engine.shared_clients.get("qdrant", engine.config.get("qdrant_url", "http://localhost:6333"), timeout=3.0)
                r = await client.get("/")
                health["qdrant"] = {"connected": r.status_code == 200}
            except Exception:
                health["qdrant"] = {"connected": False}
        
        return health
    
    # ═══════════════════════════════════════
    # Voice Pipeline - endpoints الصوت
    # ═══════════════════════════════════════

    _voice_pipeline: Optional[VoicePipeline] = None

    def get_voice_pipeline() -> VoicePipeline:
        nonlocal _voice_pipeline
        if _voice_pipeline is None:
            eng_config = engine.config if engine and hasattr(engine, 'config') and engine.config else {}
            tts_backend = eng_config.get("tts_backend", "edge_tts")
            tts_dialect = eng_config.get("tts_dialect", "eg")
            tts_voice = eng_config.get("tts_voice", "ar-EG-ShakirNeural")
            _voice_pipeline = VoicePipeline(tts_backend=tts_backend, tts_dialect=tts_dialect, tts_voice=tts_voice)
        return _voice_pipeline

    @app.post("/api/voice/transcribe")
    async def transcribe_audio(request: Request):
        """نسخ صوت إلى نص — يستقبل multipart/form-data مع حقل audio"""
        try:
            form = await request.form()
            audio_file = form.get("audio")
            if not audio_file:
                raise HTTPException(status_code=400, detail="الملف الصوتي مطلوب")

            audio_bytes = await audio_file.read()
            pipeline = get_voice_pipeline()

            # تحميل VAD + ASR إذا لزم
            if not pipeline.vad.available:
                await pipeline.load_vad()
            if not pipeline.asr.available:
                await pipeline.load_asr()

            result = await pipeline.process_audio(audio_bytes, sample_rate=16000)
            return {"text": result.text, "duration": result.duration_seconds}
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"فشل نسخ الصوت: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.post("/api/voice/chat")
    async def voice_chat(request: Request):
        """صوت → نص → Gemma 4 → TTS → {text, audio}"""
        try:
            form = await request.form()
            audio_file = form.get("audio")
            if not audio_file:
                raise HTTPException(status_code=400, detail="الملف الصوتي مطلوب")

            audio_bytes = await audio_file.read()
            session_id = form.get("session_id")
            pipeline = get_voice_pipeline()

            # تحميل VAD + ASR
            if not pipeline.vad.available:
                await pipeline.load_vad()
            if not pipeline.asr.available:
                await pipeline.load_asr()

            # ASR
            transcript = await pipeline.process_audio(audio_bytes, sample_rate=16000)
            if not transcript.text.strip():
                return {"text": "", "audioUrl": None, "duration_ms": 0}

            # إرسال النص إلى المحرك
            if engine:
                result = await engine.chat(transcript.text)
                reply_text = result.get("response", "")
            else:
                reply_text = ""

            # TTS — تحميل فقط إذا كان هناك رد
            audio_url = None
            if reply_text.strip():
                if not pipeline.tts.available:
                    await pipeline.load_tts()
                synthesis = await pipeline.process_text(reply_text, transcript.language)
                if synthesis.audio:
                    filename = f"reply_{int(datetime.now().timestamp())}.mp3"
                    audio_path = await pipeline.save_audio(synthesis.audio, filename)
                    audio_url = f"/api/voice/audio/{filename}"

                # تفريغ TTS من VRAM بعد الانتهاء
                await pipeline.unload_tts()

            # تفريغ ASR من VRAM
            await pipeline.unload_asr()

            return {
                "text": reply_text,
                "audioUrl": audio_url,
                "duration_ms": transcript.duration_seconds * 1000,
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"فشل معالجة الصوت: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/voice/audio/{filename}")
    async def get_audio(filename: str):
        """إرجاع ملف صوتي مخزَّن"""
        from fastapi.responses import FileResponse
        from fastapi import Response
        import os as _os
        audio_dir = _os.path.join(_os.path.dirname(_os.path.dirname(__file__)), "temp", "audio")
        filepath = _os.path.join(audio_dir, filename)
        if not _os.path.isfile(filepath):
            raise HTTPException(status_code=404, detail="الملف غير موجود")
        ext = filename.rsplit(".", 1)[-1] if "." in filename else "mp3"
        media_map = {"mp3": "audio/mpeg", "wav": "audio/wav", "pcm": "audio/L16", "webm": "audio/webm"}
        media_type = media_map.get(ext, "audio/mpeg")
        # inline + CORS عشان المتصفح يشتغل الصوت
        resp = FileResponse(filepath, media_type=media_type, filename=filename, headers={
            "Content-Disposition": f'inline; filename="{filename}"',
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600",
        })
        return resp

    # ═══════════════════════════════════════
    # File Upload
    # ═══════════════════════════════════════

    @app.post("/api/chat/upload")
    async def upload_file(request: Request):
        """رفع ملف/صورة وإرجاع URL"""
        try:
            import os as _os
            form = await request.form()
            file = form.get("file")
            if not file:
                raise HTTPException(status_code=400, detail="الملف مطلوب")

            upload_dir = _os.path.join(
                _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))),
                "data", "uploads"
            )
            _os.makedirs(upload_dir, exist_ok=True)

            content = await file.read()
            original_name = file.filename or "file"
            timestamp = int(datetime.now().timestamp())
            safe_name = f"{timestamp}_{original_name.replace(' ', '_')}"
            filepath = _os.path.join(upload_dir, safe_name)

            with open(filepath, "wb") as f:
                f.write(content)

            return {
                "filename": safe_name,
                "original_name": original_name,
                "url": f"/api/uploads/{safe_name}",
                "content_type": file.content_type or "application/octet-stream",
                "size": len(content),
            }
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"فشل رفع الملف: {e}")
            raise HTTPException(status_code=500, detail=str(e))

    @app.get("/api/uploads/{filename}")
    async def get_upload(filename: str):
        """إرجاع ملف مرفوع"""
        from fastapi.responses import FileResponse
        import os as _os
        upload_dir = _os.path.join(
            _os.path.dirname(_os.path.dirname(_os.path.dirname(__file__))),
            "data", "uploads"
        )
        filepath = _os.path.join(upload_dir, filename)
        if not _os.path.isfile(filepath):
            raise HTTPException(status_code=404, detail="الملف غير موجود")
        return FileResponse(filepath, headers={
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=86400",
        })

    # ═══════════════════════════════════════
    # Ollama Model Selector
    # ═══════════════════════════════════════

    @app.get("/api/ollama/models")
    async def list_ollama_models():
        """جلب كل الموديلات المتاحة في Ollama"""
        try:
            ollama_url = "http://localhost:11434"
            if engine:
                ollama_url = getattr(engine, "ollama_url", ollama_url) or ollama_url
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(f"{ollama_url}/api/tags")
                if resp.status_code != 200:
                    return {"models": [], "error": "Ollama غير متصل"}
                data = resp.json()
                models = [m["name"] for m in data.get("models", [])]
                return {"models": models}
        except Exception as e:
            return {"models": [], "error": str(e)}

    @app.post("/api/ollama/select")
    async def select_ollama_model(request: Request):
        """تبديل الموديل النشط"""
        try:
            body = await request.json()
            model = body.get("model", "")
            if not model:
                raise HTTPException(400, "اسم الموديل مطلوب")
            if engine and engine.provider:
                # Switch inference mode to ollama
                engine.provider.set_mode("ollama")
                # Try to set the model on the Ollama provider if it supports it
                ollama_provider = engine.provider._providers.get("ollama")
                if ollama_provider:
                    ollama_provider.model = model
                logger.info(f"🔄 switched inference to Ollama model: {model}")
            return {"success": True, "model": model}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ═══════════════════════════════════════
    # Skills API
    # ═══════════════════════════════════════

    @app.get("/api/skills/list")
    async def list_skills():
        """جلب كل المهارات المتاحة"""
        try:
            from adam.skills.manager import SkillManager
            mgr = SkillManager(engine)
            paths = mgr.discover()
            skills = []
            for p in paths:
                skill = await mgr.load(p)
                if skill:
                    skills.append({
                        "name": skill.name or p.split("/")[-1].replace(".md", "").replace(".py", ""),
                        "description": skill.description or "",
                        "path": p,
                    })
            return {"skills": skills}
        except Exception as e:
            logger.warning(f"فشل تحميل المهارات: {e}")
            return {"skills": [], "error": str(e)}

    @app.post("/api/skills/load")
    async def load_skill(request: Request):
        """تحميل وتشغيل مهارة"""
        try:
            body = await request.json()
            path = body.get("path", "")
            if not path:
                raise HTTPException(400, "مسار المهارة مطلوب")
            from adam.skills.manager import SkillManager
            mgr = SkillManager(engine)
            skill = await mgr.load(path)
            if not skill:
                raise HTTPException(404, "المهارة مش موجودة")
            result = await skill.on_trigger("load", {"source": "api"})
            return {"success": True, "name": skill.name, "result": str(result)[:500]}
        except HTTPException:
            raise
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    # ═══════════════════════════════════════
    # WebSocket
    # ═══════════════════════════════════════
    
    @app.websocket("/ws/chat")
    async def websocket_chat(websocket: WebSocket):
        """محادثة مباشرة عبر WebSocket مع دعم الصوت"""
        await websocket.accept()
        
        try:
            while True:
                data = await websocket.receive_text()
                parsed = json.loads(data)
                message = parsed.get("message", "")
                voice_requested = parsed.get("voice", False)
                
                if engine:
                    result = await engine.chat(message)
                    
                    # Voice synthesis إذا طلب صوت
                    if voice_requested and result.get("response"):
                        try:
                            pipeline = get_voice_pipeline()
                            reply_text = result["response"]
                            if not pipeline.tts.available:
                                await pipeline.load_tts()
                            if pipeline.tts.available:
                                synthesis = await pipeline.process_text(reply_text, "ar")
                                if synthesis.audio:
                                    filename = f"reply_{int(datetime.now().timestamp())}.mp3"
                                    audio_path = await pipeline.save_audio(synthesis.audio, filename)
                                    result["audio_url"] = f"/api/voice/audio/{filename}"
                                await pipeline.unload_tts()
                        except Exception as e:
                            logger.warning(f"فشل توليد الصوت عبر WS: {e}")
                    
                    await websocket.send_json(result)
                else:
                    await websocket.send_json({"error": "المحرك غير متصل"})
                    
        except WebSocketDisconnect:
            logger.info("تم قطع اتصال WebSocket")
        except Exception as e:
            logger.error(f"خطأ WebSocket: {e}")
    
    return app


# ═══════════════════════════════════════
# Standalone runner
# ═══════════════════════════════════════

def run_server(engine=None, host: str = "0.0.0.0", port: int = 8000, channel_config: Optional[dict] = None):
    """تشغيل الخادم مع القنوات الاختيارية"""
    import uvicorn
    channel_manager = None
    if channel_config:
        try:
            from adam.channels.manager import ChannelManager
            channel_manager = ChannelManager(channel_config)
            import asyncio
            try:
                loop = asyncio.get_running_loop()
                loop.create_task(channel_manager.start_all(engine))
            except RuntimeError:
                asyncio.run(channel_manager.start_all(engine))
            logger.info(f"✅ Channels: {list(channel_manager.channels.keys())}")
        except Exception as e:
            logger.warning(f"⚠️ Channel init skipped: {e}")
    app = create_app(engine, channel_manager)
    uvicorn.run(app, host=host, port=port)
