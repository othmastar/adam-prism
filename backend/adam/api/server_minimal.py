"""
Adam Prism — MINIMAL Showcase Server
=====================================

5 features only (proof of capability):

  1. POST /chat          — Basic chat with system prompt
  2. GET  /healthz/live  — Liveness probe
  3. GET  /docs          — OpenAPI documentation
  4. GET  /metrics       — Prometheus metrics
  5. GET  /api/skills    — List available skills

This is the PUBLIC showcase version. The full version has 93 routes
and is distributed privately under a custom proprietary license
(see DISTRIBUTION.md).

Run: uvicorn adam.api.server_minimal:app --host 0.0.0.0 --port 8000
"""
from __future__ import annotations

import logging
import os
import time
from typing import Any

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

logger = logging.getLogger("adam_prism.api")

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
# Feature 1: /chat (basic, mock LLM)
# ═══════════════════════════════════════

@app.post("/chat", response_model=ChatResponse, tags=["chat"])
async def chat(req: ChatRequest) -> ChatResponse:
    """Send a message to Adam and get a response.

    Showcase version uses a **mock LLM** (deterministic responses).
    Full version connects to Ollama/OpenAI/Anthropic with the trained
    model. See COMMERCIAL_LICENSE.md to upgrade.
    """
    if not req.message.strip():
        raise HTTPException(status_code=400, detail="Empty message")

    # Mock response — full version uses real LLM
    msg = req.message.lower().strip()
    if "مرحبا" in msg or "hi" in msg or "hello" in msg:
        response = "أهلاً بيك! أنا آدم (النسخة التجريبية). اسألني أي سؤال."
    elif "?" in msg or "؟" in msg:
        response = (
            "في النسخة الكاملة، بقدر أجاوب على أسئلتك. "
            "للحصول على النسخة الكاملة: othman@adam-prism.local"
        )
    else:
        response = (
            f"استلمت رسالتك: «{req.message}». "
            "النسخة دي مختصر — مفيش محادثة كاملة. "
            "تواصل معنا للنسخة الكاملة."
        )

    return ChatResponse(response=response, session_id="showcase-session")


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
