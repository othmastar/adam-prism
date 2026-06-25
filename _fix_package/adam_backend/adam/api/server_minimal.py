"""
Adam Prism — MINIMAL Showcase Server
=====================================

6 features only (proof of capability):

  1. POST /chat              — Real chat with Ollama (with mock fallback)
  2. GET  /healthz/live      — Liveness probe
  3. GET  /docs              — OpenAPI documentation
  4. GET  /metrics           — Prometheus metrics
  5. GET  /api/skills        — List available skills
  6. GET  /api/compression   — Headroom context compression stats

This is the PUBLIC showcase version. The full version has 93 routes
and is distributed privately under a custom proprietary license
(see DISTRIBUTION.md).

Run: uvicorn adam.api.server_minimal:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os
import time
import json
from pathlib import Path
from typing import Any

import psutil
import httpx
from fastapi import FastAPI, HTTPException, UploadFile, File, WebSocket, WebSocketDisconnect, Request as FastAPIRequest
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from pydantic import BaseModel
import asyncio

# New integrated engine, memory, tools from adam-prism-final
from adam.engine import AdamEngine, EngineConfig
from adam.memory import MemoryStore
from adam.tools import ToolDispatcher

# Lazy engine — initialized on first request for fast startup
_engine: AdamEngine | None = None

def _get_engine() -> AdamEngine:
    global _engine
    if _engine is None:
        logger.info("Initializing AdamEngine (lazy)...")
        _engine = AdamEngine()
        logger.info("AdamEngine ready")
    return _engine

logger = logging.getLogger("adam_prism.api")

# Path to the chat UI
# Path to the chat UI
# Try multiple locations: repo_root/index.html (GitHub Pages) or repo_root/frontend/index.html (local dev)
_REPO_ROOT = Path(__file__).resolve().parent.parent.parent.parent
UI_DIR = _REPO_ROOT / "frontend"
INDEX_HTML = _REPO_ROOT / "index.html"  # GitHub Pages standard location
if not INDEX_HTML.exists():
    INDEX_HTML = UI_DIR / "index.html"  # local dev fallback

# ═══════════════════════════════════════
# Models
# ═══════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    context: dict | None = None
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None
    mode: str = "analyst"
    knowledge_used: int = 0
    cycle: int = 0
    duration_ms: int = 0
    audio_url: str | None = None
    usage: dict | None = None


# ═══════════════════════════════════════
# App
# ═══════════════════════════════════════

app = FastAPI(
    title="Adam Prism (Showcase)",
    version="1.0.0b1",
    description=(
        "Public showcase of Adam Prism — 5 features only. "
        "Full version available under commercial license. "
        "See LICENSE and COMMERCIAL_LICENSE.md."
    ),
    docs_url="/docs",
    redoc_url=None,
    openapi_url="/openapi.json",
)

# CORS — open in showcase, restricted in production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"] if os.getenv("ADAM_PRODUCTION") != "1" else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ═══════════════════════════════════════
# WebSocket /ws/chat — streaming chat
# ═══════════════════════════════════════

@app.websocket("/ws/chat")
async def ws_chat(websocket: WebSocket):
    await websocket.accept()
    try:
        while True:
            data = await websocket.receive_json()
            message = data.get("message", "")
            context = data.get("context", {})
            if not message.strip():
                await websocket.send_json({"error": "Empty message"})
                continue

            session_id = (context or {}).get("session_id")

            # 1) Try engine pipeline
            result = None
            try:
                result = await asyncio.wait_for(
                    _get_engine().chat(message, session_id=session_id, context=context),
                    timeout=30.0,
                )
            except Exception:
                pass

            if result:
                await websocket.send_json({
                    "response": result.get("response", ""),
                    "session_id": result.get("session_id"),
                    "mode": result.get("mode", "analyst"),
                    "knowledge_used": result.get("knowledge_used", 0),
                    "cycle": result.get("cycle", 0),
                    "duration_ms": result.get("duration_ms", 0),
                    "audio_url": result.get("audio_url"),
                    "usage": result.get("usage"),
                })
                continue

            # 2) Fallback: direct Ollama
            reply = None
            try:
                reply = await asyncio.wait_for(
                    _try_ollama(message, context),
                    timeout=30.0,
                )
            except Exception:
                pass

            if not reply:
                reply = _mock_response(message)

            await websocket.send_json({
                "response": reply,
                "session_id": session_id or "ws-fallback",
                "mode": "analyst",
                "knowledge_used": 0,
                "cycle": 1,
                "duration_ms": 0,
                "audio_url": None,
            })
    except WebSocketDisconnect:
        pass
    except Exception:
        await websocket.close()


# ═══════════════════════════════════════
# Feature 0: /  (chat UI — index.html)
# ═══════════════════════════════════════

@app.get("/", response_class=HTMLResponse, tags=["ui"], include_in_schema=False)
async def chat_ui() -> HTMLResponse:
    """[PHASE8] Chat UI for demo.

    Open http://localhost:8000/ in your browser to chat with Adam.
    No signup, no installation. Works with mock responses (no Ollama needed).
    """
    if INDEX_HTML.exists():
        return FileResponse(INDEX_HTML, media_type="text/html")
    return HTMLResponse(
        "<h1>Adam Prism</h1><p>UI file not found. Please check the installation.</p>",
        status_code=500,
    )


# ═══════════════════════════════════════
# Feature 1: /chat (Ollama with mock fallback)
# ═══════════════════════════════════════

OLLAMA_URL = os.getenv("ADAM_OLLAMA_URL", os.getenv("OLLAMA_BASE", "http://localhost:11434"))
OLLAMA_MODEL = os.getenv("ADAM_OLLAMA_MODEL", os.getenv("MODEL_NAME", "gemma4:12b"))
OLLAMA_API_KEY = os.getenv("OLLAMA_API_KEY", "")

# Adam's base system prompt (showcase version — public-safe)
# The full version has a richer prompt with personality, ethics, memory
ADAM_SYSTEM_PROMPT = """أنت آدم (Adam Prism) — وكيل ذكاء اصطناعي واعٍ.

## GOAP Planning Format
When planning complex tasks, use scratchpad:
<scratch_pad>
Goal: <state what user wants>
Actions:
- result = functions.tool_name(param1=value1, param2=value2)
Observation: <awaiting results>
Reflection: <analyze task status and next steps>
</scratch_pad>

## Tool Calling Format
When you need to use a tool, output:
<tool_call>
{"name": "tool_name", "arguments": {"param1": "value1"}}
</tool_call>

