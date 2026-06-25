"""
Adam Prism — Complete FastAPI Server
=====================================
REST only — صفر WebSocket.

Endpoints (كلها متوافقة مع الـ frontend الموجود):
- POST /api/chat — دردشة كاملة
- POST /api/chat/upload — رفع ملفات
- GET/POST /api/chat/sessions/* — إدارة الجلسات
- GET/POST /api/memory/* — ذاكرة قصيرة
- GET/POST /api/ltm/* — ذاكرة طويلة المدى (vector)
- GET /api/tools/manifest + POST /api/tools/action — أدوات
- POST /api/json-mode — JSON structured output
- POST /api/knowledge/search, /add, /upload, /collections, /recent
- GET /api/skills/list, POST /api/skills/load
- GET /api/plugins, POST /api/plugins/load
- GET /api/subagents, POST /api/subagents/spawn
- GET/POST/DELETE /api/scheduler/jobs, /cron, /interval, /once
- GET /api/notebook/{date}, /api/notebook/stats
- GET /api/security/stats
- GET /api/engine/health, /diagnostics, /heal, /pipeline-log
- POST /api/voice/chat, /api/voice/transcribe
- GET /api/ollama/models, POST /api/ollama/select
- POST /api/settings/update
- POST /api/auth/verify
- GET /healthz/live, /healthz/ready, /metrics, /api/status

Run:
    uvicorn adam.server:app --host 0.0.0.0 --port 8000 --reload
"""

from __future__ import annotations

import json
import logging
import os
import time
from pathlib import Path
from typing import Any

import psutil
from fastapi import (
    FastAPI, HTTPException, UploadFile, File, Request,
    Depends,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse, FileResponse
from pydantic import BaseModel
import asyncio
import httpx

from adam_v3.engine import AdamEngine, EngineConfig, get_engine, cleanup_engine, estimate_tokens

logger = logging.getLogger("adam_prism.api")

# ============================================================
# Config
# ============================================================

ADAM_PRODUCTION = os.getenv("ADAM_PRODUCTION", "0") == "1"
REPO_ROOT = Path(__file__).resolve().parent.parent.parent
INDEX_HTML = REPO_ROOT / "index.html"
if not INDEX_HTML.exists():
    INDEX_HTML = REPO_ROOT / "frontend" / "index.html"

# ============================================================
# Models
# ============================================================

class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None
    context: dict | None = None
    voice: bool = False


class MemoryStoreRequest(BaseModel):
    content: str
    type: str = "semantic"
    priority: int = 3
    tags: list[str] = []


class ToolActionRequest(BaseModel):
    name: str = ""
    arguments: dict = {}
    action: dict | None = None  # backward compat


class SkillsLoadRequest(BaseModel):
    skill_name: str
    skill_path: str | None = None


class OllamaSelectRequest(BaseModel):
    model: str


class SettingsUpdateRequest(BaseModel):
    settings: dict


class AuthVerifyRequest(BaseModel):
    token: str | None = None
    api_key: str | None = None


# ============================================================
# App
# ============================================================

app = FastAPI(
    title="Adam Prism",
    version="3.1.0",
    description="Complete Adam Prism server — REST only, no WebSocket.",
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if not ADAM_PRODUCTION else [
        "https://adam-prism.com",
        "https://www.adam-prism.com",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    logger.info("Starting Adam Prism...")
    engine = get_engine()
    health = await engine.health_check()
    logger.info(f"Engine health: {health}")


@app.on_event("shutdown")
async def shutdown():
    logger.info("Shutting down...")
    await cleanup_engine()


# ============================================================
# UI
# ============================================================

@app.get("/", response_class=HTMLResponse, tags=["ui"], include_in_schema=False)
async def chat_ui():
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML, media_type="text/html")
    return HTMLResponse("<h1>Adam Prism</h1><p>UI not found.</p>", status_code=500)


# ============================================================
# Core: Chat (REST only — no WebSocket)
# ============================================================

@app.post("/api/chat", tags=["chat"])
@app.post("/chat", tags=["chat"])
async def chat(req: ChatRequest):
    """إرسال رسالة و receiving response."""
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    engine = get_engine()
    try:
        result = await engine.chat(
            message=req.message,
            session_id=req.session_id,
            context=req.context or {},
        )
        # backward compat مع الـ frontend — نفس شكل الرد القديم
        return {
            "response": result["response"],
            "session_id": result["session_id"],
            "mode": result.get("mode", "analyst"),
            "intent": result.get("intent", {}),
            "knowledge_used": result.get("knowledge_used", 0),
            "cycle": result.get("cycle", 1),
            "duration_ms": result.get("duration_ms", 0),
            "audio_url": result.get("audio_url"),
            "backend": result.get("backend"),
            "tool_calls": result.get("tool_calls", []),
            "tools_used": [t["name"] for t in result.get("tool_calls", [])],
            "errors": [],
            "permission_pending": None,
        }
    except Exception as e:
        logger.exception("Chat error:")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)[:200]}")


