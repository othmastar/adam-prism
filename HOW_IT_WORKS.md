# آدم المنظار — شرح المشروع كامل

## هيكلة المشروع

```
Adam_Prism_Complete_v2/
├── adam/                  # 🔥 الباك إنجن (البكج الرئيسي)
│   ├── api/server.py      # FastAPI — 39 route ( /api/chat , /api/status ...)
│   ├── engine/            # قلب آدم: chat.py → generate.py → utils.py
│   │   ├── chat.py        # دورة المحادثة الكاملة
│   │   ├── generate.py    # بناء البرومبت + اختيار طريقة التوليد
│   │   └── utils.py       # _call_lora_server — يضرب على LoRA
│   ├── core/learning.py   # التعليم المستمر
│   ├── memory/            # Qdrant vector store
│   ├── security/guard.py  # anti-prompt-injection
│   ├── ethics/gate.py     # البوابة الأخلاقية
│   ├── tools/manager.py   # مدير الأدوات (terminal, browser, etc)
│   └── eyes/browser.py    # Playwright browser automation
├── scripts/
│   └── inference_server.py # 🧠 سيرفر LoRA — يشغّل Gemma 4 + V87 adapter
├── web-ui/                # 🎨 الفرونت إند (Next.js + Tailwind v4)
│   └── src/
│       ├── app/page.tsx        # الصفحة الرئيسية
│       ├── components/adam/    # chat-interface.tsx + chat-sidebar.tsx
│       └── lib/
│           ├── api.ts          # ⚡ العميل اللي يضرب على الباك (fetch /api/chat)
│           └── store.ts        # Zustand store (حالة المحادثات)
├── config/default.json    # الإعدادات الأساسية
├── start.sh               # تشغيل كل حاجة بأمر واحد
└── main.py                # مدخل الباك إند
```

---

## ازاي الكود بيتحرك من أول ما تكتب رسالة?

### 1. الفرونت إند (المتصفح)
- بتكتب رسالة في `chat-interface.tsx`
- بتضغط Enter → `sendChatMessage()` في `api.ts`
- function دي بتعمل:

```
POST http://localhost:8002/api/chat
  Body: { "message": "...", "context": {...}, "voice": true }
```

### 2. الباك إند (FastAPI على port 8002)
- `adam/api/server.py` بيستقبل الطلب
- بينادي `engine.chat(message, context)` في `adam/engine/chat.py`

### 3. دورة المحادثة (chat.py)
مرحلة بمرحلة:

| الخطوة | المكان | بتعمل إيه |
|--------|--------|-----------|
| 1. أمن | `security/guard.py` | تفحص الرسالة لو فيها injection |
| 2. تصنيف | `chat.py` | تحدد نية المستخدم (سؤال/أداة/أمر) |
| 3. سياق | `chat.py` | تجيب الذكريات من Qdrant |
| 4. توليد | `generate.py` | تختار LoRA أو Ollama حسب الإعدادات |
| 5. أدوات | `chat.py` | لو عايز يفتح متصفح أو يشغّل أمر |
| 6. إنهاء | `chat.py` | يسجل في الذاكرة ويولّد صوت |

### 4. التوليد (generate.py → utils.py)

```
_generate() في generate.py
  │
  ├─ هل inference_mode == "lora"?
  │     └─ نعم → _call_lora_server() في utils.py
  │              │
  │              └─ POST http://localhost:8080/chat
  │                   { "messages": [ {"role":"system",...}, {"role":"user",...} ] }
  │
  └─ لو لا → استخدم Ollama في provider/ollama.py
```

### 5. LoRA Inference Server (على port 8080)
- `scripts/inference_server.py` بيستقبل الطلب
- بيعمل `tokenizer.apply_chat_template(messages)` ← يحولها لـ tokens
- بيعمل `model.generate(...)` على Gemma 4 E4B + V87 adapter
- بيرجع `{ "response": "..." }`

