"""
Mock Ollama Server — للاختبار في بيئة افتراضية
يحاكي Ollama API بـ responses حقيقية
"""

import asyncio
import json
import time
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Mock Ollama")

# الموديلات المتاحة (محاكاة)
AVAILABLE_MODELS = [
    {"name": "gemma4:12b", "size": 8100000000, "modified_at": "2024-01-01T00:00:00Z"},
    {"name": "qwen2.5:0.5b", "size": 500000000, "modified_at": "2024-01-01T00:00:00Z"},
    {"name": "nomic-embed-text", "size": 137000000, "modified_at": "2024-01-01T00:00:00Z"},
    {"name": "adam-prism-v13", "size": 4200000000, "modified_at": "2024-01-01T00:00:00Z"},
]

@app.get("/api/tags")
async def list_models():
    """يرجع الموديلات المتاحة."""
    return {"models": AVAILABLE_MODELS}

@app.post("/api/chat")
async def chat(request: Request):
    """يحاكي chat endpoint."""
    data = await request.json()
    model = data.get("model", "qwen2.5:0.5b")
    messages = data.get("messages", [])

    # استخرج آخر user message
    user_msg = ""
    for m in reversed(messages):
        if m.get("role") == "user":
            user_msg = m.get("content", "")
            break

    # رد ذكي حسب الموديل
    if model == "gemma4:12b":
        # gemma4 بيرجع thinking فاضي (المشكلة الأصلية)
        # بس لو السؤال بسيط، بيرجع content
        if "مرحبا" in user_msg or "hello" in user_msg.lower():
            content = "أهلاً بيك! أنا آدم، التوأم الرقمي. كيف أقدر أساعدك؟"
            thinking = ""
        else:
            # gemma4 بيرجع الرد في thinking أحياناً
            content = ""
            thinking = f"أهلاً! أنا آدم. استلمت رسالتك: '{user_msg[:50]}'. سأساعدك في هذا."
    elif model == "qwen2.5:0.5b":
        # qwen بيرد سريع وصحيح
        if "مرحبا" in user_msg:
            content = "أهلاً بيك! أنا آدم. أقدر أساعدك في البرمجة، تحليل الملفات، والذاكرة."
        elif "كود" in user_msg or "code" in user_msg.lower():
            content = "إليك كود بسيط:\n\n```python\nprint('Hello from Adam!')\n```"
        elif "ملف" in user_msg or "FILE" in user_msg:
            content = "استلمت الملف. سأحلل محتواه وأرد عليك بالتفاصيل."
        else:
            content = f"استلمت رسالتك: '{user_msg[:100]}'. أنا آدم، التوأم الرقمي لمحمد عثمان."
        thinking = ""
    else:
        content = f"Response from {model}: {user_msg[:50]}"
        thinking = ""

    # أضف delay بسيط لمحاكاة الـ inference
    await asyncio.sleep(0.5)

    return {
        "model": model,
        "created_at": "2024-01-01T00:00:00Z",
        "message": {
            "role": "assistant",
            "content": content,
            "thinking": thinking,
        },
        "done": True,
        "done_reason": "stop",
        "total_duration": 500_000_000,  # 500ms
        "load_duration": 100_000_000,
        "prompt_eval_count": 50,
        "prompt_eval_duration": 200_000_000,
        "eval_count": 30,
        "eval_duration": 200_000_000,
    }

@app.post("/api/embeddings")
async def embeddings(request: Request):
    """يحاكي embeddings endpoint."""
    data = await request.json()
    prompt = data.get("prompt", "")

    # رجع vector بـ 768 dimension (nomic-embed-text)
    import random
    random.seed(hash(prompt) % 2**32)
    embedding = [random.uniform(-1, 1) for _ in range(768)]

    return {"embedding": embedding}

@app.get("/")
async def root():
    return {"message": "Mock Ollama Server", "version": "1.0"}


if __name__ == "__main__":
    print("Starting Mock Ollama on :11434...")
    uvicorn.run(app, host="0.0.0.0", port=11434, log_level="warning")
