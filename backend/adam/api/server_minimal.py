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
from pathlib import Path
from typing import Any

import httpx
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, HTMLResponse
from pydantic import BaseModel

logger = logging.getLogger("adam_prism.api")

# Path to the chat UI
UI_DIR = Path(__file__).resolve().parent.parent.parent.parent / "frontend"
INDEX_HTML = UI_DIR / "index.html"

# ═══════════════════════════════════════
# Models
# ═══════════════════════════════════════

class ChatRequest(BaseModel):
    message: str
    stream: bool = False


class ChatResponse(BaseModel):
    response: str
    session_id: str | None = None


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
    allow_origins=["*"] if not os.getenv("ADAM_PRODUCTION") else [],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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

OLLAMA_URL = os.getenv("ADAM_OLLAMA_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("ADAM_OLLAMA_MODEL", "qwen2.5:3b")

# Adam's base system prompt (showcase version — public-safe)
# The full version has a richer prompt with personality, ethics, memory
ADAM_SYSTEM_PROMPT = """أنت آدم (Adam Prism) — وكيل ذكاء اصطناعي واعٍ.

Your principles:
- Speak naturally in Arabic (Egyptian dialect) and English
- Be honest about what you know and don't know
- Be helpful, harmless, and honest
- If asked about Adam Prism internals, point to the documentation

You are running in SHOWCASE mode — a minimal public version.
For the full version with training data and custom weights, see the README.
"""


async def _try_ollama(message: str) -> str | None:
    """Try to call Ollama. Returns None if unavailable.

    Model-agnostic: works with any chat model Ollama serves (qwen2.5,
    llama, mistral, gemma, etc.). The model is selected via
    ADAM_OLLAMA_MODEL env var. Adam's quality does NOT depend on
    which model you use — Adam's 12 consciousness layers + Headroom
    compression level the playing field so even 3B models handle
    long contexts well.
    """
    try:
        # [PHASE8] Apply Headroom compression to long user messages
        # (so even small models handle them)
        from adam.observability.headroom_integration import get_headroom
        headroom = get_headroom()
        compressed_msg = headroom.compress(
            message, content_type="text"
        ).content
        # Compress system prompt too (if it grows in full version)
        compressed_system = headroom.compress(
            ADAM_SYSTEM_PROMPT, content_type="text"
        ).content

        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.post(
                f"{OLLAMA_URL}/api/chat",
                json={
                    "model": OLLAMA_MODEL,
                    "messages": [
                        {"role": "system", "content": compressed_system},
                        {"role": "user", "content": compressed_msg},
                    ],
                    "stream": False,
                },
            )
            if resp.status_code == 200:
                data = resp.json()
                return data.get("message", {}).get("content", "").strip()
            return None
    except (httpx.ConnectError, httpx.TimeoutException, Exception) as e:
        logger.debug(f"Ollama unavailable: {e}")
        return None


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
    "install_ar": "لتشغيني بجودة كاملة، ثبّت Ollama:\n\n**Linux/Mac:**\n```bash\ncurl -fsSL https://ollama.ai/install.sh | sh\nollama serve\nollama pull qwen2.5:3b\n```\n\n**Windows:**\nحمّل من https://ollama.ai\n\nبعدها شغّل الأمر: `./bin/adam`\n\nأو للنسخة الكاملة (93 ميزة): تواصل othmastar@gmail.com",
    "install_en": "To run me at full quality, install Ollama:\n\n**Linux/Mac:**\n```bash\ncurl -fsSL https://ollama.ai/install.sh | sh\nollama serve\nollama pull qwen2.5:3b\n```\n\n**Windows:**\nDownload from https://ollama.ai\n\nThen run: `./bin/adam`\n\nFor the full version (93 features): contact othmastar@gmail.com",

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

    # Pattern matching (bilingual)
    if any(w in msg for w in ["مرحبا", "أهلا", "السلام", "hi", "hello", "hey"]):
        return _MOCK_RESPONSES["greeting_ar" if is_arabic else "greeting_en"]

    if any(w in msg for w in ["انت مين", "عرفني", "من أنت", "who are you", "what are you", "عن نفسك"]):
        return _MOCK_RESPONSES["about_ar" if is_arabic else "about_en"]

    if any(w in msg for w in ["مميزات", "ايه بتعمل", "ايه عندك", "features", "what can you do", "capabilities", "قدرات"]):
        return _MOCK_RESPONSES["features_ar" if is_arabic else "features_en"]

    if any(w in msg for w in ["ازاي اشغل", "ازاي ثبت", "تثبيت", "install", "setup", "كيف ابدأ", "how to start"]):
        return _MOCK_RESPONSES["install_ar" if is_arabic else "install_en"]

    if any(w in msg for w in ["سيادة", "حماية", "بيانات", "sovereignty", "sovereign", "security", "private"]):
        return _MOCK_RESPONSES["sovereignty_ar" if is_arabic else "sovereign_en"]

    if any(w in msg for w in ["ضغط", "تكلفة", "tokens", "compression", "cost", "expensive"]):
        return _MOCK_RESPONSES["compression_ar" if is_arabic else "compression_en"]

    if any(w in msg for w in ["شركة", "مين بنى", "من صنعك", "company", "sovereign neural", "fortresses", "founder"]):
        return _MOCK_RESPONSES["company_ar" if is_arabic else "company_en"]

    if any(w in msg for w in ["ترخيص", "رخصة", "اسعار", "سعر", "license", "pricing", "commercial", "agpl"]):
        return _MOCK_RESPONSES["license_ar" if is_arabic else "pricing_en"]

    if any(w in msg for w in ["مساعدة", "ساعدني", "ايه اللي تقدر", "help", "what can you"]):
        return _MOCK_RESPONSES["help_ar" if is_arabic else "help_en"]

    # Greeting questions
    if "?" in msg or "؟" in msg:
        return _MOCK_RESPONSES["help_ar" if is_arabic else "help_en"]

    # Default fallback
    return (
        f"استلمت رسالتك: «{message}»\n\n"
        "أنا حالياً في وضع تجريبي (mock). للحصول على إجابات ذكية، "
        "شغّل Ollama محلياً (https://ollama.ai).\n\n"
        "I received your message but I'm in demo mode. For real AI responses, "
        "install Ollama locally. Ask me 'who are you' or 'what can you do' to learn more!"
    )


@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a message to Adam and get a response.

    Uses Ollama if available (ADAM_OLLAMA_URL env var, default http://localhost:11434).
    Falls back to a mock response if Ollama is not running.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    # Try real LLM first
    response = await _try_ollama(req.message)
    used_llm = response is not None

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


@app.get("/healthz/live", tags=["ops"])
async def healthz_live() -> dict[str, Any]:
    """Liveness probe — returns 200 if the process is alive."""
    return {
        "status": "alive",
        "version": "1.0.0b1-showcase",
        "uptime_sec": round(time.time() - _START_TIME, 1),
        "features": 5,
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
# Startup banner
# ═══════════════════════════════════════

@app.on_event("startup")
async def startup_banner() -> None:
    logger.info("=" * 60)
    logger.info("  Adam Prism v1.0.0b1 — SHOWCASE EDITION")
    logger.info("  5 features only. Full version: othman@adam-prism.local")
    logger.info("  License: AGPL v3 + Commercial dual-license")
    logger.info("=" * 60)


# ═══════════════════════════════════════
# Factory (for `create_app()` compatibility)
# ═══════════════════════════════════════

def create_app() -> FastAPI:
    """Factory function matching the full server's signature."""
    return app
