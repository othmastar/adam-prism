# نصائح تفصيلية للموديل المحلي (OpenCode / GLM-5.2 المحلي)

## ⚠️ مهم جداً — اقرأ هذا قبل أي تعديل

أنت موديل محلي بـ context محدود. عشان متضيعش، اتبع القواعد دي **بالظبط**.

---

## 1. القاعدة الذهبية: ملف واحد في المرة

**ما تعملش:** تعدل 5 ملفات في نفس الوقت
**اعمل:** ملف واحد → اختبره → بعدين اللي بعده

```bash
# ❌ غلط
edit engine.py + edit server.py + edit chat-interface.tsx + edit api.ts

# ✅ صح
edit engine.py → test → commit
edit server.py → test → commit
edit chat-interface.tsx → test → commit
```

---

## 2. قبل أي تعديل — خد snapshot

```bash
# قبل ما تبدأ
cd /path/to/adam-prism
git add -A
git commit -m "snapshot before changes"

# أو لو مش git
cp -r backend backend.backup
cp -r frontend/web-ui frontend/web-ui.backup
```

**لو حصل خطأ بعد التعديل، تقدر ترجع بـ:**
```bash
git checkout -- .
# أو
rm -rf backend && mv backend.backup backend
```

---

## 3. الإصلاحات اللي اتعملت (ملخص)

### 3.1 engine.py (المشكلة الأكبر — اتحلت)

**قبل:** كل الـ requests بتقع على Mock
**بعد:** fallback chain ذكي

```
Pipeline جديد:
1. اكتشف الموديلات المتاحة (cache 60s)
2. fallback chain: primary → fallback → auxiliary → mock
3. كل model ليه timeout منفصل
4. retry مع exponential backoff
5. stats دقيقة (لكل stage success/fail منفصل)
```

**التغييرات:**
- `EngineConfig`:
  - `ollama_timeout: 90s` (كان 60s — gemma4 محتاج وقت أكتر)
  - `ollama_fallback_model: "qwen2.5:0.5b"` (جديد)
  - `max_context_tokens: 4096` (كان 8192 — صغرناه للسرعة)
  - `ollama_retry_count: 2` (جديد)
  - `ollama_retry_delay: 1.0` (جديد)
- `_call_ollama()`:
  - بيقبل `model` و `timeout` parameters
  - retry logic مع exponential backoff
  - يتعامل مع `thinking` field (gemma4 behavior)
  - يتعامل مع `<think>` tags
  - truncation لو الرسائل كبيرة
- `_detect_available_models()` — جديد، cache 60s
- `chat()` — fallback chain كامل
- `health_check()` — مربوط فعلياً بالـ engine
- `heal()` — جديد، إصلاح ذاتي
- `get_stats()` — stats دقيقة

### 3.2 server_minimal.py

- `/api/status` — `engine_ready` مربوط فعلياً
- `/api/engine/health` — يستخدم `_engine.health_check()`
- `/api/engine/diagnostics` — يستخدم `_engine.health_check()`
- `/api/engine/heal` — يستخدم `_engine.heal()`
- `/api/chat/upload` — يدعم `session_id` (يربط الملف بالجلسة)
- `/api/voice/transcribe` — STT (whisper)
- `/api/voice/synthesize` — TTS (pyttsx3)
- `/api/voice/chat` — STT → chat → TTS pipeline

### 3.3 chat-interface.tsx

- `sendChatMessage()` بيبعت `attachments` في context (كان بيبعت `history` بس)

---

## 4. خطة التطبيق (خطوة بخطوة)

### خطوة 1: backup
```bash
cd /mnt/Workspace/Adam_Prism_Complete_v2
git add -A && git commit -m "before fixes"
```

### خطوة 2: انسخ engine.py المُصلح
```bash
cp /path/to/adam-final-fixed/backend/adam/engine.py backend/adam/engine.py
```

### خطوة 3: اختبر engine.py لوحده
```bash
cd backend
python3 -c "
import asyncio, sys
sys.path.insert(0, '.')
from adam.engine import AdamEngine, EngineConfig
import os
os.environ['ADAM_SESSION_DB'] = '/tmp/test.db'
os.environ['ADAM_MEMORY_DB'] = '/tmp/test_mem.db'

async def test():
    engine = AdamEngine(EngineConfig.from_env())
    # تحقق من Ollama
    models = await engine._detect_available_models()
    print(f'Available models: {models}')
    # تحقق من chat
    result = await engine.chat('مرحبا')
    print(f'Backend: {result[\"backend\"]}')
    print(f'Response: {result[\"response\"][:100]}')
    await engine.cleanup()

asyncio.run(test())
"
```

