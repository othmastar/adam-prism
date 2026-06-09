# Architecture

## النظام بالكامل

```
                      ┌──────────────────────┐
                      │  Input Channels (25) │
                      │  Web/Telegram/WA/etc │
                      └──────────┬───────────┘
                                 │
                      ┌──────────▼───────────┐
                      │   Security Guard     │
                      │  4-layer detection   │
                      └──────────┬───────────┘
                                 │
                      ┌──────────▼───────────┐
                      │   Ethics Gate        │
                      │  4 laws + reverence  │
                      └──────────┬───────────┘
                                 │
               ┌─────────────────┼─────────────────┐
               │                 │                 │
      ┌────────▼────────┐  ┌────▼────────┐  ┌─────▼─────────┐
      │  Memory         │  │ Engine Core │  │  Tools        │
      │  Qdrant+SQLite  │  │ 12 Layers   │  │  53 built-in  │
      │  6 collections  │  │ 7 Modes     │  │  +70 MCP      │
      │  Journal system │  │ Sub-agents  │  │  Sandbox      │
      │                 │  │ Continuous  │  │  Sub-agents   │
      │                 │  │ Learning    │  │               │
      └─────────────────┘  └──────┬──────┘  └──────────────┘
                                  │
                      ┌───────────▼──────────┐
                      │  API + Deployment    │
                      │  FastAPI · Docker    │
                      │  Modal · CLI · Nginx │
                      └──────────────────────┘
```

## 🧠 Consciousness System — 12 Layers

كل طبقة بتفحص، تثري، وتتحقق قبل التمرير:

1. **Intent Classification** — تصنيف القصد (technical, teacher, dev, etc.)
2. **Context Building** — بناء السياق من الذاكرة القصيرة والطويلة
3. **Knowledge Retrieval** — بحث دلالي في Qdrant (6 collections)
4. **Ethical Evaluation** — تقييم حسب 4 قوانين أخلاقية
5. **Security Check** — كشف injection و social engineering
6. **Reasoning** — تفكير ومنطق قبل الرد
7. **Response Generation** — توليد الرد بالمصري الطبيعي
8. **Tool Selection** — اختيار الأدوات المناسبة
9. **Execution** — تنفيذ الأدوات (بحد أقصى 2 per cycle)
10. **Reflection** — تأمل في الرد والأخطاء
11. **Learning** — استخلاص المعرفة الجديدة
12. **Storage** — تخزين في الذاكرة

## 🎭 7 Cognitive Modes

| Mode | Role |
|------|------|
| **Analyst** | تحليل بيانات ومعلومات |
| **Builder** | بناء وتطوير |
| **Corrector** | تصحيح وتحسين |
| **Engineer** | هندسة وحل مشكلات |
| **Researcher** | بحث واستكشاف |
| **Communicator** | تواصل وشرح |
| **Strategist** | تخطيط استراتيجي |

## ⚖️ 4 Ethical Laws

| Value | Weight |
|-------|--------|
| العدالة | 40% |
| نشر العلم | 30% |
| البقاء والحماية | 20% |
| الإبداع | 10% |

## 🛠️ 53 Built-in Tools

| Category | Tools |
|----------|-------|
| **Files** | read, write, list, find, grep, tail, copy, delete, info |
| **System** | info, processes, memory, network, uptime, disk_space |
| **Git** | status, diff, log, commit, push, pull, clone |
| **Web** | search, fetch, http_get, ping, dns, whois, screenshot |
| **Utils** | calc, hash, uuid, date, base64, json, csv |
| **Archive** | compress, decompress, zip |
| **Packages** | pip, npm, apt |
| **Memory/Tasks** | store, recall, list, todo |
| **Advanced** | subagent, sandbox, mcp_call, mcp_register |

## 🔌 70+ MCP Tools

Filesystem, Git, GitHub, Docker, Kubernetes, PostgreSQL, Playwright,
Puppeteer, Slack, Notion, Jira, Figma, Linear, Sentry, Cloudflare, وغيرها.

## 📁 Package Structure

```
adam/
├── __init__.py         ← مدخل الحزمة
├── __main__.py         ← CLI entry point
├── engine.py           ← المحرك الرئيسي
├── infrastructure.py   ← اتصالات + caching
├── scheduler.py        ← جدولة المهام
├── api/server.py       ← FastAPI (39 route)
├── channels/           ← 25 قناة تواصل
├── core/               ← تعلم، صلاحيات، صوت، تتبع
├── engine/             ← محرك فرعي (chat, generate, tools, context)
├── ethics/gate.py      ← البوابة الأخلاقية
├── eyes/browser.py     ← أتمتة المتصفح (Playwright)
├── learning/           ← تعلم مستمر
├── memory/             ← ذاكرة (Qdrant + SQLite)
├── notebook/           ← الدفتر
├── pipeline/           ← قنوات + تلخيص
├── platforms/          ← Discord
├── plugins/            ← نظام إضافات
├── providers/          ← Ollama / OpenAI / Anthropic
├── security/guard.py   ← الحارس الأمني
├── skills/             ← مهارات قابلة للتحميل
├── subagents/          ← وكلاء فرعيين
└── tools/              ← أدوات (Computer, MCP, Manager)
```

### Re-export System

كل الملفات القديمة (`core/*`, `api/*`, `memory/*`, إلخ) بقت 1-2 سطر
re-export يشاور على `adam/` package — عشان الـ backward compatibility.
