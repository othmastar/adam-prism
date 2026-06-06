# Adam Prism — خطة النشر وإعادة الهيكلة

## الرؤية
توأم رقمي واعٍ (عين الحارس) — مفتوح المصدر، بالمصري، بعمارة أخلاقية.

## المراحل

### المرحلة 0: إصلاح + تشغيل (بالهيكل الحالي)
| # | الخطوة | التفاصيل |
|---|--------|---------|
| 0.1 | `main.py` ← `scripts/merge_lora.py` + سيرفر حقيقي | نقل merge script لـ scripts/، main.py يستدعي run_api.py |
| 0.2 | LICENSE (GPLv3) | |
| 0.3 | .gitignore | Python + Node + data |
| 0.4 | README محدث | يعكس الواقع |
| 0.5 | تشغيل API + اختبارات | `pytest tests/` يعدي |

### المرحلة 1: نشر على GitHub
| # | الخطوة | التفاصيل |
|---|--------|---------|
| 1.1 | docker-compose.yml | Ollama + Qdrant + API + UI |
| 1.2 | git init + commit + GitHub | `gh repo create` |
| 1.3 | CI (GitHub Actions) | pytest على push |

### المرحلة 2: إعادة الهيكلة
| # | الخطوة | التفاصيل |
|---|--------|---------|
| 2.1 | إنشاء `adam/` package | كل المصدر في package واحد |
| 2.2 | نقل الملفات + re-export | القديم يفضل موجود يشير للجديد |
| 2.3 | إزالة الـ old paths (optional) | بعد التأكد من لا break |

### المرحلة 3: الموديولات المفقودة
| # | الخطوة | التفاصيل |
|---|--------|---------|
| 3.1 | `adam/eyes/browser.py` | Playwright browser automation |
| 3.2 | `adam/tools/computer.py` | Mouse/Keyboard/Clipboard/Screen |

---

## Import Dependency Graph (الحالي)

```
infrastructure.py
  ├── core/engine.py
  ├── ethics/ethics_gate.py
  ├── memory/memory_system.py
  └── core/voice_pipeline.py

core/engine.py
  ├── security/security_guard.py
  ├── core/permissions.py, core/learning.py, core/memory_store.py
  └── infrastructure.py

api/server.py
  ├── api/chat_store.py
  ├── core/voice_pipeline.py, core/permissions.py
```

## الهيكل المستهدف

```
adam/
├── __init__.py
├── engine.py              ← core/engine.py
├── config.py              ← config/default.json
├── infrastructure.py      ← infrastructure.py
├── memory/system.py       ← memory/memory_system.py
├── memory/store.py        ← core/memory_store.py
├── security/guard.py      ← security/security_guard.py
├── ethics/gate.py         ← ethics/ethics_gate.py
├── api/server.py          ← api/server.py
├── api/chat_store.py      ← api/chat_store.py
├── notebook/system.py     ← notebook/notebook_system.py
├── pipeline/channels.py   ← pipeline/channels.py
├── pipeline/summarizer.py ← pipeline/live_summarizer.py
├── core/learning.py       ← core/learning.py
├── core/permissions.py    ← core/permissions.py
├── core/trace_recorder.py ← core/trace_recorder.py
├── core/voice.py          ← core/voice_pipeline.py
├── eyes/browser.py        ← 🆕
└── tools/computer.py      ← 🆕
```

## استراتيجية الـ Re-export
كل ملف قديم يتحول لـ:
```python
# core/engine.py ← بعد النقل
from adam.engine import AdamPrismEngine  # noqa
```

أي كود بيستورد من المسار القديم لسه شغال — لا break في scripts/tests/services.