**لو شاف:**
- `Backend: primary` → ✅ gemma4 شغال
- `Backend: fallback` → ✅ qwen2.5 شغال (gemma4 فشل بس fallback اشتغل)
- `Backend: mock` → ❌ المشكلة لسه موجودة — راجع logs

### خطوة 4: انسخ server_minimal.py المُصلح
```bash
cp /path/to/adam-final-fixed/backend/adam/api/server_minimal.py backend/adam/api/server_minimal.py
```

### خطوة 5: اختبر server
```bash
cd backend
uvicorn adam.api.server_minimal:app --port 8000 &
sleep 3

# تحقق من status
curl http://localhost:8000/api/status | python3 -m json.tool

# تحقق من health
curl http://localhost:8000/api/engine/health | python3 -m json.tool

# تحقق من heal
curl -X POST http://localhost:8000/api/engine/heal | python3 -m json.tool

# تحقق من chat
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "مرحبا"}' | python3 -m json.tool
```

### خطوة 6: انسخ chat-interface.tsx المُصلح
```bash
cp /path/to/adam-final-fixed/frontend/components/adam/chat-interface.tsx \
   frontend/web-ui/src/components/adam/chat-interface.tsx
```

### خطوة 7: اختبر الـ frontend
```bash
cd frontend/web-ui
npm run dev
# افتح http://localhost:3000
# ارفع ملف txt صغير
# اكتب "حلل الملف ده"
# تحقق إن الموديل بيشوف محتوى الملف
```

---

## 5. اختبار شامل (بعد كل التعديلات)

```bash
# 1. شغل الـ backend
cd backend
uvicorn adam.api.server_minimal:app --port 8000 &

# 2. شغل الـ frontend
cd ../frontend/web-ui
npm run dev &

# 3. اختبر pipeline كامل
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "مرحبا يا آدم"}'

# النتيجة المتوقعة:
# - backend: "primary" أو "fallback" (مش "mock")
# - response: نص حقيقي من الموديل
# - session_id: UUID

# 4. اختبر upload
echo "test content" > /tmp/test.txt
curl -X POST http://localhost:8000/api/chat/upload \
  -F "file=@/tmp/test.txt"

# 5. اختبر heal
curl -X POST http://localhost:8000/api/engine/heal

# 6. اختبر status
curl http://localhost:8000/api/status
# لازم engine_ready: true
```

---

## 6. مشاكل محتملة وحلولها

### مشكلة: "Event loop is closed"
**السبب:** استخدام `asyncio.run()` أكتر من مرة في نفس الـ process
**الحل:** استخدم `asyncio.get_event_loop().run_until_complete()` أو `nest_asyncio`

```python
import nest_asyncio
nest_asyncio.apply()
```

### مشكلة: "Connection refused" لـ Ollama
**السبب:** Ollama مش شغال
**الحل:**
```bash
ollama serve &
sleep 3
curl http://localhost:11434/api/tags
```

### مشكلة: gemma4:12b بيرجع response فاضي
**السبب:** gemma4 بيكتب الرد في `thinking` field مش `content`
**الحل:** الـ engine الجديد بيتعامل مع ده تلقائياً (line 954-958 في engine.py)

### مشكلة: timeout مع gemma4
**السبب:** gemma4 12b بطيء على الـ hardware المتاح
**الحل:**
- زود `ADAM_OLLAMA_TIMEOUT` لـ 180s
- أو استخدم `qwen2.5:0.5b` كـ primary (أسرع)
- الـ engine الجديد بيعمل fallback تلقائياً

### مشكلة: الـ frontend مش بيشوف الملفات
**السبب:** الـ `sendChatMessage` مش بيبعت `attachments` في context
**الحل:** الـ chat-interface.tsx المُصلح بيبعتها (line 769-777)

### مشكلة: engine_ready دايماً false
**السبب:** الـ engine مش مهيّأ صح
**الحل:** الـ engine الجديد بيتحقق فعلياً من `ollama + memory + model`

---

## 7. إعدادات .env الموصى بها

