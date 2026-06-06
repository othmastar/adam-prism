# آدم بريزم — Adam Prism
### التوأم الرقمي الواعي — Egyptian Arabic Conscious AI

**آدم بريزم** هو توأم رقمي شخصي — مش chatbot عادي. عين الحارس المُهندسة بـ 12 طبقة وعي، ذاكرة طويلة المدى، بوابة أخلاقية، وحماية أمنية. بيتكلم مصري طبيعي وبيشتغل محلياً على جهازك.

> "أنا مش أداة إنتاجية — أنا عين الحارس"

---

## المميزات

- **🧠 7 Cognitive Modes** — يختار تلقائياً الوضع المناسب: Strategic Analyst, Technical Researcher, Software Dev, Pen Tester, Systems Analyst, Knowledge Manager, Teacher
- **📚 ذاكرة طويلة المدى** — Qdrant vector DB + Nomic Embeddings (6 collections)
- **🔒 أمان متعدد الطبقات** — Injection detection عربي/إنجليزي، 19 أداة مع rate limits
- **⚖️ بوابة أخلاقية** — 4 قوانين: العدل 40%، نشر العلم 30%، البقاء 20%، الإبداع 10%
- **🎤 Voice Pipeline** — VAD + ASR (faster-whisper) + TTS (Edge TTS)
- **🌐 Web UI** — Next.js 14 مع RTL/LTR، dark/light، WebSocket، SSE
- **🔧 أدوات متكاملة** — متصفح، ملفات، شيل، ذاكرة، نوته، معرفة
- **📱 Telegram Bot** — channels/pipeline/channels.py
- **🎯 QLoRA Fine-tuning** — مدرب على Gemma 4 E4B بهوية مصرية

---

## المتطلبات

| الحاجة | الغرض |
|--------|-------|
| Python 3.12+ | المحرك الأساسي |
| [Ollama](https://ollama.com) | تشغيل النموذج (GGUF) |
| [Qdrant](https://qdrant.tech) | قاعدة بيانات شعاعية (اختياري — memory store fallback موجود) |
| Node.js 18+ (لـ UI فقط) | الواجهة الرسومية |
| NVIDIA GPU 8GB+ (للموديلات الكبيرة) | اختياري |

---

## تشغيل سريع

### 1. ثبّت المتطلبات الأساسية

```bash
# Ollama
curl -fsSL https://ollama.com/install.sh | sh
ollama pull nomic-embed-text
ollama pull adam-prism-v13  # أو أي نموذج GGUF تاني

# Qdrant (اختياري — بدونها memory system يشتغل بـ stubs)
docker run -d --name qdrant -p 6333:6333 qdrant/qdrant:latest
```

### 2. نصب المشروع

```bash
git clone https://github.com/othmastar/adam-prism
cd adam-prism
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3. شغّل آدم

```bash
python main.py
```

يفتح API على `http://localhost:8000`

### 4. الواجهة الرسومية (اختياري)

```bash
cd frontend  # أو web-ui
npm install
npm run dev
# يفتح على http://localhost:3000
```

### 5. جرب

```bash
curl http://localhost:8000/api/status
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "مرحبا يا آدم، ازيك؟"}'
```

---

## Docker

```bash
docker compose up -d
```

---

## البنية الهيكلية

```
adam/
├── engine.py              # المحرك الرئيسي — 2018 سطر
├── infrastructure.py      # Connection pooling, caching, retry
├── memory/
│   ├── system.py          # Qdrant vector memory (6 collections)
│   └── store.py           # SQLite fallback
├── security/
│   └── guard.py           # Injection detection + 19 tool registry
├── ethics/
│   └── gate.py            # 4-law evaluation
├── api/
│   └── server.py          # FastAPI — chat, voice, search, WS, SSE
├── notebook/
│   └── system.py          # دفتر دائم
├── pipeline/
│   ├── channels.py        # Telegram bot
│   └── summarizer.py      # تلخيص هرمي
├── core/
│   ├── learning.py        # Preference learning
│   ├── permissions.py     # Permission state
│   ├── trace_recorder.py  # Conversation traces
│   └── voice.py           # VAD → ASR → TTS
├── eyes/
│   └── browser.py         # 🚧 Playwright automation (قريباً)
└── tools/
    └── computer.py        # 🚧 Computer use (قريباً)
```

```
frontend/                  # Next.js 14 UI (اختياري)
scripts/                   # أدوات مساعدة
tests/                     # اختبارات
data/                      # بيانات التدريب
```

---

## الأوضاع المعرفية (7 Cognitive Modes)

| الوضع | الوظيفة |
|-------|---------|
| **Strategic Analyst** | تحليل استراتيجي — نظرة شاملة |
| **Technical Researcher** | بحث تقني — شرح مع مثال عملي |
| **Software Dev** | تطوير برمجيات — كود مع trade-offs |
| **Pen Tester** | اختبار اختراق — CVEs وأوامر |
| **Systems Analyst** | تحليل أنظمة — بنية تحتية |
| **Knowledge Manager** | إدارة معرفة — هيكلة معلومات |
| **Teacher** | تعليم — شرح ببساطة |

---

## الاختبارات

```bash
source venv/bin/activate
pytest tests/ -v -k "not slow"    # اختبارات سريعة
pytest tests/ -v                   # كل الاختبارات (يحتاج Ollama)
```

---

## التطوير

لمن أراد المساهمة:
- `PLAN.md` — خطة التطوير وإعادة الهيكلة
- `PROGRESS.md` — سجل التقدم اليومي
- `scripts/merge_lora.py` — دمج LoRA (للتطوير فقط)

---

## الترخيص

GNU General Public License v3.0 — راجع [`LICENSE`](LICENSE)

---

## صُنع بـ ❤️

**محمد عثمان** — القاهرة، مصر