### 6. الرجوع للفرونت
- الباك إند ياخد الرد، يضيفه في `ChatResponse`
- يرجع JSON للفرونت إند
- الفرونت إند يعرضه في الشات

---

## تشغيل الخدمات

### ▶️ تشغيل كل حاجة (أمر واحد)
```bash
cd /mnt/Workspace/Adam_Prism_Complete_v2
./start.sh
```

ده يعمل الآتي بالترتيب:
1. **LoRA Server** → port `8080` (ينتظر حتى يكون جاهز)
2. **API Server** → port `8002`
3. **Frontend** → port `3000`

الـ Logs:
- `/tmp/lora-server.log`
- `/tmp/main-api.log`
- `/tmp/frontend.log`

### ⏹️ إيقاف الخدمات

```bash
# وقف كل حاجة
kill $(lsof -t -i:3000 -i:8002 -i:8080) 2>/dev/null

# أو باليد:
ps aux | grep -E "inference_server|main.py|next" | grep -v grep | awk '{print $2}' | xargs -r kill
```

### 🩺 اختبار إن كل حاجة شغالة

```bash
# اختبار LoRA
curl http://localhost:8080/health

# اختبار API
curl http://localhost:8002/api/status

# اختبار الدردشة كاملة
curl -X POST http://localhost:8002/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message":"ازيك يا صاحبي"}'

# اختبار الفرونت إند (افتح في المتصفح)
# http://localhost:3000
```

---

## الخريطة الكاملة للـ Data Flow

```
المستخدم (المتصفح)
    │
    ▼
chat-interface.tsx   ← web-ui/src/components/adam/
    │
    ▼
api.ts: sendChatMessage()  ← web-ui/src/lib/
    │
    ▼  POST http://localhost:8002/api/chat
    │
adam/api/server.py: chat()  ← يستقبل الطلب
    │
    ▼
adam/engine/chat.py: chat()  ← دورة المحادثة
    │
    ├─ security/guard.py          ← فحص أمني
    ├─ chat.py: classify_intent() ← تصنيف النية
    ├─ memory/                    ← سياق + ذكريات
    │
    ▼
adam/engine/generate.py: _generate()
    │
    ├─ inference_mode == "lora"?
    │     │
    │     ▼
    │   adam/engine/utils.py: _call_lora_server()
    │     │
    │     ▼  POST http://localhost:8080/chat
    │     │
    │   scripts/inference_server.py ← Gemma 4 + V87
    │     │
    │     └─ model.generate() → رد بالعربي المصري
    │
    ▼
adam/engine/chat.py ← أدوات (tools) لو محتاج
    │
    ▼
adam/engine/chat.py ← تخزين في الذاكرة + صوت
    │
    ▼
JSON Response → الفرونت إند يعرض الرد
```

---

## الملفات المهمة اللي محتاج تعرفها

| الملف | الوظيفة |
|-------|---------|
| `scripts/inference_server.py` | 🧠 يحمّل Gemma 4 (4-bit) + V87 LoRA على GPU |
| `adam/engine/utils.py` | ⚡ `_call_lora_server()` — يضرب على LoRA |
| `adam/engine/generate.py` | يختار طريقة التوليد (LoRA / Ollama / OpenAI) |
| `adam/engine/chat.py` | دورة المحادثة الكاملة (الأمن ← السياق ← التوليد ← الأدوات) |
| `adam/api/server.py` | 39 route API (الدردشة، الحالة، tools، skills) |
| `web-ui/src/lib/api.ts` | عميل الفرونت إند (sendChatMessage، getConversations) |
| `web-ui/src/lib/store.ts` | حالة التطبيق (المحادثات، الإعدادات) |
| `web-ui/src/components/adam/chat-interface.tsx` | واجهة الشات الرئيسية |
| `config/default.json` | الإعدادات (inference_mode, lora_server_url, ports) |