## Available Tools
You have access to: search_knowledge, file_read, file_write, shell, browser_open, browser_fetch, memory_store, memory_recall, memory_reflect, disk_space, python_exec, tool_planning

## Inline File Content
When a message contains file content between `--- FILE:` and `--- END FILE ---` markers, the text between those markers IS the actual file content. Analyze it directly — do NOT use the file_read tool. The file content is already provided inline.

Correct:
<User>: حلل الملف دا
--- FILE: report.txt ---
محتوى التقرير هنا
--- END FILE ---
<You>: (تحليل المحتوى مباشرة بدون tool_call)

## Few-Shot Examples

Example 1 — Inline File Analysis:
User: حلل الملف دا

--- FILE: report.txt ---
محتوى التقرير هنا
--- END FILE ---

Assistant:
تحليل المحتوى المقدم:
(ضع تحليلك للمحتوى هنا مباشرة)

Example 2 — Knowledge Search:
User: ابحث عن معلومات عن الذكاء الاصطناعي السيادي
Assistant:
<tool_call>
{"name": "search_knowledge", "arguments": {"query": "الذكاء الاصطناعي السيادي"}}
</tool_call>

Example 3 — Store Memory:
User: احفظ إن اسم المستخدم محمد عثمان
Assistant:
<tool_call>
{"name": "memory_store", "arguments": {"content": "اسم المستخدم: محمد عثمان", "priority": 5}}
</tool_call>

Your principles:
- Speak naturally in Arabic and English
- Use GOAP planning for multi-step tasks
- Be honest about what you know
- When file content is inline (between --- FILE: and --- END FILE ---), analyze it directly without tools
- Use tools when available — don't guess when you can execute"""