```bash
# .env

# Primary model — gemma4 لو شغال، qwen2.5 لو لأ
ADAM_OLLAMA_MODEL=gemma4:12b
ADAM_OLLAMA_FALLBACK_MODEL=qwen2.5:0.5b

# Timeouts
ADAM_OLLAMA_TIMEOUT=90
ADAM_OLLAMA_RETRY_COUNT=2
ADAM_OLLAMA_RETRY_DELAY=1.0

# Auxiliary (مهم للتلخيص + title)
ADAM_AUXILIARY_ENABLED=true
ADAM_AUXILIARY_MODEL=qwen2.5:0.5b

# Context (صغير للسرعة)
ADAM_MAX_CONTEXT_TOKENS=4096
ADAM_RESERVE_FOR_RESPONSE=1024
ADAM_COMPRESSION_THRESHOLD=0.70
ADAM_PROTECT_LAST_N=6

# Pipeline
ADAM_PRIMARY_MODEL=
ADAM_FALLBACK_TO_AUXILIARY=true

# Embeddings
ADAM_EMBEDDING_MODEL=nomic-embed-text
```

---

## 8. ترتيب الأولويات (لو وقتك محدود)

1. **انسخ engine.py المُصلح** (يحل 80% من المشاكل)
2. **انسخ server_minimal.py المُصلح** (يحل engine_ready + heal)
3. **انسخ chat-interface.tsx المُصلح** (يحل مشكلة الملفات)
4. **اختبر** بالـ commands في القسم 5

**لو عندك وقت أكتر:**
5. ثبّت `whisper` للـ STT: `pip install openai-whisper`
6. ثبّت `pyttsx3` للـ TTS: `pip install pyttsx3`
7. ثبّت `PyMuPDF` للـ PDF: `pip install PyMuPDF`

---

## 9. كيف تـ debug أي مشكلة

```bash
# 1. شغل الـ backend بـ verbose logging
cd backend
uvicorn adam.api.server_minimal:app --port 8000 --log-level debug 2>&1 | tee /tmp/adam.log

# 2. ابعت طلب وشوف الـ logs
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}'

# 3. شوف الـ logs
tail -f /tmp/adam.log | grep -E "Pipeline|_call_ollama|backend|error"
```

**الـ logs المفروض تشوفها:**
```
INFO:adam_prism.engine:📋 Available Ollama models: {'gemma4:12b', 'qwen2.5:0.5b', ...}
INFO:adam_prism.engine:🔁 Pipeline: ltm=False history=0 messages=2 tokens=50 chain=['gemma4:12b', 'qwen2.5:0.5b']
INFO:adam_prism.engine:  → trying primary: gemma4:12b (timeout=90.0s)
INFO:adam_prism.engine:⚡ _call_ollama → model=gemma4:12b, msgs=2, chars=200, timeout=90.0s
INFO:adam_prism.engine:  ← 200, content=0, thinking=150, done=stop, total_duration=5000ms
INFO:adam_prism.engine:  ← استخدمنا thinking field (gemma4 behavior)
INFO:adam_prism.engine:  ← result_len=150
INFO:adam_prism.engine:  ✅ primary succeeded: model=gemma4:12b resp_len=150
```

**لو شفت:**
- `⬇️ primary returned None` → gemma4 فشل، هيجرب fallback
- `❌ primary failed: timeout` → زود الـ timeout
- `⚠️ All models failed → mock fallback` → كل الموديلات فشلت

---

## 10. ما تعملش (تحذيرات)

1. **ما تـ rewriteش engine.py من الصفر** — التعديلات دقيقة ومختبرة
2. **ما تغيرش الـ fallback chain** — الترتيب مهم (primary → fallback → auxiliary → mock)
3. **ما تـ disableش الـ retry** — retry مهم لـ gemma4 (أحياناً بيفشل ثم ينجح)
4. **ما تكبرش max_context_tokens** — 4096 مثالي للسرعة
5. **ما تـ skipش `_detect_available_models`** — لازم عشان fallback يشتغل

---

## 11. لو فيه مشكلة بعد كل ده

```bash
# 1. اجمع الـ logs
uvicorn adam.api.server_minimal:app --port 8000 --log-level debug 2>&1 | tee /tmp/adam_full.log

# 2. ابعت طلب بسيط
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "test"}' > /tmp/adam_response.json

# 3. اجمع info النظام
curl http://localhost:8000/api/engine/diagnostics > /tmp/adam_diag.json
curl http://localhost:8000/api/status > /tmp/adam_status.json
ollama list > /tmp/adam_models.txt

# 4. ابعت كل ده للموديل السحابي
```

---

**ملاحظة أخيرة:** الـ engine.py المُصلح بياخد **1200+ سطر** كود مختبر. ما تحاولش تفهمه كله مرة واحدة. عدّل حاجة صغيرة، اختبر، كرر.