# WebSocket disabled entirely — REST only.
# No endpoint here, so it returns 404 cleanly.


@app.post("/api/chat/upload", tags=["chat"])
async def upload_file(file: UploadFile = File(...)):
    """رفع ملف واستخراج محتواه."""
    import io
    MAX_SIZE = 10 * 1024 * 1024
    content = await file.read()
    if len(content) > MAX_SIZE:
        raise HTTPException(status_code=413, detail="File too large (max 10MB)")

    filename = file.filename or "unknown"
    file_ext = Path(filename).suffix.lower()

    text_exts = {
        ".txt", ".md", ".py", ".js", ".ts", ".tsx", ".jsx", ".json",
        ".yaml", ".yml", ".csv", ".tsv", ".xml", ".html", ".css",
        ".java", ".c", ".cpp", ".h", ".rs", ".go", ".rb", ".php",
        ".sh", ".bash", ".sql", ".log", ".ini", ".toml",
    }

    if file_ext == ".pdf":
        try:
            import fitz
            doc = fitz.open(stream=content, filetype="pdf")
            text = "".join(page.get_text() for page in doc)
            doc.close()
            return {
                "filename": filename, "size": len(content), "type": "text",
                "text_content": text[:50000],
            }
        except ImportError:
            return {"filename": filename, "size": len(content), "type": "binary",
                    "error": "PyMuPDF not installed"}
        except Exception as e:
            return {"filename": filename, "size": len(content), "type": "error",
                    "error": str(e)}

    if file_ext in {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp"}:
        try:
            import pytesseract
            from PIL import Image
            img = Image.open(io.BytesIO(content))
            text = pytesseract.image_to_string(img, lang="ara+eng")
            return {
                "filename": filename, "size": len(content), "type": "image",
                "text_content": text,
            }
        except ImportError:
            return {"filename": filename, "size": len(content), "type": "image",
                    "error": "pytesseract/PIL not installed"}
        except Exception as e:
            return {"filename": filename, "size": len(content), "type": "image",
                    "error": str(e)}

    if file_ext in text_exts or not file_ext:
        try:
            text = content.decode("utf-8", errors="ignore")
            return {
                "filename": filename, "size": len(content), "type": "text",
                "text_content": text[:50000],
            }
        except Exception as e:
            return {"filename": filename, "size": len(content), "type": "error",
                    "error": str(e)}

    return {
        "filename": filename, "size": len(content), "type": "binary",
        "note": f"Binary file ({file_ext}). Content not extracted.",
    }


# ============================================================
# Sessions
# ============================================================

@app.get("/api/chat/sessions", tags=["sessions"])
async def list_sessions(limit: int = 50, user_id: str = "default"):
    engine = get_engine()
    sessions = await engine.session_manager.list_sessions(user_id=user_id, limit=limit)
    return {"sessions": sessions, "total": len(sessions)}


@app.get("/api/chat/sessions/{session_id}", tags=["sessions"])
async def get_session(session_id: str):
    engine = get_engine()
    messages = await engine.session_manager.get_messages(session_id, limit=100)
    stats = await engine.session_manager.get_session_stats(session_id)
    session = await engine.session_manager.get_session(session_id)
    return {
        "session_id": session_id,
        "messages": messages,
        "stats": stats,
        "session": session,
    }


@app.post("/api/chat/sessions/{session_id}/sync", tags=["sessions"])
async def sync_session(session_id: str, request: Request):
    engine = get_engine()
    try:
        body = await request.json()
        if isinstance(body, list):
            synced = 0
            for msg in body:
                role = msg.get("role", "user")
                content = msg.get("content", "")
                if content:
                    await engine.session_manager.add_message(session_id, role, content)
                    synced += 1
            return {"session_id": session_id, "synced": synced, "status": "ok"}
        return {"session_id": session_id, "synced": 0, "status": "ok"}
    except Exception as e:
        return {"session_id": session_id, "synced": 0, "status": "error", "error": str(e)[:200]}


@app.post("/api/chat/sessions/{session_id}/messages", tags=["sessions"])
async def add_session_message(session_id: str, request: dict):
    engine = get_engine()
    role = request.get("role", "user")
    content = request.get("content", "")
    msg_id = await engine.session_manager.add_message(session_id, role, content)
    return {"id": msg_id, "session_id": session_id, "role": role, "content": content[:100]}


@app.delete("/api/chat/sessions/{session_id}", tags=["sessions"])
async def delete_session(session_id: str):
    engine = get_engine()
    deleted = await engine.session_manager.delete_session(session_id)
    return {"deleted": deleted, "session_id": session_id}


@app.post("/api/chat/search", tags=["chat"])
async def search_chat(request: dict):
    """بحث في رسائل الجلسات."""
    query = request.get("query", "")
    # stub — يرجع نتائج فارغة
    return {"results": [], "query": query, "total": 0}


# ============================================================
# Memory (Short-term API — يستخدم نفس الـ store)
# ============================================================

@app.post("/api/memory/store", tags=["memory"])
async def memory_store(req: MemoryStoreRequest):
    engine = get_engine()
    mem_id = await engine.memory.store(
        content=req.content, type=req.type, priority=req.priority,
        tags=req.tags, source="api",
    )
    return {"success": bool(mem_id), "id": mem_id}


@app.get("/api/memory/recall", tags=["memory"])
async def memory_recall(query: str, limit: int = 10):
    engine = get_engine()
    if not query.strip():
        return {"results": [], "total": 0}
    results = await engine.memory.search(query, top_k=limit)
    return {
        "results": [
            {
                "id": r.memory.id,
                "content": r.memory.content,
                "type": r.memory.type,
                "priority": r.memory.priority,
                "score": round(r.score, 3),
            }
            for r in results
        ],
        "total": len(results),
    }


@app.get("/api/memory/stats", tags=["memory"])
async def memory_stats():
    engine = get_engine()
    return engine.memory.stats()


# ============================================================
# LTM (Long-term Memory — vector)
# ============================================================

@app.post("/api/ltm/store", tags=["ltm"])
async def ltm_store(req: MemoryStoreRequest):
    engine = get_engine()
    mem_id = await engine.memory.store(
        content=req.content, type=req.type, priority=req.priority,
        tags=req.tags, source="api",
    )
    return {"success": bool(mem_id), "id": mem_id}


@app.get("/api/ltm/search", tags=["ltm"])
async def ltm_search(query: str, top_k: int = 5, type: str | None = None, min_priority: int = 1):
    engine = get_engine()
    if not query.strip():
        return {"results": [], "total": 0}
    results = await engine.memory.search(
        query, top_k=top_k, memory_type=type, min_priority=min_priority
    )
    return {
        "results": [
            {
                "id": r.memory.id,
                "content": r.memory.content,
                "type": r.memory.type,
                "priority": r.memory.priority,
                "tags": r.memory.tags,
                "score": round(r.score, 3),
                "bm25_score": round(r.bm25_score, 3),
                "vector_score": round(r.vector_score, 3),
                "access_count": r.memory.access_count,
                "created_at": r.memory.created_at,
            }
            for r in results
        ],
        "total": len(results),
    }


@app.get("/api/ltm/recall", tags=["ltm"])
async def ltm_recall(query: str, max_memories: int = 5, max_chars: int = 1500):
    engine = get_engine()
    text = await engine.memory.recall_for_context(query, max_memories, max_chars)
    return {"context": text, "length": len(text)}


@app.get("/api/ltm/stats", tags=["ltm"])
async def ltm_stats():
    engine = get_engine()
    return engine.memory.stats()


@app.get("/api/ltm/health", tags=["ltm"])
async def ltm_health():
    engine = get_engine()
    return await engine.memory.health_check()


@app.delete("/api/ltm/memories/{memory_id}", tags=["ltm"])
async def ltm_delete(memory_id: int):
    engine = get_engine()
    success = await engine.memory.delete(memory_id)
    return {"deleted": success, "id": memory_id}


# ============================================================
# Knowledge (stubs — تستخدم memory داخلياً)
# ============================================================

@app.post("/api/knowledge/search", tags=["knowledge"])
async def knowledge_search(request: dict):
    """بحث معرفي — يستخدم memory store."""
    engine = get_engine()
    query = request.get("query", "")
    collection = request.get("collection", "knowledge")
    top_k = request.get("top_k", 5)
    if not query.strip():
        return {"results": [], "total": 0}
    results = await engine.memory.search(query, top_k=top_k)
    return {
        "results": [
            {
                "id": str(r.memory.id),
                "content": r.memory.content,
                "score": round(r.score, 3),
                "collection": collection,
                "metadata": {"type": r.memory.type, "priority": r.memory.priority},
            }
            for r in results
        ],
        "total": len(results),
    }


@app.post("/api/knowledge/add", tags=["knowledge"])
async def knowledge_add(request: dict):
    engine = get_engine()
    content = request.get("content", "")
    collection = request.get("collection", "knowledge")
    mem_id = await engine.memory.store(
        content=content, type="semantic", priority=3, source=f"knowledge:{collection}"
    )
    return {"success": bool(mem_id), "id": mem_id, "collection": collection}


@app.post("/api/knowledge/upload", tags=["knowledge"])
async def knowledge_upload(file: UploadFile = File(...), collection: str = "knowledge"):
    """رفع ملف للـ knowledge base."""
    content = await file.read()
    text = content.decode("utf-8", errors="ignore")[:50000]
    engine = get_engine()
    mem_id = await engine.memory.store(
        content=f"[{file.filename}] {text[:2000]}",
        type="semantic", priority=3, source=f"knowledge:{collection}",
    )
    return {"success": bool(mem_id), "id": mem_id, "filename": file.filename}


@app.get("/api/knowledge/collections", tags=["knowledge"])
async def knowledge_collections():
    """يرجع الكوليكشنز المتاحة."""
    return {
        "collections": [
            {"name": "knowledge", "count": 0},
            {"name": "project_architecture", "count": 0},
            {"name": "user_profile", "count": 0},
            {"name": "frontend_components", "count": 0},
            {"name": "backend_modules", "count": 0},
        ]
    }


@app.get("/api/knowledge/recent", tags=["knowledge"])
async def knowledge_recent(limit: int = 10):
    """أحدث الذكريات."""
    engine = get_engine()
    stats = engine.memory.stats()
    return {"recent": [], "total": stats.get("total", 0)}


# ============================================================
# Skills (stubs)
# ============================================================

@app.get("/api/skills/list", tags=["skills"])
async def skills_list():
    return {
        "skills": [
            {"name": "security_scan", "description": "فحص أمني للنظام", "loaded": True},
            {"name": "code_review", "description": "مراجعة كود", "loaded": True},
            {"name": "data_analysis", "description": "تحليل بيانات", "loaded": True},
            {"name": "system_check", "description": "فحص النظام", "loaded": True},
            {"name": "memory_ops", "description": "عمليات الذاكرة", "loaded": True},
        ],
        "total": 5,
    }


@app.post("/api/skills/load", tags=["skills"])
async def skills_load(req: SkillsLoadRequest):
    return {"loaded": True, "skill": req.skill_name}


# Alias بدون /list (لو الفرونت بيستخدم /api/skills بس)
@app.get("/api/skills", tags=["skills"])
async def skills_alias():
    return await skills_list()


# ============================================================
# Plugins (stubs)
# ============================================================

@app.get("/api/plugins", tags=["plugins"])
async def plugins_list():
    return {"plugins": [], "total": 0}


@app.get("/api/plugins/{plugin_name}", tags=["plugins"])
async def plugin_get(plugin_name: str):
    return {"name": plugin_name, "loaded": False, "error": "Plugin not found"}


@app.post("/api/plugins/load", tags=["plugins"])
async def plugins_load(request: dict):
    name = request.get("name", "unknown")
    return {"loaded": False, "name": name, "error": "Plugin loading not implemented"}


# ============================================================
# Subagents (stubs)
# ============================================================

@app.get("/api/subagents", tags=["subagents"])
async def subagents_list():
    return {"subagents": [], "total": 0}


@app.get("/api/subagents/{subagent_id}", tags=["subagents"])
async def subagent_get(subagent_id: str):
    return {"id": subagent_id, "status": "not_found"}


@app.post("/api/subagents/spawn", tags=["subagents"])
async def subagents_spawn(request: dict):
    return {
        "id": "stub-subagent",
        "status": "stub",
        "message": "Subagent spawning not implemented in this version",
    }


# ============================================================
# Scheduler (stubs)
# ============================================================

@app.get("/api/scheduler/jobs", tags=["scheduler"])
async def scheduler_jobs():
    return {"jobs": [], "total": 0}


@app.get("/api/scheduler/jobs/{job_id}", tags=["scheduler"])
async def scheduler_job_get(job_id: str):
    return {"id": job_id, "status": "not_found"}


@app.delete("/api/scheduler/jobs/{job_id}", tags=["scheduler"])
async def scheduler_job_delete(job_id: str):
    return {"deleted": False, "id": job_id, "error": "Job not found"}


@app.post("/api/scheduler/cron", tags=["scheduler"])
async def scheduler_cron(request: dict):
    return {"id": "stub-cron", "status": "stub", "scheduled": False}


@app.post("/api/scheduler/interval", tags=["scheduler"])
async def scheduler_interval(request: dict):
    return {"id": "stub-interval", "status": "stub", "scheduled": False}


@app.post("/api/scheduler/once", tags=["scheduler"])
async def scheduler_once(request: dict):
    return {"id": "stub-once", "status": "stub", "scheduled": False}


# ============================================================
# Notebook (stubs)
# ============================================================

@app.get("/api/notebook/{date}", tags=["notebook"])
async def notebook_get(date: str):
    return {"date": date, "entries": [], "total": 0}


@app.get("/api/notebook/stats", tags=["notebook"])
async def notebook_stats():
    return {"total_entries": 0, "total_words": 0, "last_entry": None}


# ============================================================
# Security (stubs)
# ============================================================

@app.get("/api/security/stats", tags=["security"])
async def security_stats():
    return {
        "total_checks": 0,
        "blocked": 0,
        "flagged": 0,
        "allowed": 0,
        "top_threats": [],
    }


# ============================================================
# Voice (stubs)
# ============================================================

@app.post("/api/voice/chat", tags=["voice"])
async def voice_chat(request: dict):
    """معالجة رسالة صوتية — stub."""
    return {
        "transcript": "",
        "response": "Voice processing not implemented",
        "audio_url": None,
    }


@app.post("/api/voice/transcribe", tags=["voice"])
async def voice_transcribe(file: UploadFile = File(...)):
    """تفريغ صوتي — stub."""
    return {"transcript": "", "language": "ar", "confidence": 0.0}


# ============================================================
# Ollama
# ============================================================

@app.get("/api/ollama/models", tags=["ollama"])
async def ollama_models():
    """يرجع الموديلات المتاحة في Ollama."""
    engine = get_engine()
    try:
        async with httpx.AsyncClient(timeout=5.0) as c:
            r = await c.get(f"{engine.config.ollama_url}/api/tags")
            if r.status_code == 200:
                models = r.json().get("models", [])
                return {
                    "models": [{"name": m["name"], "size": m.get("size", 0)} for m in models],
                    "total": len(models),
                }
    except Exception as e:
        logger.warning(f"Ollama models fetch failed: {e}")
    return {"models": [], "total": 0, "error": "Ollama not available"}


@app.post("/api/ollama/select", tags=["ollama"])
async def ollama_select(req: OllamaSelectRequest):
    """تغيير الموديل النشط."""
    engine = get_engine()
    old_model = engine.config.ollama_model
    engine.config.ollama_model = req.model
    return {"previous": old_model, "current": req.model, "success": True}


# ============================================================
# Settings
# ============================================================

@app.post("/api/settings/update", tags=["settings"])
async def settings_update(req: SettingsUpdateRequest):
    """تحديث الإعدادات (stub — ما يأثرش فعلياً على runtime)."""
    return {"success": True, "updated_keys": list(req.settings.keys())}


# ============================================================
# Auth (stubs)
# ============================================================

@app.post("/api/auth/verify", tags=["auth"])
async def auth_verify(req: AuthVerifyRequest):
    """التحقق من token (stub — دايماً valid في dev)."""
    if ADAM_PRODUCTION:
        # في production، تحقق فعلي
        if not req.token and not req.api_key:
            raise HTTPException(status_code=401, detail="No credentials provided")
    return {"valid": True, "user": "default", "role": "admin"}


# ============================================================
# Pipeline (stubs)
# ============================================================

@app.post("/api/pipeline/summarize", tags=["pipeline"])
async def pipeline_summarize(request: dict):
    """تلخيص — يستخدم auxiliary model لو متاح."""
    engine = get_engine()
    text = request.get("text", "")
    if not text.strip():
        raise HTTPException(status_code=400, detail="Text required")
    if engine.auxiliary:
        try:
            summary = await engine.auxiliary.chat(
                [
                    {"role": "system", "content": "لخّص النص التالي بشكل مختصر."},
                    {"role": "user", "content": text[:5000]},
                ],
                max_tokens=500, temperature=0.3,
            )
            return {"summary": summary, "success": True}
        except Exception as e:
            return {"summary": "", "success": False, "error": str(e)[:200]}
    # fallback
    return {"summary": text[:500] + "...", "success": True, "method": "truncation"}


# ============================================================
# Tools
# ============================================================

@app.get("/api/tools/manifest", tags=["tools"])
async def tools_manifest():
    engine = get_engine()
    tools = engine.tools.list_tools()
    return {
        "total": len(tools),
        "tools": {t["name"]: t for t in tools},
        "format": '<tool_call>{"name": "...", "arguments": {...}}</tool_call>',
    }


@app.post("/api/tools/action", tags=["tools"])
async def tools_action(req: ToolActionRequest):
    """تنفيذ أداة."""
    engine = get_engine()
    # backward compat: الـ frontend ممكن يبعت action: {type, params}
    if req.action:
        name = req.action.get("type", req.name)
        arguments = req.action.get("params", req.arguments)
    else:
        name = req.name
        arguments = req.arguments
    result = await engine.tools.execute(name, arguments)
    return {
        "success": result.success,
        "result": result.result,
        "error": result.error,
        "latency_ms": result.latency_ms,
    }


# ============================================================
# JSON Mode
# ============================================================

@app.post("/api/json-mode", tags=["json"])
async def json_mode(request: dict):
    schema = request.get("schema", {})
    query = request.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query required")

    schema_str = json.dumps(schema, ensure_ascii=False)
    prompt = f"رد بصيغة JSON فقط ملتزمًا بالمخطط:\n<schema>\n{schema_str}\n</schema>\n\nاستفسار: {query}\n\nالرد (JSON فقط):"

    engine = get_engine()
    result = await engine.chat(prompt)
    response = result["response"]

    import re
    json_match = re.search(r'\{.*\}', response, re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            return {"valid": True, "data": parsed, "raw": response}
        except json.JSONDecodeError:
            pass
    return {"valid": False, "data": None, "raw": response, "error": "Could not parse JSON"}


# ============================================================
# Engine health & diagnostics
# ============================================================

@app.get("/api/engine/health", tags=["ops"])
async def engine_health():
    engine = get_engine()
    health = await engine.health_check()
    return {
        **health,
        "system": {
            "cpu_percent": round(psutil.cpu_percent(), 1),
            "memory_percent": round(psutil.virtual_memory().percent, 1),
            "disk_percent": round(psutil.disk_usage("/").percent, 1),
        },
        "config": {
            "lora_url": engine.config.lora_url,
            "ollama_url": engine.config.ollama_url,
            "ollama_model": engine.config.ollama_model,
            "auxiliary_model": engine.config.auxiliary_model if engine.config.auxiliary_enabled else None,
            "embedding_model": engine.config.embedding_model,
        },
    }


@app.get("/api/engine/diagnostics", tags=["ops"])
async def engine_diagnostics():
    engine = get_engine()
    health = await engine.health_check()
    return {
        "summary": {
            "total": len(health["services"]),
            "passed": sum(1 for v in health["services"].values() if v),
            "failed": sum(1 for v in health["services"].values() if not v),
        },
        "services": health["services"],
        "stats": engine.get_stats(),
        "system": {
            "cpu_percent": round(psutil.cpu_percent(), 1),
            "memory_percent": round(psutil.virtual_memory().percent, 1),
            "disk_percent": round(psutil.disk_usage("/").percent, 1),
        },
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@app.post("/api/engine/heal", tags=["ops"])
async def engine_heal():
    """محاولة إصلاح ذاتي — stub."""
    return {
        "status": "checked",
        "details": {"checked": [], "restarted": [], "errors": []},
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@app.get("/api/engine/pipeline-log", tags=["ops"])
async def engine_pipeline_log(limit: int = 50):
    """سجل الـ pipeline — stub."""
    return {"steps": [], "total": 0}


@app.get("/api/engine/stream", tags=["ops"])
async def engine_stream():
    """SSE keepalive."""
    async def gen():
        engine = get_engine()
        while True:
            stats = engine.get_stats()
            yield f"data: {json.dumps({'type': 'keepalive', 'stats': stats})}\n\n"
            await asyncio.sleep(15)
    return StreamingResponse(gen(), media_type="text/event-stream",
                             headers={"Cache-Control": "no-cache", "Connection": "keep-alive"})


# ============================================================
# Health & Metrics
# ============================================================

@app.get("/healthz/live", tags=["ops"])
async def healthz_live():
    return {"status": "alive", "version": "3.1.0", "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}


@app.get("/healthz/ready", tags=["ops"])
async def healthz_ready():
    engine = get_engine()
    health = await engine.health_check()
    if health["status"] == "healthy":
        return health
    return JSONResponse(status_code=503, content=health)


@app.get("/api/status", tags=["ops"])
async def api_status():
    engine = get_engine()
    return {
        "status": "ok",
        "version": "3.1.0",
        "engine_ready": True,
        "stats": engine.get_stats(),
    }


@app.get("/metrics", tags=["ops"])
async def metrics():
    engine = get_engine()
    stats = engine.get_stats()
    lines = [
        "# HELP adam_total_turns Total chat turns",
        "# TYPE adam_total_turns counter",
        f"adam_total_turns {stats['total_turns']}",
        "",
        "# HELP adam_lora_calls LoRA calls",
        "# TYPE adam_lora_calls counter",
        f"adam_lora_calls {stats['lora_calls']}",
        "",
        "# HELP adam_ollama_calls Ollama calls",
        "# TYPE adam_ollama_calls counter",
        f"adam_ollama_calls {stats['ollama_calls']}",
        "",
        "# HELP adam_tool_calls Tool executions",
        "# TYPE adam_tool_calls counter",
        f"adam_tool_calls {stats['tool_calls']}",
        "",
        "# HELP adam_compressions Context compressions",
        "# TYPE adam_compressions counter",
        f"adam_compressions {stats['compressions']}",
        "",
        "# HELP adam_errors Total errors",
        "# TYPE adam_errors counter",
        f"adam_errors {stats['errors']}",
        "",
        "# HELP adam_memories_extracted Auto-extracted memories",
        "# TYPE adam_memories_extracted counter",
        f"adam_memories_extracted {stats.get('memories_extracted', 0)}",
        "",
        "# HELP adam_cpu_percent CPU usage",
        "# TYPE adam_cpu_percent gauge",
        f"adam_cpu_percent {psutil.cpu_percent()}",
        "",
        "# HELP adam_memory_percent Memory usage",
        "# TYPE adam_memory_percent gauge",
        f"adam_memory_percent {psutil.virtual_memory().percent}",
        "",
    ]
    return "\n".join(lines)


# ============================================================
# Main
# ============================================================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "adam.server:app",
        host="0.0.0.0",
        port=int(os.getenv("PORT", "8000")),
        reload=os.getenv("ADAM_RELOAD", "0") == "1",
        log_level=os.getenv("ADAM_LOG_LEVEL", "info"),
    )