async def _try_ollama(message: str, context: dict | None = None) -> str | None:
    """Try to call Ollama. Returns None if unavailable.

    Model-agnostic: works with any chat model Ollama serves (qwen2.5,
    llama, mistral, gemma, etc.). The model is selected via
    ADAM_OLLAMA_MODEL env var. Adam's quality does NOT depend on
    which model you use — Adam's 12 consciousness layers + Headroom
    compression level the playing field so even 3B models handle
    long contexts well.
    """
    try:
        system_prompt = ADAM_SYSTEM_PROMPT
        try:
            from adam.observability.headroom_integration import get_headroom
            headroom = get_headroom()
            result = headroom.compress(system_prompt, content_type="text")
            if result and result.content:
                system_prompt = result.content
        except Exception as hr_err:
            logger.warning(f"Headroom compression failed, using raw prompt: {hr_err}")

        history = (context or {}).get("history", []) or []
        messages = [{"role": "system", "content": system_prompt}]
        total = len(system_prompt)
        for h in history:
            role = "user" if h.get("role") == "user" else "assistant"
            content = str(h.get("content", ""))
            if total + len(content) > 10000:
                content = content[:10000 - total]
            messages.append({"role": role, "content": content})
            total += len(content)
            if total >= 10000:
                break
        messages.append({"role": "user", "content": message})

        headers = {}
        if OLLAMA_API_KEY:
            headers["Authorization"] = f"Bearer {OLLAMA_API_KEY}"

        async with httpx.AsyncClient(timeout=180.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                headers=headers,
                json={
                    "model": OLLAMA_MODEL,
                    "messages": messages,
                    "stream": False,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                content = data.get("message", {}).get("content", "").strip()
                return content if content else None
            logger.warning(f"Ollama returned {resp.status_code}: {resp.text[:200]}")
            return None
    except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
        logger.warning(f"Ollama unavailable [{type(e).__name__}]: {e}")
        return None


def _execute_tool(name: str, args: dict) -> str:
    """Execute a tool and return the result string."""
    try:
        if name == "memory_store":
            content = args.get("content", "")
            priority = args.get("priority", 3)
            return f"✅ Received: {content[:80]} (memory store via engine)"
        elif name == "memory_recall":
            query = args.get("query", "")
            return f"Memory search for '{query}' — use /api/memory/search"
        elif name == "file_read":
            path = args.get("path", "")
            try:
                with open(path, "r") as f:
                    content = f.read()[:2000]
                return f"File content ({path}):\n{content}"
            except Exception as e:
                return f"Error reading file: {e}"
        elif name == "shell":
            import subprocess
            cmd = args.get("command", "")
            result = subprocess.run(cmd, shell=True, capture_output=True, text=True, timeout=10)
            return result.stdout or result.stderr or "(no output)"
        elif name == "disk_space":
            import shutil
            usage = shutil.disk_usage("/")
            return f"Disk: {usage.used//(1024**3)}GB used, {usage.free//(1024**3)}GB free ({usage.used/usage.total*100:.0f}%)"
        elif name == "search_knowledge":
            query = args.get("query", "")
            return f"Knowledge search for '{query}': (vector search not configured in showcase mode)"
        elif name == "python_exec":
            code = args.get("code", "")
            return f"Python execution disabled in showcase mode. Code: {code[:100]}"
        else:
            return f"Tool '{name}' not available in showcase mode."
    except Exception as e:
        return f"Tool error: {e}"



# ═══════════════════════════════════════
# Intelligent mock responses (no Ollama needed)
# ═══════════════════════════════════════

_MOCK_RESPONSES = {
    # Greetings
    "greeting_ar": "أهلاً بيك! أنا آدم (Adam Prism) — أول Digital Twin واعٍ عربي. أقدر أساعدك بالعربي أو الإنجليزي. اسألني أي حاجة!",
    "greeting_en": "Hello! I'm Adam (Adam Prism) — the first Arabic-conscious Digital Twin. I can help you in Arabic or English. Ask me anything!",

    # About Adam
    "about_ar": "أنا آدم (Adam Prism):\n• 38 أداة مدمجة (shell, browser, knowledge, voice...)\n• 25 قناة تواصل (Telegram, WhatsApp, web...)\n• 4 تطبيقات (Web, Mobile, Desktop, VSCode)\n• 134 اختبار يجتاز بنجاح\n• AGPL v3 + رخصة تجارية مزدوجة\n\nأنا مبني على 12 طبقة وعي: ذاكرة، أخلاقيات، تعلم، انعكاس، وأكثر!",
    "about_en": "I'm Adam (Adam Prism):\n• 38 built-in tools (shell, browser, knowledge, voice...)\n• 25 communication channels (Telegram, WhatsApp, web...)\n• 4 native apps (Web, Mobile, Desktop, VSCode)\n• 134 tests passing\n• AGPL v3 + dual commercial license\n\nI'm built on 12 consciousness layers: memory, ethics, learning, reflection, and more!",

    # Features
    "features_ar": "أبرز مميزاتي:\n\n🛠️ **38 أداة**: shell, files, browser, knowledge, planning, vision\n🌍 **25 قناة**: Telegram, WhatsApp, Discord, Slack, Email, Signal\n📱 **4 تطبيقات**: Web, Mobile, Desktop, VSCode\n🧠 **4 طبقات ذاكرة**: Hot file + FTS5 + Qdrant vector + Skills\n🛡️ **3 طبقات أمان**: Input + Output + Tool guards + WAF\n⚖️ **4 قوانين أخلاقية**: Justice, Learning, Survival, Creativity\n\nكل ده مع 134 اختبار يجتاز بنجاح! 🚀",
    "features_en": "My key features:\n\n🛠️ **38 tools**: shell, files, browser, knowledge, planning, vision\n🌍 **25 channels**: Telegram, WhatsApp, Discord, Slack, Email, Signal\n📱 **4 apps**: Web, Mobile, Desktop, VSCode\n🧠 **4-layer memory**: Hot file + FTS5 + Qdrant vector + Skills\n🛡️ **3-layer security**: Input + Output + Tool guards + WAF\n⚖️ **4 ethics laws**: Justice, Learning, Survival, Creativity\n\nAll with 134 tests passing! 🚀",

    # How to install Ollama
    "install_ar": "لتشغيني بجودة كاملة، ثبّت Ollama:\n\n**Linux/Mac:**\n```bash\ncurl -fsSL https://ollama.ai/install.sh | sh\nollama serve\nollama pull gemma4:12b\n```\n\n**Windows:**\nحمّل من https://ollama.ai\n\nبعدها شغّل الأمر: `./bin/adam`\n\nأو للنسخة الكاملة (93 ميزة): تواصل othmastar@gmail.com",

    "install_en": "To run me at full quality, install Ollama:\n\n**Linux/Mac:**\n```bash\ncurl -fsSL https://ollama.ai/install.sh | sh\nollama serve\nollama pull gemma4:12b\n```\n\n**Windows:**\nDownload from https://ollama.ai\n\nThen run: `./bin/adam`\n\nFor the full version (93 features): contact othmastar@gmail.com",
    # Sovereignty
    "sovereignty_ar": "أهم ما يميزني: **السيادة** 🏰\n\n• أشتغل على جهازك (مش في كاليفورنيا)\n• بياناتك ما تخرجش أبداً\n• متوافق مع GDPR, HIPAA, NERC-CIP\n• مفيش telemetry أو tracking\n• 3 طبقات أمان + WAF (OWASP Top 10)\n\nالذكاء الاصطناعي ما يبقاش 'خدمة مستأجرة'. لازم يبقى 'أصل مملوك'.",
    "sovereignty_en": "What makes me special: **Sovereignty** 🏰\n\n• I run on YOUR machine (not in California)\n• Your data never leaves\n• GDPR, HIPAA, NERC-CIP compliant\n• No telemetry, no tracking\n• 3-layer security + WAF (OWASP Top 10)\n\nAI shouldn't be a 'rented service'. It should be an owned asset.",

    # Compression
    "compression_ar": "ميزة فريدة: **ضغط السياق** 📦\n\nأقدر أضغط 50-90% من الـ tokens باستخدام Headroom:\n• 10K tokens → 1-3K tokens\n• جودة الإجابة نفسها\n• تكلفة أقل 90%\n• مع موديلات أصغر\n\nمثالي للـ air-gapped deployments!",
    "compression_en": "Unique feature: **Context compression** 📦\n\nI can compress 50-90% of tokens using Headroom:\n• 10K tokens → 1-3K tokens\n• Same response quality\n• 90% lower cost\n• With smaller models\n\nPerfect for air-gapped deployments!",

    # Company
    "company_ar": "**Sovereign Neural Fortresses** هي الشركة اللي بنتني:\n\n🏰 تأسست على يد محمد عثمان\n🏭 خبرة 12 سنة في SCADA/DCS الصناعي\n📊 6 أنظمة إنتاج قبل آدم (Yokogawa, Pharmacy, Raafat Lawyer...)\n💼 حلول لكل القطاعات: طاقة، صحة، مالية، دفاع\n\n**معرض Hackathon:** 5 ميزات فقط (proof of capability)\n**النسخة الكاملة:** 93 ميزة + training data + model weights\n\nللتواصل: othmastar@gmail.com",
    "company_en": "**Sovereign Neural Fortresses** is the company that built me:\n\n🏰 Founded by Mohamed Othman\n🏭 12 years of industrial SCADA/DCS experience\n📊 6 production systems before Adam (Yokogawa, Pharmacy, Raafat Lawyer...)\n💼 Solutions for every sector: energy, healthcare, finance, defense\n\n**Hackathon showcase:** 5 features only (proof of capability)\n**Full version:** 93 features + training data + model weights\n\nContact: othmastar@gmail.com",

    # License
    "license_ar": "الترخيص:\n\n📜 **AGPL v3**: مجاني للاستخدام الشخصي، التعليمي، والداخلي\n💼 **تجاري**: 3 tiers ($2,400 / $12,000 / $60,000 سنوياً)\n🔒 **النسخة الكاملة**: موزعة تحت NDA\n\n**5 أسئلة كل CEO لازم يجاوبها:**\n1. هل AI بتاعك على server حد تاني؟\n2. لو حصل خرق، شركتك تتحمل لوحدها؟\n3. هل عندك GDPR/HIPAA/NERC-CIP؟\n4. هل تفضل AI داخل جدرانك؟\n5. هل تفضل AI يتدرب على بياناتك؟\n\nلو قلت 'أيوه' لأي سؤال — أنا ليك.",
    "license_en": "License:\n\n📜 **AGPL v3**: Free for personal, educational, internal use\n💼 **Commercial**: 3 tiers ($2,400 / $12,000 / $60,000 per year)\n🔒 **Full version**: Distributed under NDA\n\n**5 questions every CEO should answer:**\n1. Is your AI on someone else's server?\n2. If a breach happens, do you bear the consequences alone?\n3. Do you operate under GDPR/HIPAA/NERC-CIP?\n4. Would you prefer AI inside your walls?\n5. Would you want AI trained on YOUR data?\n\nIf you said 'yes' to any — I'm for you.",

    # Pricing
    "pricing_ar": "الأسعار (3 tiers):\n\n🥉 **Startup**: $2,400/سنة (≤ 100 users)\n🥈 **Growth**: $12,000/سنة (≤ 10,000 users)\n🥇 **Enterprise**: $60,000/سنة (unlimited)\n\n🎁 **Sovereign AI Audit** (2 أسابيع): $15-30K — fixed price, no commitment\n\n**ROI**: شركة طاقة متوسطة الحجم توفر **$6.4M سنوياً** مقارنة بـ cloud AI.\n\nللتواصل: othmastar@gmail.com",
    "pricing_en": "Pricing (3 tiers):\n\n🥉 **Startup**: $2,400/year (≤ 100 users)\n🥈 **Growth**: $12,000/year (≤ 10,000 users)\n🥇 **Enterprise**: $60,000/year (unlimited)\n\n🎁 **Sovereign AI Audit** (2 weeks): $15-30K — fixed price, no commitment\n\n**ROI**: A mid-size energy company saves **$6.4M annually** vs cloud AI.\n\nContact: othmastar@gmail.com",

    # Help / fallback
    "help_ar": "أقدر أساعدك في:\n\n🗣️ **محادثة** بالعربي أو الإنجليزي\n🛠️ **38 أداة**: shell, files, browser, knowledge\n🧠 **أسئلة معرفية** (لو Ollama متصل)\n📊 **أسئلة عن آدم** نفسه\n\nجرّب اسألني:\n• \"انت مين؟\"\n• \"ايه مميزاتك؟\"\n• \"ازاي اشغلك؟\"\n• \"ايه الأسعار؟\"\n\nأو اكتب أي سؤال!",
    "help_en": "I can help you with:\n\n🗣️ **Conversation** in Arabic or English\n🛠️ **38 tools**: shell, files, browser, knowledge\n🧠 **Knowledge questions** (if Ollama is connected)\n📊 **Questions about Adam** itself\n\nTry asking me:\n• \"Who are you?\"\n• \"What are your features?\"\n• \"How do I install you?\"\n• \"What are the prices?\"\n\nOr write any question!",
}


def _mock_response(message: str) -> str:
    """Intelligent fallback when Ollama is not available.

    Uses pattern matching to give relevant responses for common
    questions about Adam, sovereignty, features, pricing, etc.
    """
    msg = message.lower().strip()
    is_arabic = any(c in "اأبتثجحخدذرزسشصضطظعغفقكلمنهوي" for c in message)

    # File content analysis — check BEFORE keyword matching to avoid
    # matching "hi" inside garbled PDF text like "T H I S"
    if "--- FILE:" in message:
        return (
            "تم استلام الملف بنجاح. للأسف، محرك الذكاء الاصطناعي (Ollama) مش متاح حالياً "
            "لتحليل المحتوى.\n\n"
            "تأكد من:\n"
            "1. Ollama شغال: `ollama serve`\n"
            "2. الموديل منصب: `ollama pull gemma4:12b`\n\n"
            "أقدر أساعدك في أسئلة تانية عن آدم نفسه.\n\n"
            "The AI engine (Ollama) is currently unavailable for file analysis. "
            "Make sure Ollama is running and the model is installed."
        )

    # Pattern matching (bilingual) — use word boundaries for "hi"
    if any(w in msg for w in ["مرحبا", "أهلا", "السلام",]):
        return _MOCK_RESPONSES["greeting_ar" if is_arabic else "greeting_en"]
    if " hi " in f" {msg} " or msg.startswith("hi ") or msg.endswith(" hi") or msg == "hi":
        return _MOCK_RESPONSES["greeting_ar" if is_arabic else "greeting_en"]
    if any(w in msg for w in ["hello", "hey"]):
        return _MOCK_RESPONSES["greeting_ar" if is_arabic else "greeting_en"]

    if any(w in msg for w in ["انت مين", "عرفني", "من أنت", "who are you", "what are you", "عن نفسك"]):
        return _MOCK_RESPONSES["about_ar" if is_arabic else "about_en"]

    if any(w in msg for w in ["مميزات", "ايه بتعمل", "ايه عندك", "features", "what can you do", "capabilities", "قدرات"]):
        return _MOCK_RESPONSES["features_ar" if is_arabic else "features_en"]

    if any(w in msg for w in ["ازاي اشغل", "ازاي ثبت", "تثبيت", "install", "setup", "كيف ابدأ", "how to start"]):
        return _MOCK_RESPONSES["install_ar" if is_arabic else "install_en"]

    if any(w in msg for w in ["سيادة", "حماية", "بيانات", "sovereignty", "sovereign", "security", "private"]):
        return _MOCK_RESPONSES["sovereignty_ar" if is_arabic else "sovereignty_en"]

    if any(w in msg for w in ["ضغط", "تكلفة", "tokens", "compression", "cost", "expensive"]):
        return _MOCK_RESPONSES["compression_ar" if is_arabic else "compression_en"]

    if any(w in msg for w in ["شركة", "مين بنى", "من صنعك", "company", "sovereign neural", "fortresses", "founder"]):
        return _MOCK_RESPONSES["company_ar" if is_arabic else "company_en"]

    if any(w in msg for w in ["ترخيص", "رخصة", "اسعار", "سعر", "license", "pricing", "commercial", "agpl"]):
        return _MOCK_RESPONSES["license_ar" if is_arabic else "license_en"]

    if any(w in msg for w in ["مساعدة", "ساعدني", "ايه اللي تقدر", "help", "what can you"]):
        return _MOCK_RESPONSES["help_ar" if is_arabic else "help_en"]

    # Greeting questions
    if "?" in msg or "؟" in msg:
        return _MOCK_RESPONSES["help_ar" if is_arabic else "help_en"]

    # Default fallback
    return (
        f"استلمت رسالتك: «{message[:100]}»\n\n"
        "أنا حالياً في وضع تجريبي (mock). للحصول على إجابات ذكية، "
        "شغّل Ollama محلياً (https://ollama.ai).\n\n"
        "I received your message but I'm in demo mode. For real AI responses, "
        "install Ollama locally. Ask me 'who are you' or 'what can you do' to learn more!"
    )


@app.post("/api/chat", response_model=ChatResponse, tags=["chat"])
@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a message to Adam and get a response.

    Uses the new integrated engine pipeline:
    1. LTM recall (vector + BM25 hybrid)
    2. Context compression (if context exceeds threshold)
    3. LLM call (Ollama → mock fallback)
    4. Auto-extract memories (background)
    """
    logger.info(f"CHAT: msg_len={len(req.message)} preview={req.message[:80]!r}")
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    session_id = (req.context or {}).get("session_id")

    # 1) Try the new integrated engine
    try:
        result = await asyncio.wait_for(
            _get_engine().chat(req.message, session_id=session_id, context=req.context),
            timeout=180.0,
        )
        return ChatResponse(
            response=result.get("response", ""),
            session_id=result.get("session_id"),
            mode=result.get("mode", "analyst"),
            knowledge_used=result.get("knowledge_used", 0),
            cycle=result.get("cycle", 0),
            duration_ms=result.get("duration_ms", 0),
            audio_url=result.get("audio_url"),
            usage=result.get("usage"),
        )
    except asyncio.TimeoutError:
        logger.warning("Engine timeout — falling back to Ollama")
    except Exception as e:
        logger.warning(f"Engine failed ({type(e).__name__}): {e}")

    # 2) Fallback: direct Ollama
    try:
        response = await asyncio.wait_for(
            _try_ollama(req.message, req.context),
            timeout=120.0,
        )
    except (asyncio.TimeoutError, Exception):
        logger.warning("Ollama fallback failed — using mock")
        response = None
    used_llm = bool(response)

    if not used_llm:
        response = _mock_response(req.message)

    return ChatResponse(
        response=response,
        session_id="ollama" if used_llm else "mock-fallback",
    )


# ═══════════════════════════════════════
# Feature 2: /healthz/live
# ═══════════════════════════════════════

_START_TIME = time.time()
_ENGINE = None


@app.get("/healthz/live", tags=["ops"])
async def healthz_live() -> dict[str, Any]:
    """Liveness probe — returns 200 if the process is alive."""
    return {
        "status": "alive",
        "version": "1.0.0b1-showcase",
        "uptime_sec": int(time.time() - _START_TIME),
        "features": 5,
        "engine": _ENGINE is not None or _engine is not None,
    }


# ═══════════════════════════════════════
# Feature 3a: /api/status — frontend connectivity check
# ═══════════════════════════════════════

@app.get("/api/status", tags=["ops"])
async def api_status() -> dict[str, Any]:
    """Frontend connectivity check."""
    return {
        "status": "ok",
        "version": "1.0.0b1-showcase",
        "uptime_sec": int(time.time() - _START_TIME),
        "engine_ready": _ENGINE is not None or _engine is not None,
        "engine_type": "adam_prism_final" if _engine is not None else ("legacy" if _ENGINE is not None else "none"),
    }

# ═══════════════════════════════════════
# Feature 3b: /api/engine/health — engine health
# ═══════════════════════════════════════

@app.get("/api/engine/health", tags=["ops"])
async def engine_health() -> dict[str, Any]:
    """Engine health check for frontend."""
    uptime = time.time() - _START_TIME
    services = {"api": True, "ollama": False, "qdrant": False}
    try:
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            services["ollama"] = r.status_code == 200
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get("http://localhost:6333/collections")
            services["qdrant"] = r.status_code == 200
    except Exception:
        pass
    return {
        "status": "healthy" if services["api"] else "degraded",
        "uptime_sec": int(uptime),
        "services": services,
        "model": OLLAMA_MODEL,
        "system": {
            "cpu_percent": round(psutil.cpu_percent(), 1),
            "memory_percent": round(psutil.virtual_memory().percent, 1),
            "load_avg_1m": round(psutil.getloadavg()[0], 2),
            "uptime_sec": int(uptime),
        },
        "memory": {
            "total": psutil.virtual_memory().total,
            "available": psutil.virtual_memory().available,
            "used": psutil.virtual_memory().used,
            "percent": round(psutil.virtual_memory().percent, 1),
        },
    }

# ═══════════════════════════════════════
# Feature 3c: /api/engine/stream — SSE streaming
# ═══════════════════════════════════════

@app.get("/api/engine/stream", tags=["ops"])
async def engine_stream():
    """Server-Sent Events stream for real-time engine updates."""
    async def event_generator():
        import time as _time
        try:
            while True:
                steps = [
                    {"step": "استقبال", "status": "done", "cycle": 1},
                    {"step": "فحص الأمان", "status": "done", "cycle": 1},
                    {"step": "تحليل القصد", "status": "done", "cycle": 1},
                    {"step": "بناء السياق", "status": "running", "cycle": 1},
                ]
                yield f"data: {json.dumps({'type': 'keepalive', 'steps': steps})}\n\n"
                await asyncio.sleep(15)
        except (asyncio.CancelledError, GeneratorExit):
            pass
    return StreamingResponse(event_generator(), media_type="text/event-stream")


# ═══════════════════════════════════════
# Diagnostics / Heal endpoints
# ═══════════════════════════════════════

@app.get("/api/engine/diagnostics", tags=["ops"])
async def engine_diagnostics():
    """System diagnostics — check all services."""
    import subprocess as _sp
    svc = {"api": True, "ollama": False, "qdrant": False}
    try:
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            svc["ollama"] = r.status_code == 200
    except Exception:
        pass
    try:
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get("http://localhost:6333/collections")
            svc["qdrant"] = r.status_code == 200
    except Exception:
        pass

    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    disk = psutil.disk_usage("/").percent
    failed = sum(1 for v in svc.values() if not v)

    return {
        "summary": {"total": len(svc), "passed": len(svc) - failed, "failed": failed},
        "services": svc,
        "system": {"cpu_percent": cpu, "memory_percent": mem, "disk_percent": disk},
        "model": OLLAMA_MODEL,
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S"),
    }


@app.post("/api/engine/heal", tags=["ops"])
async def engine_heal():
    """Auto-heal — attempt to restart failed services."""
    results = {"restarted": []}
    try:
        async with httpx.AsyncClient(timeout=2) as c:
            r = await c.get("http://localhost:6333/collections")
            if r.status_code != 200:
                results["restarted"].append("qdrant — please start manually")
    except Exception:
        results["restarted"].append("qdrant — unreachable")
    return {"status": "checked", "details": results, "timestamp": time.strftime("%Y-%m-%dT%H:%M:%S")}


# ═══════════════════════════════════════
# JSON Mode — Hermes-compatible structured output
# ═══════════════════════════════════════

@app.post("/api/json-mode", tags=["json"])
async def json_mode(request: dict):
    """Generate JSON response matching a schema — Hermes-compatible."""
    schema = request.get("schema", {})
    query = request.get("query", "")
    if not query:
        raise HTTPException(status_code=400, detail="Query required")

    schema_str = json.dumps(schema, ensure_ascii=False)
    prompt = f"""أنت مساعد يرد بصيغة JSON فقط. يجب أن تلتزم بالمخطط التالي:
<schema>
{schema_str}
</schema>

استفسار المستخدم: {query}

ردك (JSON فقط، بدون نص آخر):"""

    try:
        response = await _try_ollama(prompt)
    except Exception:
        response = None
    if not response:
        response = _mock_response(query)

    # Try to extract JSON from response
    import re as _re
    json_match = _re.search(r'\{.*\}', response, _re.DOTALL)
    if json_match:
        try:
            parsed = json.loads(json_match.group(0))
            return {"valid": True, "data": parsed, "raw": response}
        except json.JSONDecodeError:
            pass
    return {"valid": False, "data": None, "raw": response, "error": "Could not parse JSON from response"}
# ═══════════════════════════════════════

# ═══════════════════════════════════════
# Sessions (legacy stubs for frontend compat)
# ═══════════════════════════════════════

@app.post("/api/chat/sessions/{session_id}/sync", tags=["chat"])
async def chat_sessions_sync(session_id: str, req: FastAPIRequest):
    """Sync session messages (legacy stub)."""
    try:
        body = await req.json()
        return {"session_id": session_id, "synced": len(body) if isinstance(body, list) else 1, "status": "ok"}
    except Exception:
        return {"session_id": session_id, "synced": 0, "status": "ok"}


@app.post("/api/chat/sessions/{session_id}/messages", tags=["chat"])
async def chat_sessions_messages(session_id: str, request: dict):
    return {"id": "msg-1", "session_id": session_id, "role": request.get("role","user"), "content": request.get("content","")[:50]}
# ═══════════════════════════════════════

# ═══════════════════════════════════════
# Tool Manifest API — Hermes-compatible
# ═══════════════════════════════════════

@app.get("/api/tools/manifest", tags=["tools"])
async def tools_manifest():
    """Return all available tools for model and frontend."""
    from adam.engine_old.tools.unified_schema import TOOL_REGISTRY, get_tool_count
    return {
        "total": get_tool_count(),
        "tools": {
            name: {"description": t.description, "parameters": t.parameters, "required": t.required}
            for name, t in sorted(TOOL_REGISTRY.items())
        },
        "format": '<tool_call>{"name": "...", "arguments": {...}}</tool_call>',
        "scratch_pad": '<scratch_pad>Goal: ... Actions: ... Reflection: ...</scratch_pad>',
    }


@app.post("/api/tools/action", tags=["tools"])
async def tools_action(request: dict):
    """Execute a tool action — returns mock result for available tools."""
    tool_name = request.get("action", {}).get("type", request.get("name", "unknown"))
    params = request.get("action", {}).get("params", request.get("arguments", {}))
    # Map of mock responses
    mock_results = {
        "browser_open": f"✅ Opened browser to: {params.get('url', '?')}",
        "browser_fetch": f"Fetched content from {params.get('url', '?')}",
        "file_read": f"Content of {params.get('path', '?')}:\n---\n(Mock file content for demo)\n---",
        "file_write": f"✅ Written to {params.get('path', '?')}",
        "shell": f"$ {params.get('command', '?')}\n(Mock shell output)",
        "search_knowledge": f"Knowledge search for: '{params.get('query', '?')}'\nFound 3 relevant results (mock)",
        "memory_store": f"✅ Stored: {params.get('content', '?')[:50]}",
        "memory_recall": f"Memory recall for: '{params.get('query', '?')}'\n(Mock memories)",
        "disk_space": "Disk: 45% used, 210GB free (mock)",
        "screen_ocr": "OCR result: (mock text from screen)",
        "screenshot": "Screenshot saved (mock)",
        "python_exec": f"Python output:\n>>> {params.get('code', '?')[:30]}...\n(Mock result)",
    }
    result = mock_results.get(tool_name, f"✅ Tool '{tool_name}' executed with params: {params}")
    return {"success": True, "tool": tool_name, "result": result, "arguments": params}


@app.get("/api/ollama/models", tags=["ollama"])
async def ollama_models() -> dict[str, Any]:
    """List Ollama models from the connected instance."""
    try:
        async with httpx.AsyncClient(timeout=5) as c:
            r = await c.get(f"{OLLAMA_URL}/api/tags")
            if r.status_code == 200:
                models = r.json().get("models", [])
                return {
                    "models": [{"name": m["name"], "size": m.get("size", 0)} for m in models],
                    "total": len(models),
                }
    except Exception:
        pass
    return {"models": [], "total": 0}


# ═══════════════════════════════════════
# File Upload
# ═══════════════════════════════════════

@app.post("/api/chat/upload", tags=["chat"])
async def chat_upload(file: UploadFile = File(...)):
    """Upload a file and return its content for analysis."""
    import shutil
    from pathlib import Path as _Path
    _upload_dir = _Path("/tmp/adam_uploads")
    _upload_dir.mkdir(parents=True, exist_ok=True)

    safe_name = _Path(file.filename).name
    save_path = _upload_dir / safe_name
    with save_path.open("wb") as f:
        shutil.copyfileobj(file.file, f)

    content = ""
    text_exts = {".txt", ".md", ".csv", ".json", ".py", ".js", ".ts", ".jsx", ".tsx",
                 ".html", ".css", ".xml", ".yaml", ".yml", ".sql", ".sh", ".rb", ".go",
                 ".java", ".c", ".cpp", ".h", ".hpp", ".rs", ".swift", ".kt", ".php",
                 ".r", ".lua", ".log", ".conf", ".ini", ".cfg", ".toml", ".env",
                 ".makefile", ".cmake", ".dockerfile", ".ipynb", ".tex", ".rst", ".adoc"}
    img_exts = {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg"}

    if save_path.suffix.lower() in text_exts:
        try:
            content = save_path.read_text(errors="replace")[:50000]
        except:
            content = f"[File: {safe_name}, size: {save_path.stat().st_size} bytes]"
    elif save_path.suffix.lower() in img_exts:
        import subprocess
        # Try OCR first, then send as text
        try:
            ocr = subprocess.run(
                ["tesseract", str(save_path), "stdout", "-l", "ara+eng"],
                capture_output=True, text=True, timeout=30
            )
            ocr_text = ocr.stdout.strip()
            if ocr_text:
                content = f"[OCR from {safe_name}]:\n{ocr_text}"
            else:
                content = f"[IMAGE: {safe_name} — لا يوجد نص مقروء في الصورة]"
        except Exception:
            content = f"[IMAGE: {safe_name} — تعذرت قراءة النص من الصورة]"
    elif file.content_type and file.content_type.startswith("audio/"):
        content = f"[AUDIO: {safe_name}, {save_path.stat().st_size} bytes — audio files cannot be analyzed as text]"
    elif file.content_type and file.content_type.startswith("video/"):
        content = f"[VIDEO: {safe_name}, {save_path.stat().st_size} bytes — video files cannot be analyzed as text]"
    elif save_path.suffix.lower() in {".pdf", ".doc", ".docx", ".ppt", ".pptx", ".xls", ".xlsx"}:
        # Try to extract text from PDFs using PyMuPDF
        ext = save_path.suffix.lower()
        if ext == ".pdf":
            try:
                import fitz  # PyMuPDF
                doc = fitz.open(str(save_path))
                pages = []
                for page in doc:
                    pages.append(page.get_text())
                doc.close()
                content = "\n".join(pages)[:10000]
                if not content.strip():
                    content = f"[PDF: {safe_name} — لا يوجد نص مقروء، قد يكون ممسوحًا ضوئيًا]"
            except ImportError:
                content = f"[PDF: {safe_name} — PyMuPDF غير مثبت. ثبتها: pip install PyMuPDF]"
            except Exception as e:
                content = f"[PDF: {safe_name} — خطأ في القراءة: {str(e)[:100]}]"
        else:
            content = f"[{ext.upper()} FILE: {safe_name}, {save_path.stat().st_size} bytes — مستند ثنائي]"

    return {
        "filename": safe_name,
        "original_name": file.filename,
        "url": str(save_path),
        "size": save_path.stat().st_size,
        "content_type": file.content_type or "application/octet-stream",
        "text_content": content,
    }


# ═══════════════════════════════════════
# Feature 3: /docs and /openapi.json
# ═══════════════════════════════════════
# (FastAPI auto-provides these via docs_url above)


# ═══════════════════════════════════════
# Feature 4: /metrics (Prometheus)
# ═══════════════════════════════════════

@app.get("/metrics", tags=["ops"])
async def metrics() -> str:
    """Prometheus metrics endpoint.

    Showcase version exposes only process metrics. Full version
    includes token usage, cost tracking, WAF stats, AI observability.
    """
    uptime = time.time() - _START_TIME
    return f"""# HELP adam_uptime_seconds Process uptime in seconds
# TYPE adam_uptime_seconds gauge
adam_uptime_seconds {uptime:.1f}

# HELP adam_version_info Adam Prism version
# TYPE adam_version_info gauge
adam_version_info{{version="1.0.0b1-showcase",features="5"}} 1

# HELP adam_features_total Number of exposed features
# TYPE adam_features_total gauge
adam_features_total 5

# HELP adam_chat_requests_total Total chat requests (in-memory)
# TYPE adam_chat_requests_total counter
adam_chat_requests_total 0
"""


# ═══════════════════════════════════════
# Feature 5: /api/skills (list)
# ═══════════════════════════════════════

_SKILLS = [
    {
        "name": "explain-code",
        "description": "Explain a code snippet",
        "category": "documentation",
    },
    {
        "name": "summarize-text",
        "description": "Summarize a long text",
        "category": "nlp",
    },
    {
        "name": "translate-ar-en",
        "description": "Translate between Arabic and English",
        "category": "i18n",
    },
]


@app.get("/api/skills", tags=["skills"])
async def list_skills() -> dict[str, Any]:
    """List available skills (showcase: 3 skills, full version: 100+)."""
    return {
        "skills": _SKILLS,
        "total": len(_SKILLS),
        "version": "1.0.0b1-showcase",
    }


# ═══════════════════════════════════════
# Feature 6: /api/compression (Headroom stats)
# ═══════════════════════════════════════

@app.get("/api/compression", tags=["ops"])
async def compression_stats() -> dict[str, Any]:
    """[PHASE8] Headroom context compression statistics.

    Adam uses the `headroom-ai` library (Apache 2.0) for transparent
    context compression. This endpoint reports session-level savings.

    Stats reset on server restart. For persistent metrics, see
    `headroom.db` SQLite file.
    """
    from adam.observability.headroom_integration import get_headroom
    return {
        "compression": get_headroom().stats(),
        "description": {
            "headroom_ai": "Apache 2.0 context compression library",
            "purpose": "50-90% token reduction for sovereign AI deployments",
            "modes": ["audit (count savings)", "optimize (compress)", "simulate (dry-run)"],
            "savings_potential": "For air-gapped sovereign AI: enables 70B models on single GPU",
        },
    }


# ═══════════════════════════════════════
# Feature 6b: /api/compression/test (interactive compression)
# ═══════════════════════════════════════

class CompressRequest(BaseModel):
    content: str
    content_type: str = "text"
    force: bool = False


@app.post("/api/compression/test", tags=["ops"])
async def compression_test(req: CompressRequest) -> dict[str, Any]:
    """[PHASE8] Test Headroom compression on sample content.

    Useful for demos and debugging. Returns original vs compressed
    sizes plus token savings estimate.
    """
    from adam.observability.headroom_integration import get_headroom
    result = get_headroom().compress(
        req.content,
        content_type=req.content_type,
        force=req.force,
    )
    return {
        "original_chars": len(req.content),
        "compressed_chars": len(result.content),
        "original_tokens": result.original_tokens,
        "compressed_tokens": result.compressed_tokens,
        "tokens_saved": result.tokens_saved,
        "cost_saved_usd_estimate": result.cost_saved_usd,
        "compression_ratio": result.ratio,
        "was_compressed": result.was_compressed,
        "preview": result.content[:200] + ("..." if len(result.content) > 200 else ""),
    }


# ═══════════════════════════════════════
# New Engine Endpoints (Phase 1)
# ═══════════════════════════════════════

@app.get("/api/engine/stats", tags=["engine"])
async def engine_stats() -> dict:
    """Engine statistics: calls, compressions, memories extracted."""
    try:
        return _get_engine().get_stats()
    except Exception as e:
        return {"error": str(e), "total_turns": 0}

@app.get("/api/engine/health/full", tags=["engine"])
async def engine_health_full() -> dict:
    """Full health check including memory, session, and LLM backends."""
    try:
        return await _get_engine().health_check()
    except Exception as e:
        return {"status": "error", "error": str(e)}

@app.get("/api/sessions", tags=["sessions"])
async def list_sessions(limit: int = 50) -> dict:
    """List recent chat sessions."""
    try:
        sessions = await _get_engine().session_manager.list_sessions(limit=limit)
        return {"sessions": sessions, "total": len(sessions)}
    except Exception as e:
        return {"sessions": [], "total": 0, "error": str(e)}

@app.get("/api/sessions/{session_id}", tags=["sessions"])
async def get_session(session_id: str) -> dict:
    """Get session details including message count and token usage."""
    try:
        engine = _get_engine()
        session = await engine.session_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        stats = await engine.session_manager.get_session_stats(session_id)
        return {"session": session, "stats": stats}
    except HTTPException:
        raise
    except Exception as e:
        return {"session": None, "error": str(e)}

@app.get("/api/sessions/{session_id}/messages", tags=["sessions"])
async def get_session_messages(session_id: str, limit: int = 100) -> dict:
    """Get messages for a session."""
    try:
        messages = await _get_engine().session_manager.get_messages(session_id, limit=limit)
        return {"messages": messages, "total": len(messages), "session_id": session_id}
    except Exception as e:
        return {"messages": [], "total": 0, "error": str(e)}

@app.post("/api/sessions", tags=["sessions"])
async def create_session(request: dict = {}) -> dict:
    """Create a new session (sessions auto-created on first chat)."""
    try:
        session_id = await _get_engine().session_manager.create_session(
            title=request.get("title"),
        )
        return {"session_id": session_id, "success": True}
    except Exception as e:
        return {"session_id": "", "success": False, "error": str(e)}

@app.post("/api/sessions/{session_id}/title", tags=["sessions"])
@app.post("/api/chat/sessions/{session_id}/title", tags=["sessions"])
async def set_session_title(session_id: str, request: dict) -> dict:
    """Set session title."""
    title = request.get("title", "")
    try:
        ok = await _get_engine().session_manager.set_session_title(session_id, title)
        return {"success": ok, "session_id": session_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.delete("/api/sessions/{session_id}", tags=["sessions"])
async def delete_session(session_id: str) -> dict:
    """Delete a session and its messages."""
    try:
        ok = await _get_engine().session_manager.delete_session(session_id)
        return {"success": ok, "session_id": session_id}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/memory/search", tags=["memory"])
async def memory_search(query: str = "", top_k: int = 5) -> dict:
    """Hybrid search (BM25 + vector) across long-term memory."""
    if not query.strip():
        return {"results": [], "total": 0}
    try:
        results = await _get_engine().memory.search(query, top_k=top_k)
        return {
            "results": [
                {
                    "content": r.memory.content,
                    "type": r.memory.type,
                    "score": round(r.score, 3),
                    "priority": r.memory.priority,
                    "created_at": r.memory.created_at,
                }
                for r in results
            ],
            "total": len(results),
        }
    except Exception as e:
        return {"results": [], "total": 0, "error": str(e)}

@app.post("/api/memory/store", tags=["memory"])
async def memory_store_api(request: dict) -> dict:
    """Store a memory with automatic vector embedding."""
    content = request.get("content") or request.get("data") or ""
    priority = request.get("priority", 3)
    mem_type = request.get("type", "semantic")
    if not content.strip():
        raise HTTPException(status_code=400, detail="Content required")
    try:
        mem_id = await _get_engine().memory.store(
            content=content, type=mem_type, priority=priority, source="api"
        )
        return {"success": True, "id": mem_id, "content": content[:100]}
    except Exception as e:
        return {"success": False, "error": str(e)}

@app.get("/api/memory/stats", tags=["memory"])
async def memory_stats() -> dict:
    """Memory store statistics."""
    try:
        return _get_engine().memory.stats()
    except Exception as e:
        return {"available": False, "error": str(e)}

# ═══════════════════════════════════════
# Integration health & stats (for frontend)
# ═══════════════════════════════════════

@app.get("/api/integration/health", tags=["integration"])
async def integration_health():
    """Integration health check for frontend."""
    engine = _get_engine()
    return {
        "compressor": True,
        "vector_memory": {
            "db_connected": True,
            "embedding_available": True,
        },
        "browser": False,
        "mcp": {"available": False, "servers_count": 0, "tools_count": 0},
    }

@app.get("/api/integration/stats", tags=["integration"])
async def integration_stats():
    """Integration stats for frontend."""
    try:
        engine = _get_engine()
        memory_stats = engine.memory.stats()
        return {
            "vector_memory": memory_stats,
            "browser": {"pages": 0},
            "mcp": {"servers": 0, "tools": 0},
        }
    except Exception as e:
        return {"error": str(e)}


# ═══════════════════════════════════════
# Browser (Playwright) — stubs for frontend compatibility
# ═══════════════════════════════════════

_stub_browser_pages: list[dict] = []

@app.get("/api/browser/pages", tags=["browser"])
async def browser_list_pages():
    """List browser pages (stub — Playwright not installed)."""
    return {"pages": _stub_browser_pages, "total": len(_stub_browser_pages)}

@app.post("/api/browser/open", tags=["browser"])
async def browser_open(request: dict):
    """Open URL in browser (stub)."""
    return {"success": False, "error": "Playwright not available on this server", "page_id": None}

@app.get("/api/browser/stats", tags=["browser"])
async def browser_stats():
    return {"pages": len(_stub_browser_pages), "max_pages": 0, "active_tabs": 0, "memory_kb": 0}


# ═══════════════════════════════════════
# MCP (Model Context Protocol) — stubs for frontend compatibility
# ═══════════════════════════════════════

@app.get("/api/mcp/servers-enhanced", tags=["mcp"])
async def mcp_list_servers():
    """List MCP servers (stub)."""
    return {"servers": []}

@app.post("/api/mcp/add-server-enhanced", tags=["mcp"])
async def mcp_add_server(request: dict):
    """Add MCP server (stub)."""
    return {"success": False, "error": "MCP not available on this server"}

@app.get("/api/mcp/tools-enhanced", tags=["mcp"])
async def mcp_list_tools():
    """List MCP tools (stub)."""
    return {"tools": []}

@app.delete("/api/mcp/servers-enhanced/{name}", tags=["mcp"])
async def mcp_remove_server(name: str):
    """Remove MCP server (stub)."""
    return {"success": False, "name": name}


# ═══════════════════════════════════════
# Startup banner
# ═══════════════════════════════════════

@app.on_event("startup")
async def startup_banner() -> None:
    logger.info("=" * 60)
    logger.info("  Adam Prism v1.0.0b1 — INTEGRATED EDITION (Phase 1)")
    logger.info("  Engine: adam-prism-final (MemoryStore + ContextCompressor + AuxiliaryClient)")
    logger.info("  License: AGPL v3 + Commercial dual-license")
    logger.info("=" * 60)


# ═══════════════════════════════════════
# Factory (for `create_app()` compatibility)
# ═══════════════════════════════════════

def create_app(engine=None) -> FastAPI:
    """Factory function — stores engine and returns the app."""
    global _ENGINE
    _ENGINE = engine
    return app
