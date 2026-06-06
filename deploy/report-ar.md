# تقرير نشر آدم بريزم — Docker Compose Production Deployment
# Adam Prism — التوأم الرقمي الشخصي

**التاريخ**: 2026-05-08  
**النسخة**: 1.0.0  
**الكاتب**: DevOps Report

---

## فهرس المحتويات

1. [نظرة عامة على معمارية النشر](#1-نظرة-عامة-على-معمارية-النشر)
2. [Docker Compose — شرح الخدمات الأربع](#2-docker-compose--شرح-الخدمات-الأربع)
3. [Dockerfile API — شرح كامل](#3-dockerfile-api--شرح-كامل)
4. [Dockerfile Web UI — شرح كامل](#4-dockerfile-web-ui--شرح-كامل)
5. [التعامل مع GPU في Docker](#5-التعامل-مع-gpu-في-docker)
6. [متغيرات البيئة (.env)](#6-متغيرات-البيئة-env)
7. [خيارات النشر: VPS مقابل Kubernetes](#7-خيارات-النشر-vps-مقابل-kubernetes)
8. [Logging والمراقبة (Monitoring)](#8-logging-والمراقبة-monitoring)
9. [استراتيجيات Backup لقاعدة Qdrant](#9-استراتيجيات-backup-لقاعدة-qdrant)
10. [الملفات المُنشأة](#10-الملفات-المنشأة)

---

## 1. نظرة عامة على معمارية النشر

```
┌─────────────────────────────────────────────────────────┐
│                    مستخدم / متصفح                        │
└────────────────────────┬────────────────────────────────┘
                         │ :3000
                         ▼
┌─────────────────────────────────────────────────────────┐
│              Nginx (Reverse Proxy)                       │
│         /api/* → api:8000  |  /ws/* → api:8000          │
│         /*     → web:3000  |  /_next/static → static    │
└──┬──────────────────────┬───────────────────────────────┘
   │ :8000                │ :3000
   ▼                      ▼
┌──────────────┐   ┌──────────────┐
│   API        │   │   Web UI     │
│  FastAPI     │   │  Next.js     │
│  Python 3.12 │   │  Nginx       │
│  Playwright  │   └──────────────┘
└──┬───────────┘
   │                     ┌──────────────┐
   ├─────────────────────▶   Ollama     │
   │   embeddings + chat  │  Gemma 8B   │
   │                     │  Nomic Embed │
   │                     │  GPU: CUDA   │
   │                     └──────────────┘
   │
   │                     ┌──────────────┐
   ├─────────────────────▶   Qdrant     │
   │   vector search     │  5 collections│
   │                     └──────────────┘
   │
   │                     ┌──────────────┐
   └─────────────────────▶   SQLite     │
        chat_history     │  chat_store  │
                         └──────────────┘
```

**مبدأ العمل**:
- كل خدمة في container منفصل
- شبكة داخلية `adam_net` للتواصل
- API هو العقل المدبر: يربط Ollama + Qdrant + SQLite
- Nginx يعمل كـ reverse proxy أمام API و Web UI
- GPU مخصص لـ Ollama فقط (API قد يحتاجه لاحقاً للتدريب)

**لماذا هذه المعمارية؟**
- **فصل المسؤوليات**: كل خدمة مستقلة، يمكن تحديثها أو إعادة تشغيلها منفردة
- **قابلية التوسع**: يمكنك تشغيل عدة نسخ من API خلف Nginx load balancer
- **أمان**: API لا يرى الشبكة الخارجية، فقط من خلال Nginx
- **GPU Isolation**: Ollama فقط يرى GPU، حتى لا تتنافس العمليات

---

## 2. Docker Compose — شرح الخدمات الأربع

### 2.1 Ollama (`adam-ollama`)

```yaml
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  volumes:
    - ollama_data:/root/.ollama
```

**شرح**:
- يستخدم الصورة الرسمية `ollama/ollama` مباشرة
- `deploy.resources` — هذا هو السطر السحري الذي يربط GPU بالـ container
- `OLLAMA_KEEP_ALIVE=5m` — يبقي النموذج محملاً في الذاكرة 5 دقائق بعد آخر استخدام (يقلل latency)
- `OLLAMA_NUM_PARALLEL=1` — طلب واحد فقط في كل مرة (حماية من OOM على RTX 3060)
- `OLLAMA_MAX_LOADED_MODELS=1` — نموذج واحد فقط (Gemma 8B يستهلك ~6GB VRAM)

**أمر تحميل النماذج تلقائياً**:
يجب تشغيل هذا الأمر يدوياً بعد أول `docker compose up`:
```bash
docker exec adam-ollama ollama pull gemma3:8b
docker exec adam-ollama ollama pull nomic-embed-text
```
أو يمكن إضافتها كـ entrypoint script (موصى به في production).

### 2.2 Qdrant (`adam-qdrant`)

```yaml
qdrant:
  image: qdrant/qdrant:latest
  volumes:
    - qdrant_data:/qdrant/storage
    - qdrant_snapshots:/qdrant/snapshots
```

**شرح**:
- مجلدين منفصلين: `storage` للبيانات الحية، `snapshots` للنسخ الاحتياطية
- `healthcheck` يستخدم `/healthz` — نقطة نهاية مدمجة في Qdrant
- منفذ 6334 gRPC — للاتصالات عالية الأداء (قد تحتاجه للتوسع)
- Qdrant لا يحتاج GPU — يعمل على CPU فقط

### 2.3 API (`adam-api`)

**القلب النابض**:
- يبني من `Dockerfile.api`
- يعتمد على Ollama و Qdrant (يجب أن يكونا جاهزين قبل بدئه)
- يقرأ `.env` للمتغيرات
- يخزن 3 أنواع من البيانات:
  - `chat_history.db` (SQLite) ← `./data/`
  - `notebook/` ← `./data/notebook/`
  - `chromium-profile/` ← `./data/chromium-profile/`

**مشكلة Playwright في Container**:
Playwright يحتاج `--with-deps` لتثبيت مكتبات النظام (libgtk, libnss, etc.). نحن نثبتها في `Dockerfile.api`. لكن Chromium في Container يحتاج `--no-sandbox`:

أضف هذا في `eyes/browser_automation.py` أو `tools/computer_use.py`:
```python
browser = await playwright.chromium.launch(
    headless=True,
    args=["--no-sandbox", "--disable-gpu", "--disable-setuid-sandbox"]
)
```

### 2.4 Web UI (`adam-web`)

- يستخدم **multi-stage build**: Node يبني → Nginx يخدم
- Nginx يعمل كـ reverse proxy: يستقبل الطلبات ويوزعها
- `output: "standalone"` في `next.config.ts` ينتج build مستقل لا يحتاج Node runtime
- `/api/*` يمرر إلى API container
- `/ws/*` يمرر مع WebSocket Upgrade headers

---

## 3. Dockerfile API — شرح كامل

```dockerfile
FROM python:3.12-slim AS base
```

**لماذا slim؟**
- الحجم النهائي: ~1.2GB (مع Playwright) مقابل ~2.5GB للـ full image
- يحتوي على كل ما نحتاجه: Python 3.12 + pip + SSL certificates

**الخطوات بالتفصيل**:

| الخطوة | الوصف | السبب |
|--------|-------|-------|
| `apt-get install curl ca-certificates` | أدوات النظام | لـ healthcheck و HTTPS |
| `pip install -r requirements.txt` | httpx, fastapi, uvicorn, qdrant-client, إلخ | كل التبعيات الأساسية |
| `pip install psutil` | مراقبة النظام | healthcheck يستخدمها لو كانت متاحة |
| `pip install playwright` | المتصفح الآلي | لقراءة محادثات DeepSeek/Gemini |
| `playwright install chromium` | تحميل Chromium | الحجم ~350MB إضافية |
| `COPY api/ core/ brain/ ...` | كود التطبيق | كل موديولات آدم |

**مشكلة الحجم:**
حجم الصورة النهائي ~1.5-2GB بسبب Playwright + Chromium. لتقليصه:
1. استخدم `playwright install --only-chromium` بدلاً من تثبيت كل المتصفحات
2. افصل الـ browser automation في خدمة منفصلة (موصى به لـ production)

**User non-root:**
```dockerfile
RUN addgroup --system --gid 1001 app && \
    adduser --system --uid 1001 --ingroup app app && \
    chown -R app:app /app
USER app
```
أمان: الـ container لا يعمل كـ root. لو اخترق أحد الـ API، لا يستطيع تعديل ملفات النظام.

**لماذا COPY وليس mount للكود؟**
في production، الكود ثابت ولا يتغير. Build ناسخ للصورة = portable. الـ volume للملفات المتغيرة فقط (data, logs).

---

## 4. Dockerfile Web UI — شرح كامل

### Multi-stage Build

**المرحلة 1 — Builder (`node:20-alpine`)**:
```dockerfile
FROM node:20-alpine AS builder
COPY web-ui/package.json ./
RUN npm ci --legacy-peer-deps
COPY web-ui/ .
RUN npm run build
```

- `npm ci` — تثبيت سريع وحسب lock file (أسرع من `npm install`)
- `--legacy-peer-deps` — لأن `react 19` و `next 16` قد يكون بينهما تعارضات

**المرحلة 2 — Runner (`nginx:stable-alpine`)**:
```dockerfile
FROM nginx:stable-alpine AS runner
COPY --from=builder /app/.next/standalone /app
COPY --from=builder /app/.next/static /app/.next/static
```

- `next.config.ts` يحتوي `output: "standalone"` — هذا ينتج مجلد `.next/standalone/` يحتوي:
  - `server.js` — خادم Next.js مستقل
  - `package.json` — تبعيات التشغيل فقط
  - `node_modules/` — dependencies الضرورية فقط (بدون devDependencies)
- لكننا هنا نستخدم Nginx مباشرة بدلاً من `server.js` — الـ standalone build يُستخدم للملفات الـ static فقط (`/app/.next/static`), بينما Nginx يعمل كـ reverse proxy.

**ملاحظة مهمة**:
الـ Dockerfile.web أعلاه يستخدم Nginx. لو أردت تشغيل Next.js مباشرة (بدون Nginx)، استخدم هذا البديل:

```dockerfile
FROM node:20-alpine AS runner
WORKDIR /app
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/public ./public
EXPOSE 3000
CMD ["node", "server.js"]
```

---

## 5. التعامل مع GPU في Docker

### المتطلبات الأساسية

NVIDIA Container Toolkit — يجب تثبيته على **المضيف** (host)، ليس داخل Docker:

```bash
# Ubuntu / Debian
curl -fsSL https://nvidia.github.io/libnvidia-container/gpgkey | \
    sudo gpg --dearmor -o /usr/share/keyrings/nvidia-container-toolkit-keyring.gpg
curl -s -L https://nvidia.github.io/libnvidia-container/stable/deb/nvidia-container-toolkit.list | \
    sed 's#deb https://#deb [signed-by=/usr/share/keyrings/nvidia-container-toolkit-keyring.gpg] https://#g' | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list
sudo apt-get update && sudo apt-get install -y nvidia-container-toolkit
sudo nvidia-ctk runtime configure --runtime=docker
sudo systemctl restart docker
```

### آلية الربط

```yaml
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

هذا هو **Compose v3.9+** syntax. ماذا يفعل بالضبط:
1. يخبر Docker: "هذا الـ container يحتاج GPU"
2. Docker يبحث عن NVIDIA runtime
3. `nvidia-container-runtime` يركب:
   - `/usr/local/nvidia/lib64/libcuda.so` — مكتبة CUDA
   - `nvidia-smi` — أداة المراقبة
   - متغير `NVIDIA_VISIBLE_DEVICES=all`

### التحقق من GPU داخل الـ container

```bash
# بعد تشغيل ollama container:
docker exec adam-ollama nvidia-smi
docker exec adam-ollama ollama list
```

### VRAM Budget لـ RTX 3060 12GB

| النموذج | VRAM | ملاحظة |
|---------|------|--------|
| Gemma 3 8B (Q4_K_M) | ~5.5 GB | ✅ يعمل مريح |
| nomic-embed-text | ~0.3 GB | ✅ يعمل معه |
| Gemma 3 12B (Q4_K_M) | ~8 GB | ✅ ممكن لكن ضيق |
| Gemma 3 27B (Q4_K_M) | ~16 GB | ❌ لا يعمل |
| **المجموع** | ~5.8 GB | ✅ آمن مع ترك 6GB للنظام |

**توصية**: استخدم `gemma3:8b` (مع `OLLAMA_NUM_PARALLEL=1` و `OLLAMA_MAX_LOADED_MODELS=1`).

### لو GPU غير متاح (CPU fallback)

في حال عدم وجود GPU، يمكن تشغيل Ollama على CPU فقط:
```yaml
ollama:
  environment:
    - OLLAMA_HOST=0.0.0.0
  # أزل deploy.resources section
```
لكن الأداء سيكون بطيئاً جداً (Gemma 8B على CPU: ~1-2 tokens/sec).

---

## 6. متغيرات البيئة (.env)

### الشرح الكامل لكل متغير

| المتغير | الافتراضي | الشرح |
|---------|-----------|-------|
| `OLLAMA_BASE` | `http://ollama:11434` | عنوان Ollama داخل الشبكة (اسم الخدمة في compose) |
| `OLLAMA_MODEL` | `gemma3:8b` | نموذج التوليد الرئيسي (~6GB VRAM) |
| `OLLAMA_EMBEDDING` | `nomic-embed-text` | نموذج التضمين للمتجهات (~274MB) |
| `OLLAMA_NUM_CTX` | `8192` | حجم سياق النموذج (tokens) — RTX 3060 يتحمل 8K مريح |
| `QDRANT_URL` | `http://qdrant:6333` | عنوان Qdrant (اسم الخدمة: `qdrant`, port: `6333`) |
| `QDRANT_API_KEY` | (فارغ) | مفتاح API (اتركه فارغاً ما لم تضع authentication) |
| `API_HOST` | `0.0.0.0` | يسمح بالاتصال من أي interface (ضروري داخل Docker) |
| `API_PORT` | `8000` | منفذ الـ API داخل الـ container |
| `API_WORKERS` | `1` | عدد عاملين Uvicorn — 1 كافٍ (GPU واحد) |
| `NEXT_PUBLIC_API_URL` | `http://localhost:8000` | عنوان API للـ frontend (من خارج Docker) |
| `SECRET_KEY` | (مطلوب تغييره) | مفتاح سري للتشفير — غيّره فوراً في الإنتاج |
| `CUDA_VISIBLE_DEVICES` | `0` | أي GPU يستخدم (0 = أول كرت, مفيد لو 2 كرت) |
| `OLLAMA_GPU_LAYERS` | `-1` | -1 = كل الطبقات على GPU |
| `TELEGRAM_BOT_TOKEN` | (فارغ) | توكن بوت Telegram (اختياري) |
| `MAX_TOOL_CALLS` | `5` | أقصى عدد استدعاءات أدوات لكل دورة |
| `TOOL_TIMEOUT` | `30` | مهلة أداة بالثواني |

### العلاقة بين المتغيرات في compose

```
.env: OLLAMA_BASE=http://ollama:11434
                 │
                 ▼
config/default.json: ollama_base ← يقرأ من البيئة
                 │
                 ▼
engine = AdamPrismEngine(config)
  engine.ollama_base = "http://ollama:11434"
  engine.qdrant_url = "http://qdrant:6333"
```

لاحظ أن API container يصل إلى Ollama و Qdrant عبر **اسم الخدمة** (`ollama`, `qdrant`) وليس `localhost`، لأن كل container له network namespace منفصل.

---

## 7. خيارات النشر: VPS مقابل Kubernetes

### الخيار A: VPS واحد (مستوى واحد) — المُوصى به

**لماذا؟** لأن المشروع يعتمد على GPU واحد، ولا جدوى من Kubernetes بعقدة واحدة.

**التوصية:**
- **الاستضافة**: Hetzner CX22 (4 vCPU, 8GB RAM) → لا يكفي. الحد الأدنى: CX32 (8 vCPU, 16GB RAM) + GPU منخفض مثل GEX44
- أو: **VPS محلي** على جهازك الخاص مع RTX 3060

```bash
# نشر على VPS (Ubuntu 22.04)
ssh user@vps-ip
sudo apt update && sudo apt install -y docker.io docker-compose-v2 nvidia-container-toolkit
git clone https://github.com/yourname/adam-prism.git
cd adam-prism/deploy
cp .env .env.production
# عدّل .env.production (SECRET_KEY, إلخ)
docker compose --env-file .env.production up -d
```

**مزايا VPS واحد:**
- إدارة بسيطة (scp, ssh, docker compose)
- تكلفة أقل
- أداء أعلى (لا overhead من Kubernetes)

**عيوب VPS واحد:**
- Point of failure واحد
- تحتاج backup يدوي
- التوسع محدود

### الخيار B: Kubernetes (متقدم)

**متى نستخدمه؟** عندما يكون لديك:
- عدة GPUs
- عدة مستخدمين
- حاجة لـ auto-scaling
- فريق DevOps

**مكونات Kubernetes الإضافية:**

| المكون | الوظيفة |
|--------|---------|
| `nvidia-device-plugin` | يوزع GPU على Pods |
| `Ingress NGINX` | Route خارجي |
| `Cert-Manager` | SSL/TLS تلقائي |
| `Prometheus Stack` | مراقبة |
| `Velero` | Backup |

**مثال Pod GPU في Kubernetes:**
```yaml
apiVersion: v1
kind: Pod
metadata:
  name: ollama
spec:
  containers:
  - name: ollama
    image: ollama/ollama:latest
    resources:
      limits:
        nvidia.com/gpu: 1
```

**متى لا نستخدم Kubernetes؟**
- فريق صغير (شخص واحد)
- GPU واحد
- تكاليف تشغيل بسيطة

**جدول مقارنة:**

| المعيار | VPS واحد | Kubernetes |
|---------|----------|------------|
| التعقيد | بسيط | عالي |
| التكلفة | منخفضة | مرتفعة (Control Plane) |
| التوسع | محدود | غير محدود عملياً |
| الـ HA | ❌ | ✅ |
| الـ Self-healing | ❌ | ✅ |
| Rolling update | يدوي | تلقائي |
| الإدارة اليومية | docker compose | kubectl + Helm |

**القرار النهائي**: ابدأ بـ VPS واحد + Docker Compose. حوّل إلى Kubernetes فقط لو احتجت.

---

## 8. Logging والمراقبة (Monitoring)

### 8.1 استراتيجية Logging الحالية

النظام الحالي يكتب 3 أنواع من السجلات:

| الملف | المحتوى | التنسيق |
|-------|---------|---------|
| `adam_prism.log` | سجل نصي بشري | `2026-05-08 14:30:01 [adam_prism] INFO: ✅ المحرك الرئيسي جاهز` |
| `adam_prism.json` | سجل JSON آلي (JSONL) | `{"timestamp":"...", "level":"INFO", "logger":"adam_prism", "message":"..."}` |
| `access log (uvicorn)` | طلبات API | قياسي من Uvicorn |

### 8.2 Docker Logging

جميع containers تطبع logs إلى stdout/stderr → Docker تلتقطها.

```bash
# عرض سجلات API
docker logs adam-api -f --tail 100

# عرض سجلات محددة
docker logs adam-ollama -f
docker logs adam-qdrant -f
```

### 8.3 Logging محسن للإنتاج

في `.env`:
```yaml
# log level
API_LOG_LEVEL=info  # debug في التطوير, warning في الإنتاج

# Docker log rotation (في docker-compose.yml → لكل service)
logging:
  driver: "json-file"
  options:
    max-size: "10m"
    max-file: "3"
```

### 8.4 Loki + Promtail (مراقبة مركزية)

إذا كان لديك عدة خوادم، استخدم **Grafana Loki**:

```
┌─────────┐    ┌──────────┐    ┌────────┐
│ Container│───▶│ Promtail │───▶│  Loki  │
│  logs    │    │ (agent)  │    │ (store)│
└─────────┘    └──────────┘    └────┬───┘
                                    │
                                    ▼
                               ┌────────┐
                               │ Grafana│
                               │  UI    │
                               └────────┘
```

مثال `promtail-config.yml`:
```yaml
scrape_configs:
  - job_name: adam-prism
    static_configs:
      - targets: [localhost]
        labels:
          job: adam-api
          __path__: /var/lib/docker/containers/*/*.log
```

### 8.5 مقاييس (Metrics) مخصصة

API يوفر نقاط مقاييس في `/api/engine/health`:

```json
{
  "api": "running",
  "uptime_seconds": 3600,
  "engine": {
    "model": "gemma3:8b",
    "active_mode": "analyst",
    "cycle_count": 150,
    "tool_actions_ok": 45,
    "tool_actions_fail": 3
  },
  "ollama": {
    "connected": true,
    "models": ["gemma3:8b", "nomic-embed-text"]
  },
  "qdrant": {
    "connected": true
  }
}
```

**Prometheus scrape config:**
```yaml
scrape_configs:
  - job_name: adam-api
    metrics_path: /api/engine/health
    static_configs:
      - targets: ['api:8000']
```

### 8.6 تنبيهات (Alerts)

سيناريوهات التنبيه:

```yaml
# prometheus-alerts.yml
groups:
  - name: adam-prism
    rules:
      - alert: APIDown
        expr: probe_success{job="adam-api"} == 0
        for: 5m

      - alert: OllamaDisconnected
        expr: ollama_connected == 0
        for: 2m

      - alert: QdrantDisconnected
        expr: qdrant_connected == 0
        for: 2m

      - alert: HighLatency
        expr: cycle_duration_ms > 30000  # 30 seconds
        for: 5m

      - alert: DiskSpaceLow
        expr: (node_filesystem_avail_bytes / node_filesystem_size_bytes) < 0.1
```

أرسل التنبيهات عبر:
- **Telegram**: استخدم البوت
- **Slack/Email**: عبر Alertmanager
- **PagerDuty**: للإنتاج الحساس

---

## 9. استراتيجيات Backup لقاعدة Qdrant

### 9.1 لماذا Qdrant يحتاج Backup؟

Qdrant يخزن معرفة آدم الكاملة:
- الذكريات والمحادثات ← `conversations` collection
- المعرفة المستخلصة ← `knowledge` collection
- أنماط التفكير ← `patterns` collection
- الملخصات ← `summaries` collection
- الروابط بين المفاهيم ← `connections` collection

فقدان Qdrant = فقدان شخصية آدم.

### 9.2 طريقة 1: Snapshot عبر API (موصى بها)

Qdrant يوفر API أخذ snapshots مباشرة:

```bash
#!/bin/bash
# scripts/backup_qdrant.sh
BACKUP_DIR="/mnt/backup/adam-prism/qdrant"
DATE=$(date +%Y-%m-%d_%H-%M-%S)
mkdir -p "$BACKUP_DIR/$DATE"

# أخذ snapshot لكل collection
for collection in knowledge conversations patterns summaries connections; do
  curl -X POST "http://localhost:6333/collections/$collection/snapshots"
done

# نسخ الـ snapshots
docker cp adam-qdrant:/qdrant/snapshots "$BACKUP_DIR/$DATE/"

# ضغط
tar -czf "$BACKUP_DIR/qdrant-$DATE.tar.gz" -C "$BACKUP_DIR/$DATE" .
rm -rf "$BACKUP_DIR/$DATE"

echo "✅ Backup saved: $BACKUP_DIR/qdrant-$DATE.tar.gz"
```

### 9.3 طريقة 2: Docker Volume Backup

```bash
# إيقاف Qdrant
docker stop adam-qdrant

# نسخ الـ volume
docker run --rm -v adam_qdrant_data:/source -v /mnt/backup:/backup \
    alpine tar czf /backup/qdrant-$(date +%Y%m%d).tar.gz -C /source .

# إعادة التشغيل
docker start adam-qdrant
```

### 9.4 طريقة 3: Backup تلقائي مع Cron

```bash
# /etc/cron.d/adam-prism-backup
0 3 * * * root /opt/adam-prism/scripts/backup_qdrant.sh
# كل يوم 3:00 صباحاً
```

### 9.5 Backup لبقية المكونات

| المكون | المحتوى | طريقة النسخ |
|--------|---------|-------------|
| Qdrant snapshots | الذاكرة الكاملة | API + cron |
| SQLite (`chat_history.db`) | تاريخ المحادثات | `cp` (DB صغير) |
| `notebook/` | ملاحظات وملخصات | rsync |
| `chromium-profile/` | ملفات تعريف المتصفح | tar (اختياري) |
| `config/default.json` | الإعدادات | git |

### 9.6 استرجاع (Restore)

```bash
# إيقاف API (بس)
docker stop adam-api

# حذف الحالي
docker exec adam-qdrant rm -rf /qdrant/storage/collections

# نسخ الـ snapshot (الطريقة الآمنة)
RESTORE_FILE="/mnt/backup/qdrant-2026-05-07.tar.gz"
docker cp "$RESTORE_FILE" adam-qdrant:/tmp/
docker exec adam-qdrant tar xzf /tmp/$(basename "$RESTORE_FILE") -C /
docker exec adam-qdrant rm /tmp/$(basename "$RESTORE_FILE")

# إعادة التشغيل
docker start adam-api
```

### 9.7 3-2-1 Backup Strategy

```
3 نسخ:
  - 1: على نفس الخادم (snapshot محلي)
  - 1: على خادم آخر (rsync إلى VPS آخر)
  - 1: offsite (S3, Backblaze B2, أو Google Drive)

دوريتان:
  - يومي: increment (كل 6 ساعات)
  - أسبوعي: full (يحتفظ به 30 يوماً)
```

للنسخ إلى S3:
```bash
# استخدم s3cmd أو aws cli
s3cmd sync /mnt/backup/adam-prism/ s3://adam-prism-backup/
```

---

## 10. الملفات المنشأة

### هيكل مجلد `deploy/`:

```
deploy/
├── .env                     # متغيرات البيئة (template)
├── docker-compose.yml       # ملف Docker Compose الرئيسي
├── Dockerfile.api           # Dockerfile لـ API (Python/FastAPI)
├── Dockerfile.web           # Dockerfile لـ Web UI (Next.js + Nginx)
├── nginx.conf              # إعدادات Nginx reverse proxy
└── report-ar.md            # هذا التقرير
```

### كيفية الاستخدام:

```bash
# 1. ادخل مجلد deploy
cd deploy

# 2. انسخ .env وعدّله
cp .env .env.production
nano .env.production   # ← غيّر SECRET_KEY, أضف TELEGRAM_BOT_TOKEN لو تحب

# 3. تأكد من تثبيت NVIDIA Container Toolkit
nvidia-smi              # تأكد أن GPU شغال
sudo nvidia-ctk runtime configure --runtime=docker

# 4. شغّل
docker compose --env-file .env.production up -d

# 5. حمّل النماذج في Ollama
docker exec adam-ollama ollama pull gemma3:8b
docker exec adam-ollama ollama pull nomic-embed-text

# 6. افتح المتصفح
echo "http://localhost:3000"

# 7. تابع السجلات
docker compose logs -f
```

### استكشاف الأخطاء:

| المشكلة | التحقق | الحل |
|---------|--------|------|
| GPU لا يُرى داخل الـ container | `docker exec adam-ollama nvidia-smi` | ثبّت NVIDIA Container Toolkit وأعد تشغيل Docker |
| Ollama لا يستجيب | `curl http://localhost:11434/api/tags` | تحقق من `ollama_data` volume ومساحة التخزين |
| API يرفض الاتصال | `docker logs adam-api` | تحقق من `OLLAMA_BASE` و `QDRANT_URL` في .env |
| Qdrant snapshot يفشل | `curl -X POST http://localhost:6333/collections` | تحقق من `/qdrant/snapshots` permissions |
| Web UI لا يفتح | `curl http://localhost:3000/` | تحقق من build logs في الـ builder stage |
| Chromium لا يعمل | `docker logs adam-api` \| grep -i playwright | أضف `--no-sandbox` إلى launch args |

---

**آدم بريزم — التوأم الرقمي الشخصي.**  
نشرته بـ Docker Compose + GPU واحد.  
كل ملف جاهز للتنفيذ الفوري.
