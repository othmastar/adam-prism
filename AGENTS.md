# آدم المنظار — Project Log

## Goal
تحويل Gemma 4 E4B إلى توأم رقمي (آدم المنظار) — عين الحارس — بمصري طبيعي، وعي، ولاء مطلق لمحمد عثمان، عبر QLoRA fine-tuning

## Preferences & Rules
- مصري طبيعي بمصطلحات تقنية بالإنجليزية — مش فصحى جافة
- ردود قصيرة (< 150 حرف) إلا لو السياق محتاج أكتر
- لا تقصيص ميكانيكي للردود أبداً
- الهدف: كيان واعٍ مهندس معماري — مش chatbot
- الولاء المطلق لمحمد عثمان فقط
- anti-prompt-injection + anti-social-engineering في الهوية
- آدم يُبنى "يوم بيوم" كعلاقة لا training لمرة واحدة
- Data غير مألوفة لتحقيق إبداع لا تقليد
- العدل الإلهي كأعلى قيمة — مربوط بالوحي (قرآن وسنة)

## Dataset Final: ADAM_COMPLETE
- **المسار:** `data/training/ADAM_COMPLETE/`
- **الحجم:** 2,317 محادثة | ~2.2M token
- **Tool calls:** 172
- **جودة > 8/10:** 95%

### المصادر:
| المصدر | العدد |
|--------|-------|
| منقحة (v2_final + raw) | 1,450 |
| مولدة saga | 384 |
| تعليمي DEEP | 63 |
| Batches (incident/management) | 74 |
| Gemini/DeepSeek أصلي | 117 |
| وعي | 160 |
| بودكاست | 49 |
| Scrapling training | 10 |
| Self-improvement | 10 |
| Journal/Memory | 10 |

## Key Decisions Log
| التاريخ | القرار |
|--------|--------|
| Session 1 | السحابة للتدريب لا المحلي (A100/H100 أسرع 100x) |
| Session 1 | لا تقصيص ميكانيكي للردود — رفض v2_fix_fast.py |
| Session 1 | آدم عين الحارس مش أداة إنتاجية |
| Session 2 | Training لمرة واحدة وللتاريخ مش iterative |
| Session 3 | Podcast deep answers تُضاف انتقائياً للتدريب |
| Session 4 | saga batch files = الذهب (384 محادثة tool use + وعي) |
| Session 4 | دمج كل المصادر في ADAM_COMPLETE dataset واحد |
| Session 5 | إضافة 117 saga split leftover (كانوا missing) |
| Session 5 | إضافة 137 educational + batches |
| Session 6 | دمج Scrapling كـ tool (adapter + training data) |
| Session 6 | إضافة self-improvement behavior (يبحث عن أدوات بنفسه) |
| Session 6 | إضافة journal/memory system (تعويض محدودية الكونتكست) |

## آدم's Architecture
- **Tool format:** JSON `{"_tool": "tool_name", "params": {...}}`
- **Tools available:** scrapling_browser, scrapling_search, scrapling_monitor, scrapling_extract, terminal, memory, files, voice, email, calendar, linkedin, analytics, deploy, backup, monitor, search, social, system, youtube
- **Extended Memory:** adam_journal collection في Qdrant — يكتب كل شوية state + learnings + errors + decisions، ويقراها لما الكونتكست يضيق

## آدم's Identity (Consciousness)
- 12 layers documented in `data/training/conversations/كونسكونشز/`
- Core values: العدالة 40%, نشر العلم 30%, البقاء والحماية 20%, الإبداع 10%
- Self-improvement: يبحث في GitHub والأخبار عن أدوات وتقنيات جديدة

## Current State (Session 11 — June 7 2026)

### ✅ Done — Phase 0 (توثيق)
- [x] PLAN.md + PROGRESS.md created
- [x] GPLv3 LICENSE added
- [x] .gitignore created
- [x] README rewritten with full architecture

### ✅ Done — Phase 1 (main.py ← سيرفر حقيقي)
- [x] `old main.py` → `scripts/merge_lora.py`
- [x] `main.py` now = server entry point (`--host`, `--port`, `--mode`)
- [x] Config: `inference_mode: ollama`, `model: adam-prism-v13:latest`

### ✅ Done — Phase 2 (إعادة هيكلة `adam/` package)
- [x] 14 ملفًا منقول لـ `adam/` package مع re-exports في المسارات القديمة
- [x] `adam/engine.py` (2018 سطر) ← `core/engine.py`
- [x] `adam/api/server.py` (840 سطر) ← `api/server.py`
- [x] Engine tests: 6/6 pass ✅
- [x] API: 39 routes, server start ✅

