# دليل تعلم Adam Prism — Architecture & Routing الشامل

## 📚 المحتويات

1. [نظرة عامة على الـ Architecture](#1-نظرة-عامة)
2. [كيف يشتغل الـ Request Flow](#2-request-flow)
3. [الـ Frontend Routing](#3-frontend-routing)
4. [الـ Backend Routing](#4-backend-routing)
5. [الـ Tool Routing (كيف الموديل يختار أداة)](#5-tool-routing)
6. [الـ Memory Routing (كيف الذاكرة بتشتغل)](#6-memory-routing)
7. [الـ Provider Routing (Ollama vs LoRA vs OpenAI)](#7-provider-routing)
8. [الـ Channel Routing (WhatsApp, Telegram, etc)](#8-channel-routing)
9. [الـ Security Routing (WAF, Ethics, Guard)](#9-security-routing)
10. [كيف تـ debug أي مشكلة](#10-debug-guide)
11. [كيف تضيف ميزة جديدة](#11-add-feature)
12. [خريطة طريق للتعلم](#12-learning-path)

---

## 1. نظرة عامة

Adam Prism مبني بـ **3-tier architecture**:

```
┌─────────────────────────────────────────────────┐
│           FRONTEND (Next.js + React)            │
│                                                  │
│  chat-interface.tsx                              │
│    ↓ calls                                       │
│  lib/api.ts (HTTP client)                        │
│    ↓ fetch                                       │
│  Next.js proxy (next.config.ts rewrites)         │
└──────────────────────┬──────────────────────────┘
                       │ HTTP /api/*
                       ▼
┌─────────────────────────────────────────────────┐
│           BACKEND (FastAPI + Python)             │
│                                                  │
│  api/server.py (100+ endpoints)                  │
│    ↓ calls                                        │
│  engine/chat.py (main loop)                      │
│    ↓ calls                                        │
│  engine/base.py (module orchestration)           │
│    ↓ uses                                         │
│  memory/, security/, ethics/, tools/, eyes/      │
└──────────────────────┬──────────────────────────┘
                       │ HTTP/gRPC
                       ▼
┌─────────────────────────────────────────────────┐
│           EXTERNAL SERVICES                      │
│                                                  │
│  • Ollama (LLM inference) — :11434              │
│  • LoRA server (gemma4 12b) — :7861             │
│  • Qdrant (vector DB) — :6333                    │
│  • SQLite (sessions, memory) — local file        │
│  • Playwright (browser) — subprocess              │
└─────────────────────────────────────────────────┘
```

### الـ Layers (12 consciousness layer):

| # | Layer | الوظيفة | الملف |
|---|---|---|---|
| 1 | Provider Management | اختيار LLM | `providers/manager.py` |
| 2 | Context Engine | بناء RAG context | `engine/context.py` |
| 3 | Security Guard | input/output/tool guards | `security/guard.py` |
| 4 | Tool Orchestration | تنفيذ الأدوات | `engine/tools/` |
| 5 | Iron Memory | 4 طبقات ذاكرة | `memory/*.py` |
| 6 | Learning Engine | تعلم مستمر | `learning/closed_loop.py` |
| 7 | Ethics Gate | 4 قوانين أخلاقية | `ethics/gate.py` |
| 8 | Channel Hub | 25 قناة تواصل | `channels/manager.py` |
| 9 | Subagent Teams | swarm orchestration | `subagents/teams.py` |
| 10 | Voice Pipeline | STT + TTS | `core/voice.py` |
| 11 | Meta Learner | skill generation | `core/meta_learner.py` |
| 12 | Ethics Reflection | self-verification | `engine/chat.py` |

---

## 2. Request Flow

لما المستخدم يبعت رسالة، الـ flow بيكون:

```
1. المستخدم يكتب في chat-interface.tsx
   ↓
2. handleSend() في chat-interface.tsx
   - يبني payloadMessage
   - لو فيه ملف: uploadFile() الأول
   - يدخل payloadMessage في sendChatMessage()
   ↓
3. lib/api.ts → sendChatMessage()
   - POST /api/chat
   - body: { message, context, voice }
   ↓
4. Next.js proxy (next.config.ts)
   - rewrite /api/* → http://localhost:8000/api/*
   ↓
5. FastAPI: api/server.py → chat() endpoint
   - يستقبل ChatRequest
   - ينادي engine.chat(message, context)
   ↓
6. engine/chat.py → chat()
   - فحص أمني (security/guard.py)
   - تصنيف القصد (intent classification)
   - بناء السياق (memory recall + RAG)
   - استدعاء الموديل (_generate)
   - تنفيذ الأدوات لو موجودة
   - حفظ في الذاكرة + notebook
   - فحص إخراج (output guard)
   ↓
7. engine/generate.py → _generate()
   - يبني system prompt
   - يبني messages array
   - يستدعي provider (LoRA أو Ollama)
   ↓
8. providers/manager.py → ProviderManager
   - يختار الـ provider المناسب
   - auto-fallback لو الأول فشل
   ↓
9. External LLM (LoRA server أو Ollama)
   - يرجع response text
   ↓
10. engine/chat.py → _process_tool_calls()
    - لو فيه <tool_call> في الرد
    - ينفذ الأداة
    - يبعت النتيجة للموديل مرة تانية
   ↓
11. engine/chat.py → _chat_finalize()
    - حفظ في conversation_history
    - حفظ في notebook
    - حفظ في Qdrant
    - تسجيل trace
    - output guard
   ↓
12. FastAPI: يرجع ChatResponse JSON
   ↓
13. Next.js proxy: يمرر الـ response
   ↓
14. chat-interface.tsx: يعرض الرد للمستخدم
```

### مثال عملي:

```typescript
// 1. المستخدم يكتب: "اقرأ ملف /tmp/test.txt"
// 2. chat-interface.tsx:
const result = await sendChatMessage("اقرأ ملف /tmp/test.txt", {
  history: messages.slice(-10),
});

// 3. POST /api/chat
// body: { message: "اقرأ ملف /tmp/test.txt", context: { history: [...] } }

// 4. backend server.py → engine.chat()
// 5. engine ينادي الموديل
// 6. الموديل يرد بـ:
//    <tool_call>{"name":"file_read","arguments":{"path":"/tmp/test.txt"}}</tool_call>
// 7. engine ينفذ file_read
// 8. النتيجة: { content: "محتوى الملف..." }
// 9. engine يبعت النتيجة للموديل تاني
// 10. الموديل يرد: "الملف يحتوي على..."
// 11. engine يرجع: { response: "الملف يحتوي على..." }
```

---

## 3. Frontend Routing

الـ frontend Next.js بيستخدم **App Router** (الجديد):

### الـ pages:

```
src/app/
├── page.tsx              → /          (الصفحة الرئيسية - chat)
├── layout.tsx            → (wrapper لكل الصفحات)
├── admin/dashboard/      → /admin/dashboard
├── login/                → /login
├── register/             → /register
├── offline/              → /offline
├── error.tsx             → (error boundary)
├── global-error.tsx      → (global error)
└── api/                  → (API routes - serverless functions)
    ├── auth/[...nextauth]/  → /api/auth/*
    ├── health/              → /api/health
    ├── models/              → /api/models
    └── route.ts             → /api
```

### الـ API Proxy (مهم جداً):

في `next.config.ts` فيه rewrites:

```typescript
async rewrites() {
  return [
    { source: "/api/:path*", destination: "http://localhost:8000/api/:path*" },
    { source: "/ws/:path*", destination: "http://localhost:8000/ws/:path*" },
    { source: "/healthz/:path*", destination: "http://localhost:8000/healthz/:path*" },
    { source: "/metrics", destination: "http://localhost:8000/metrics" },
    { source: "/docs", destination: "http://localhost:8000/docs" },
  ];
}
```

**يعني:** أي request لـ `/api/*` على Next.js (port 3000) بيتحويل لـ FastAPI (port 8000).

### الـ Components hierarchy:

```
app/page.tsx
  └── chat-interface.tsx (المكون الرئيسي)
        ├── chat-sidebar.tsx (قائمة الجلسات)
        ├── tools-panel.tsx (لوحة الأدوات)
        ├── settings-panel.tsx (الإعدادات)
        ├── knowledge-panel.tsx (قاعدة المعرفة)
        ├── memory-panel.tsx (الذاكرة)
        ├── notebook-panel.tsx (الدفتر)
        ├── subagent-dashboard.tsx (الوكلاء الفرعيين)
        ├── skills-panel.tsx (المهارات)
        ├── plugin-manager.tsx (الإضافات)
        ├── scheduler-dashboard.tsx (المجدول)
        ├── channels-panel.tsx (القنوات)
        ├── floating-monitor.tsx (المراقب)
        ├── pipeline-monitor.tsx (الـ pipeline)
        ├── system-dashboard.tsx (النظام)
        ├── voice-button.tsx (الصوت)
        ├── permission-dialog.tsx (الحوار)
        └── action-trace.tsx (trace)
```

### الـ State Management:

الـ frontend بيستخدم **Zustand** (مش Redux):

```typescript
// lib/store.ts
type AppState = {
  conversations: Conversation[];
  activeConversationId: string | null;
  settings: AppSettings;
  apiConnected: boolean;
  // ...
};

// استخدام:
const { conversations, addConversation } = useAppStore();
```

**ليه Zustand مش Redux؟**
- أبسط بكتير (مش محتاج actions, reducers, dispatch)
- أصغر حجماً
- أسرع

---

## 4. Backend Routing

الـ backend FastAPI بيستخدم ** decorators**:

```python
@app.post("/api/chat")          # POST فقط
@app.get("/api/chat/sessions")  # GET فقط
@app.delete("/api/chat/sessions/{session_id}")  # DELETE مع path param
@app.websocket("/ws/chat")      # WebSocket
```

### الـ endpoints المنظمة حسب الـ function:

| الـ endpoint | الملف | الوظيفة |
|---|---|---|
| `POST /api/chat` | server.py | دردشة |
| `GET /api/chat/sessions` | server.py | قائمة الجلسات |
| `POST /api/chat/upload` | server.py | رفع ملفات |
| `POST /api/memory/store` | server.py | حفظ ذاكرة |
| `GET /api/memory/recall` | server.py | استرجاع ذاكرة |
| `POST /api/ltm/store` | server.py | حفظ LTM (vector) |
| `GET /api/ltm/search` | server.py | بحث LTM hybrid |
| `GET /api/tools/manifest` | server.py | قائمة الأدوات |
| `POST /api/tools/action` | server.py | تنفيذ أداة |
| `POST /api/browser/open` | server.py | فتح URL |
| `POST /api/mcp/add-server` | server.py | إضافة MCP server |
| `GET /api/engine/health` | server.py | صحة الـ engine |
| `GET /metrics` | server.py | Prometheus metrics |

### الـ Middleware chain:

```
Request
  ↓
1. CORS middleware (السماح بالـ origins)
  ↓
2. WAF middleware (فحص OWASP Top 10)
  ↓
3. Rate limiter middleware (منع الـ spam)
  ↓
4. Auth middleware (لو protected endpoint)
  ↓
5. Route handler (الـ endpoint الفعلي)
  ↓
6. Response middleware (إضافة headers)
  ↓
Response
```

---

## 5. Tool Routing

كيف الموديل يختار أداة؟

### الـ Tool Registry:

في `engine/tools/unified_schema.py`:

```python
TOOL_REGISTRY = {
    "browser_open": ToolDefinition(
        name="browser_open",
        description="Open a URL in the browser",
        parameters={"url": {"type": "string"}},
        required=["url"],
    ),
    "file_read": ToolDefinition(...),
    "memory_store": ToolDefinition(...),
    # ... 32 أداة
}
```

### الـ Tool Calling Format:

الموديل بيتعلم إنه يكتب:

```
<tool_call>
{"name": "file_read", "arguments": {"path": "/tmp/test.txt"}}
</tool_call>
```

### الـ Tool Dispatch Flow:

```
1. الموديل يرد بـ: <tool_call>{"name":"file_read","arguments":{...}}</tool_call>
   ↓
2. engine/chat.py → _parse_tool_request()
   - يستخرج الـ JSON من الـ <tool_call> tags
   - يرجع: {"_tool": "file_read", "params": {"path": "..."}}
   ↓
3. engine/tools/__init__.py → _execute_tool()
   - يفحص الصلاحيات (security/guard.py)
   - يوزع على الـ handler المناسب:
     - browser_* → _tool_browser()
     - file_* → _tool_file()
     - memory_* → _tool_memory()
     - shell → _tool_shell()
     - python_exec → _tool_python()
     - search_knowledge → _tool_knowledge()
   ↓
4. الـ handler ينفذ الأداة
   - مثلاً: _tool_file("file_read", {"path": "/tmp/test.txt"})
   - يقرا الملف ويرجع: {"success": True, "content": "..."}
   ↓
5. engine/chat.py يبعت النتيجة للموديل
   - "نتيجة file_read:\n{...}\n\nرد على المستخدم."
   ↓
6. الموديل يرد بالـ final response
```

---

## 6. Memory Routing

عندك **4 طبقات ذاكرة**:

```
┌─────────────────────────────────────────┐
│ Layer 1: Hot Memory (MEMORY.md)          │
│ - ذاكرة سريعة جداً                        │
│ - بـ markdown                             │
│ - 0 token cost (في system prompt)         │
└──────────────────┬──────────────────────┘
                   ↓ لو محتاج أعمق
┌─────────────────────────────────────────┐
│ Layer 2: Session Search (FTS5)           │
│ - بحث في الجلسة الحالية                   │
│ - SQLite + FTS5                          │
│ - ~20ms latency                          │
└──────────────────┬──────────────────────┘
                   ↓ لو محتاج cross-session
┌─────────────────────────────────────────┐
│ Layer 3: Vector Memory (Qdrant)          │
│ - semantic search                        │
│ - nomic-embed-text embeddings            │
│ - cross-session recall                   │
└──────────────────┬──────────────────────┘
                   ↓ لو محتاج skills
┌─────────────────────────────────────────┐
│ Layer 4: Skills Index                    │
│ - مهارات متعلمة                          │
│ - progressive disclosure                 │
└─────────────────────────────────────────┘
```

### الـ Memory Recall Flow:

```
1. المستخدم يكتب: "اذكرلي آخر مرة اتكلمنا عن Python"
   ↓
2. engine/context.py → _build_context()
   - يبحث في Layer 1 (Hot Memory) — فوري
   - يبحث في Layer 2 (Session Search) — FTS5
   - يبحث في Layer 3 (Vector Memory) — semantic
   - يبحث في Layer 4 (Skills) — لو relevant
   ↓
3. يدمج النتائج في system prompt
   - "[MEMORY]\n- ذكرى 1\n- ذكرى 2\n..."
   ↓
4. الموديل يرد بناءً على الذكريات
```

---

## 7. Provider Routing

عندك **3 providers** بـ auto-fallback:

```
┌─────────────────────────────────────┐
│ ProviderManager                     │
│                                     │
│ 1. LoRA server (gemma4 12b)         │
│    - الأسرع (محلي)                   │
│    - الأقوى (fine-tuned)             │
│    - لو فشل ↓                       │
│                                     │
│ 2. Ollama (qwen2.5:3b)              │
│    - fallback                        │
│    - أبطأ بس موثوق                   │
│    - لو فشل ↓                       │
│                                     │
│ 3. OpenAI / Anthropic (اختياري)     │
│    - cloud fallback                  │
│    - أغلى                            │
└─────────────────────────────────────┘
```

### الـ Provider Selection Logic:

```python
# providers/manager.py
class ProviderManager:
    def __init__(self, config):
        self._providers = {
            "ollama": OllamaProvider(config),
            "openai": OpenAIProvider(config) if config.get("openai_api_key") else None,
            "anthropic": AnthropicProvider(config) if config.get("anthropic_api_key") else None,
        }
        self.mode = config.get("inference_mode", "ollama")
        self.current = self._providers.get(self.mode)

    async def chat(self, messages):
        try:
            return await self.current.chat(messages)
        except Exception as e:
            # fallback
            for provider in self._providers.values():
                if provider and provider != self.current:
                    try:
                        result = await provider.chat(messages)
                        self.current = provider  # switch
                        return result
                    except:
                        continue
            raise e  # كلهم فشلوا
```

---

## 8. Channel Routing

عندك **25 قناة تواصل**:

```
┌─────────────────────────────────────────┐
│ ChannelManager                           │
│                                          │
│  • WhatsApp (webhook)                    │
│  • Telegram (bot polling)                │
│  • Discord (bot gateway)                 │
│  • Slack (webhook)                       │
│  • Email (IMAP/SMTP)                     │
│  • Signal                                │
│  • Matrix                                │
│  • ... (19 قناة تانية)                   │
└─────────────────────────────────────────┘
```

### الـ Channel Flow:

```
1. رسالة تيجي من WhatsApp
   ↓
2. channels/whatsapp.py → receive_message()
   - يفك التشفير (signature verification)
   - يستخرج النص
   ↓
3. channels/manager.py → route_to_engine()
   - ينادي engine.chat(message, context)
   ↓
4. engine يعالج الرسالة (زي ما شوفنا)
   ↓
5. channels/whatsapp.py → send_message()
   - يبعت الـ response لـ WhatsApp API
```

---

## 9. Security Routing

3 طبقات حماية:

```
Request
  ↓
┌─────────────────────────────────────────┐
│ Layer 1: WAF (Web Application Firewall)  │
│ - فحص OWASP Top 10                       │
│ - SQL injection, XSS, path traversal     │
│ - command injection, SSRF                │
│ - لو خطر: block فوراً                    │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ Layer 2: Security Guard                  │
│ - InputGuard: فحص الـ user input         │
│ - ToolGuard: فحص قبل تنفيذ أداة          │
│ - OutputGuard: فحص الـ response          │
└──────────────────┬──────────────────────┘
                   ↓
┌─────────────────────────────────────────┐
│ Layer 3: Ethics Gate                     │
│ - 4 قوانين: عدالة، تعلم، بقاء، إبداع     │
│ - LLM evaluation                         │
│ - لو رفض: block الـ response             │
└─────────────────────────────────────────┘
```

---

## 10. Debug Guide

لما تواجه مشكلة، اتبع الـ flow ده:

### خطوة 1: تحقق من الـ Frontend

افتح DevTools (F12):

```
Console tab → شوف أي errors
Network tab → شوف الـ requests
  - /api/chat → status code؟
  - /api/chat/upload → response فيه text_content؟
```

### خطوة 2: تحقق من الـ Backend

```bash
# شغل بـ verbose logging
uvicorn adam.api.server:app --port 8000 --log-level debug 2>&1 | tee /tmp/adam.log

# شوف الـ logs
tail -f /tmp/adam.log | grep -E "ERROR|WARN|chat|tool"
```

### خطوة 3: تحقق من الـ Services

```bash
# Ollama
curl http://localhost:11434/api/tags

# LoRA server
curl http://localhost:7861/

# Qdrant
curl http://localhost:6333/collections

# Adam health
curl http://localhost:8000/api/engine/health
```

### خطوة 4: تحقق من الـ Data

```bash
# sessions DB
sqlite3 ~/.adam/sessions.db "SELECT COUNT(*) FROM sessions;"

# memory DB
sqlite3 ~/.adam/memory.db "SELECT COUNT(*) FROM memories;"

# vector memory DB (لو موجود)
sqlite3 ~/.adam/vector_memory.db "SELECT COUNT(*) FROM vector_memories;"
```

### خطوة 5: اختبار isolé

```bash
# جرّب chat مباشرة (من غير frontend)
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "مرحبا"}'

# جرّب upload مباشرة
curl -X POST http://localhost:8000/api/chat/upload \
  -F "file=@/tmp/test.txt"

# جرّب tool مباشرة
curl -X POST http://localhost:8000/api/tools/action \
  -H "Content-Type: application/json" \
  -d '{"name": "disk_space", "arguments": {}}'
```

---

## 11. How to Add a New Feature

### مثال: إضافة أداة جديدة "send_email"

#### خطوة 1: عرف الـ tool في `unified_schema.py`

```python
"send_email": ToolDefinition(
    name="send_email",
    description="Send an email",
    parameters={
        "to": {"type": "string", "description": "Recipient email"},
        "subject": {"type": "string", "description": "Email subject"},
        "body": {"type": "string", "description": "Email body"},
    },
    required=["to", "subject", "body"],
),
```

#### خطوة 2: اكتب الـ handler في `engine/tools/`

```python
# engine/tools/email.py
class EmailToolsMixin:
    async def _tool_email(self, tool_name: str, params: dict) -> dict:
        if tool_name == "send_email":
            return await self._send_email(
                params["to"], params["subject"], params["body"]
            )

    async def _send_email(self, to, subject, body):
        # استخدم smtplib
        import smtplib
        from email.mime.text import MIMEText
        # ... implementation
        return {"success": True, "sent_to": to}
```

#### خطوة 3: أضفه للـ dispatcher في `engine/tools/__init__.py`

```python
# في _execute_tool():
elif tool_name == "send_email":
    result = await self._tool_email(tool_name, params)
```

#### خطوة 4: أضفه للـ Mixin chain

```python
class AdamPrismEngineTools(
    # ... existing mixins
    EmailToolsMixin,  # جديد
    AdamPrismEngineGenerate,
):
```

#### خطوة 5: أضفه للـ system prompt

في `engine/generate.py`:

```python
def _build_tool_registry_prompt(self) -> str:
    return """
    ...
    📧 **email** → send_email(to, subject, body)
    ...
    """
```

#### خطوة 6: اختبر

```bash
curl -X POST http://localhost:8000/api/tools/action \
  -H "Content-Type: application/json" \
  -d '{
    "name": "send_email",
    "arguments": {
      "to": "test@example.com",
      "subject": "Test",
      "body": "Hello from Adam"
    }
  }'
```

---

## 12. Learning Path

### المستوى 1: أساسيات (أسبوع)

1. **Python async/await**
   - `asyncio.run()`, `await`, `asyncio.gather()`
   - مهم جداً لأن كل الكود async

2. **FastAPI basics**
   - `@app.get()`, `@app.post()`
   - Pydantic models
   - Dependency injection

3. **Next.js App Router**
   - `app/page.tsx` structure
   - Server vs Client components
   - `next.config.ts` rewrites

### المستوى 2: فهم الـ architecture (أسبوعين)

1. **اقرا الكود بالترتيب ده:**
   - `main.py` (entry point)
   - `backend/adam/api/server.py` (endpoints)
   - `backend/adam/engine/base.py` (engine init)
   - `backend/adam/engine/chat.py` (main loop)
   - `backend/adam/engine/generate.py` (LLM call)
   - `backend/adam/engine/context.py` (RAG)

2. **افهم الـ Mixin chain:**
   ```python
   AdamPrismEngineBase
     → AdamPrismEngineUtils
       → AdamPrismEngineContext
         → AdamPrismEngineGenerate
           → AdamPrismEngineTools
             → AdamPrismEngineChat
   ```
   ده pattern اسمه **mixin inheritance** — بيسمح بإضافة methods من غير ما تعدل الـ base class.

3. **افهم الـ Provider pattern:**
   - `providers/base.py` (interface)
   - `providers/ollama.py`, `openai.py`, `anthropic.py` (implementations)
   - `providers/manager.py` (routing + fallback)

### المستوى 3: التعمق (شهر)

1. **Memory system:**
   - Qdrant vector DB
   - Embeddings (nomic-embed-text)
   - Hybrid search (BM25 + Vector)

2. **Security:**
   - OWASP Top 10
   - SSRF protection
   - Sandbox design

3. **MCP protocol:**
   - JSON-RPC
   - stdio transport
   - Tool discovery

### المستوى 4: المساهمة (مستمر)

1. **أضف tools جديدة**
2. **أضف channels جديدة**
3. **حسّن الـ prompts**
4. **اكتب tests**

---

## 📖 Resources للتعلم

### Python:
- [Real Python - Async IO](https://realpython.com/async-io-python/)
- [FastAPI docs](https://fastapi.tiangolo.com/)

### TypeScript/Next.js:
- [Next.js App Router](https://nextjs.org/docs/app)
- [React hooks](https://react.dev/reference/react)

### AI/LLM:
- [LangChain concepts](https://python.langchain.com/docs/concepts/)
- [Ollama API](https://github.com/ollama/ollama/blob/main/docs/api.md)

### Architecture:
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)
- [12-Factor App](https://12factor.net/)

---

## 🎯 الخلاصة

Adam Prism مبني بـ **modular architecture**:
- كل module لوحده (memory, security, tools, etc.)
- بيتكلموا مع بعض عبر الـ engine
- تقدر تستبدل أي module من غير ما تكسر الباقي

**السر:** افهم الـ **request flow** الأول (قسم 2). لما تفهم رسالة المستخدم بتعدّ بإيه من الـ frontend للـ LLM وترجع، كل حاجة هتبقى واضحة.

لو فيه أي حاجة مش واضحة، ارجع للقسم الخاص بيها. ولو لسه مش واضح، اسألني.