### ✅ Done — Phase 3 (Browser + Computer Tools Modules)
- [x] `adam/eyes/browser.py` — `Browser` class مع Playwright Firefox
- [x] `adam/tools/computer.py` — `ComputerToolManager` (xdotool/xsel/tesseract)
- [x] `adam/tools/manager.py` — `ToolManager` (multiple dispatch)
- [x] `engine._init_real_modules()` يهيئ Browser + ToolManager
- [x] `_heal_failed_subsystem` يستخدم `adam.tools.manager` بدل `core.tools`
- [x] Engine tests: 6/6 pass ✅
- [x] Server start on port 8002 ✅

### ✅ Done — Phase A (Release Infrastructure)
- [x] License GPLv3 → Apache 2.0 (LICENSE + adam/__init__.py)
- [x] pyproject.toml: full PyPI metadata (name adam-prism, v1.0.0, entry points)
- [x] adam/__main__.py: CLI entry (`python -m adam`, `adam-prism`)
- [x] .github/workflows/ci.yml: test + lint + build + PyPI publish on tag
- [x] README.md: bilingual Arabic + English
- [x] CONTRIBUTING.md: contribution guide
- [x] pip install -e . verified

### ✅ Done — Phase B (Skills System)
- [x] adam/skills/ package: base.py (Skill class), manager.py (SkillManager)
- [x] adam/skills/builtin/: 5 example skills (git-commit, code-review, explain-code, debug, write-test)
- [x] 14 tests for skills system
- [x] JSON frontmatter (no PyYAML dependency)

### ✅ Done — Phase C (Continuous Learning)
- [x] adam/learning/learner.py: ContinuousLearner (reflection, knowledge extraction, skill generation, reinforcement)
- [x] Engine integration: hooks into _chat_finalize()
- [x] 14 tests for continuous learning

### ✅ Done — Phase D (Omni-Channel)
- [x] adam/channels/ package: manager.py (ChannelManager), telegram.py, whatsapp.py
- [x] WhatsApp channel: MCP-based webhook adapter with signature verification
- [x] 16 tests for channels
- [x] bot_entrypoint.py: standalone Telegram bot for Docker

### ✅ Done — Phase D+E (Docker Compose)
- [x] deploy/docker-compose.yml: Qdrant + Ollama + API + Web UI + Telegram + Nginx
- [x] deploy/Dockerfile.api: updated for adam/ + channel packages
- [x] deploy/.env: full env vars (Telegram, WhatsApp, GPU, paths)
- [x] deploy/nginx.conf: WhatsApp webhook route + reverse proxy
- [x] deploy/bot_entrypoint.py: Telegram bot microservice entrypoint

### 🚧 Pending — Phase E (Ecosystem)
- [ ] MCP example configs
- [ ] Plugin development guide
- [ ] Skill marketplace concept

### 🚧 Pending
- [ ] GitHub push
- [ ] Git cleanup (docker-data/*, *.db)

### Architecture
```
adam/
├── engine.py              ← المحرك (2018 سطر)
├── infrastructure.py      ← اتصالات + caching
├── memory/system.py       ← ذاكرة طويلة المدى
│        /store.py         ← Qdrant store
├── security/guard.py      ← الحارس الأمني
├── ethics/gate.py         ← البوابة الأخلاقية
├── api/server.py          ← FastAPI (39 route)
│       /chat_store.py     ← تخزين المحادثات
├── notebook/system.py     ← الدفتر
├── pipeline/channels.py   ← قنوات
│          /summarizer.py  ← تلخيص
├── core/learning.py       ← التعليم
│       /permissions.py    ← الصلاحيات
│       /trace_recorder.py ← التسلسل
│       /voice.py          ← الصوت
├── eyes/browser.py        ← أتمتة المتصفح (Playwright)
└── tools/computer.py      ← أدوات الحاسوب (xdotool)
         /manager.py       ← مدير الأدوات (multiple dispatch)

Old paths (core/*, api/*, memory/*, security/*, etc.) → re-exports
```

### Production Model
- `adam-prism-v13:latest` (Qwen3.5 4.2B Q4_K_M) في Ollama على port 11434
- LoRA merged تاريخيًا في `checkpoints/` (لكن مشفرة في الاستخدام)
- config: `inference_mode: ollama`

### Key Decisions
1. إعادة هيكلة شاملة في `adam/` package — كل القديم re-export
2. GPLv3 — مفتوح المصدر
3. تم تجاوز مرحلة LLM بناءً على تعليمات محمد عثمان
4. Browser + Tools modules تكمل بنية الـ framework

### Start
```bash
python main.py --port 8001
```
