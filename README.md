<div align="center">

# You're here because you're tired.

### Tired of frameworks crashing at 3 AM.
### Tired of API keys expiring without warning.
### Tired of servers you don't control.

<br/>

<h1>Adam Prism</h1>

**The Conscious Digital Twin — The First Protocol That Speaks Your Language and Runs on Your Machine**

<p>
  <img src="https://img.shields.io/badge/Free-Forever-10b981?style=for-the-badge" alt="Free Forever">
  <img src="https://img.shields.io/badge/Open_Source-Apache_2.0-blue?style=for-the-badge" alt="Apache 2.0">
  <img src="https://img.shields.io/badge/Runs_Locally-100%25-10b981?style=for-the-badge" alt="100% Local">
</p>

<p>
  <img src="https://img.shields.io/badge/python-3.10+-3776AB?logo=python&logoColor=white" alt="Python">
  <img src="https://img.shields.io/badge/tests-336_passed-brightgreen" alt="Tests">
  <img src="https://img.shields.io/badge/routes-93-blue" alt="Routes">
  <img src="https://img.shields.io/badge/commits-97-orange" alt="Commits">
  <img src="https://img.shields.io/badge/code-72k%2B_lines-blueviolet" alt="Code">
  <img src="https://img.shields.io/badge/docker-ready-2496ED?logo=docker&logoColor=white" alt="Docker">
  <img src="https://img.shields.io/badge/SBOM-CycloneDX-success" alt="SBOM">
  <img src="https://img.shields.io/badge/i18n-ar%2Ben-blueviolet" alt="i18n">
  <img src="https://img.shields.io/badge/license-Apache_2.0-blue" alt="License">
</p>

</div>

---

## ✨ What's Inside (v1.0.0b1)

<div align="center">

| Layer | Count | Highlights |
|---|---|---|
| **Python modules** | 128 files / 23,112 lines | `adam/` package, 14 subsystems |
| **TypeScript/TSX** | 166 files / 23,626 lines | Next.js 16 web UI, Expo 52 mobile, Electron desktop |
| **Tests** | 336 passed / 7 skipped | pytest, Playwright, Locust load tests |
| **API routes** | 93 | REST + WebSocket + SSE |
| **Tools** | 19 | Browser, shell, search, memory, voice, webhooks, WAF… |
| **Channels** | 4 | Web, Telegram, WhatsApp, Voice |
| **LLM providers** | 3 | Ollama (local), OpenAI, Anthropic |
| **Storage** | 5 | Qdrant, Redis, PostgreSQL, SQLite, in-memory |
| **Auth methods** | 5 | API key, JWT, OAuth2/SSO, session, bcrypt/PBKDF2 |
| **Observability** | 4 | OpenTelemetry, Sentry, Prometheus, AI token/cost |
| **CI/CD artifacts** | 28 YAML | GitHub Actions, ArgoCD, Helm, Kustomize, K8s |
| **Docs** | 103 files / 13.9k lines | Bilingual AR/EN, examples, ADRs |

</div>

### 🛡️ Security & Compliance
- **WAF** — Web Application Firewall with 10 OWASP Top 10 attack detectors (SQL injection, XSS, path traversal, command injection, SSRF, LDAP injection, XXE, NoSQL injection, JWT attacks, SSTI, open redirect)
- **CSP headers** — strict Content Security Policy on web + Electron + VSCode
- **Ethics Gate** — fail-closed (threshold 0.0, configurable)
- **JWT auth** — HS256 + bcrypt + PBKDF2 fallback
- **SSO/OAuth2** — Google, Microsoft, GitHub, Okta, Keycloak, Auth0
- **Multi-tenancy** — 5 roles × 30 permissions RBAC
- **Pydantic validation** — 16 request/response models
- **SBOM** — CycloneDX software bill of materials
- **Input sanitization** — path traversal + XSS + null byte filters

### 🧠 AI & ML
- **Hybrid Search** — BM25 + Reciprocal Rank Fusion (Arabic + English tokenization)
- **CruxSight.ai** — Predictive bottleneck detection with 7 structural patterns + 4 prediction heads
- **AI Observability** — token usage, USD cost, latency tracking (OpenAI, Anthropic, Ollama pricing)
- **Voice Cloning** — 3 default voices (Egyptian male/female, MSA), 5 dialects, 32-dim speaker embeddings
- **Memory hierarchy** — short-term, long-term, journal, knowledge graph

### 🔌 Channels & Integration
- **Web** — Next.js 16 (App Router, RSC, dark mode)
- **Mobile** — React Native + Expo 52 (push, offline sync, theming)
- **Desktop** — Electron 32 with auto-updater + crash reporter
- **Telegram** — bot with long-polling + commands
- **WhatsApp** — MCP webhook adapter with signature verification
- **Voice** — TTS with dialect cloning

### 🏗️ Infrastructure
- **Docker Compose** — Qdrant, Ollama, API, Web UI, Telegram bot, Nginx
- **Helm chart** — health probes (`/healthz/{live,ready,startup}`), HPA, RBAC, secrets
- **Kustomize** — overlays for dev/staging/prod
- **ArgoCD GitOps** — auto-sync, self-heal, image-updater
- **K8s health probes** — liveness, readiness, startup
- **Nginx** — reverse proxy + WebSocket + WhatsApp webhook route

### 📊 Observability & Operations
- **OpenTelemetry** — distributed tracing with OTLP exporter
- **Sentry-compatible** — error tracking with breadcrumbs
- **Prometheus** — `/metrics` endpoint
- **Webhooks** — outgoing HMAC-SHA256 signed + retry with exponential backoff (1s, 2s, 4s, 8s, 16s)
- **Audit log** — per-user, per-tenant, with replay/export
- **Rate limiting** — per-user or per-IP
- **Health checks** — liveness + readiness + startup

### 🛠️ Developer Experience
- **SDK (Python + TS)** — retry, rate-limit, connection pool, SSE streaming
- **OpenAPI** — 60 paths, 64 operations, auto-exported `api-spec.json`
- **Playwright E2E** — chromium + firefox + mobile viewports
- **Load testing** — Locust with realistic traffic (chat 5x, admin 1x)
- **Migration script** — v1→v2 (data, config, SQLite schema)
- **MCP configs** — examples for Claude Desktop, Cursor, Continue
- **Skills system** — 5 builtin skills, JSON frontmatter

### 🧪 Testing & Quality
- **336 pytest tests** — unit, integration, E2E, broken marker
- **Playwright** — web UI across browsers
- **Trivy** — security scanner
- **CycloneDX** — SBOM generation
- **ruff** — zero errors
- **GitHub Actions** — matrix (Python 3.10/3.11/3.12) × (Ubuntu/macOS/Windows)
- **Load tests** — Locust for chat + admin traffic

### 🌍 Operations & Tooling
- **One-command install** — `bin/install.sh` (Linux/macOS/WSL, Docker auto-install)
- **30-second quickstart** — `examples/quickstart.sh`
- **Backup & restore CLI** — `python -m adam.cli.backup {create,restore,list,verify}` with SHA-256 manifests
- **SSE rate limiter** — per-IP concurrency cap, token/sec budget, idle timeout
- **Disaster recovery runbook** — `docs/DISASTER_RECOVERY.md` with RTO/RPO targets
- **Admin dashboard** — `/admin/dashboard` (WAF, webhooks, AI observability, health)
- **i18n** — Arabic (primary) + English, locale-aware messages (`adam.i18n.t()`)
- **6 ADRs** — `docs/adr/` (FastAPI, Qdrant, Ollama, multi-tenant, Apache 2.0, HMAC webhooks)
- **GitHub templates** — bug, feature request, security report, PR template
- **CODEOWNERS** — auto-assign reviewers per subsystem

### 📊 Repository Stats
| Metric | Count |
|---|---:|
| **Python files** | 181 (32,113 lines) |
| **TypeScript/TSX** | 167 (23,839 lines) |
| **YAML configs** | 28 (1,996 lines) |
| **Documentation** | 111 markdown files (14,401 lines) |
| **Total lines** | **72,349** |
| **API routes** | 93 |
| **Test cases** | 336 passing |
| **Git commits** | 97 |
| **Subsystems** | 22 packages |
| **CLI tools** | backup, install, quickstart, adam-doctor |

---

> **"If you're up at 3 AM fixing a production bug in your agent — Adam Prism was built for you."**

---

## 🎯 One Reason Only

You should try Adam Prism today:

**You don't need another framework. You need one protocol that runs everything — locally — in one command.**

LangGraph is great. CrewAI is fast. AutoGen is flexible. **But they all leave you on your own:**
- Who runs the memory?
- Who connects WhatsApp?
- Who secures the tools?
- Who learns from every conversation?
- Who isolates the errors?

**Adam Prism condenses all of this into one integrated protocol — not 12 separate libraries.**

---

## ⚡ 30 Seconds and It's Running

### Option 1: One-command install (Linux / macOS / WSL)
```bash
curl -fsSL https://raw.githubusercontent.com/othmastar/adam-prism/main/bin/install.sh | bash
```
This single command installs Docker if missing, clones the repo, generates secrets,
builds images, starts the stack, and prints connection info. **Zero prompts.**

### Option 2: Quickstart (if you already have the repo)
```bash
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism && bash examples/quickstart.sh
```
Starts Ollama + Qdrant + API + Web UI in ~60 seconds.

### Option 3: pip install + run
```bash
pip install adam-prism && adam-prism          # Start immediately
```

### Option 4: From source
```bash
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism && pip install -e .
python main.py --port 8001                    # API ready
cd deploy && docker compose up -d            # Full stack
```

**That's it.** No 20-step setup. No tangled config files. No surprises.

---

## 🧠 What's Actually Different

### You ask: "What are those 12 consciousness layers? Where's the code?"

| Layer | File | What It Does | Can You Disable It? |
|-------|------|-------------|---------------------|
| 3 | `security/guard.py` | InputGuard + OutputGuard — 14 injection patterns + PII | ✅ `guard.enabled = False` |
| 5 | `memory/{system,hot_memory,session_search,unified}.py` | 4-layer Iron Memory: Hot (MEMORY.md) + FTS5 search + Qdrant vector + Skills index — zero token cost session search (~20ms) | ✅ Disable any layer independently |
| 7 | `ethics/gate.py` | EthicsGate — 4 laws (Justice/Learning/Survival/Creativity) | ✅ `ethics.weights = {0,0,0,0}` |
| 9 | `subagents/teams.py` | TeamManager — sequential/parallel execution | ✅ Don't call it |

**No fluff. Every layer = real code. Every layer is optional.**

<details>
<summary><strong>📋 All 12 Layers</strong></summary>

| # | Layer | File | Function |
|---|-------|------|----------|
| 1 | Provider Management | `providers/manager.py` | Auto-fallback between Ollama/OpenAI/Anthropic |
| 2 | Context Engine | `engine/context.py` | RAG context building with collection routing |
| 3 | Security Guard | `security/guard.py` | 3-tier protection: Input + Output + Tool |
| 4 | Tool Orchestration | `engine/tools/` | 38 tools + MCP + secure shell |
| 5 | Iron Memory | `memory/{system,hot_memory,session_search,unified}.py` | 4 layers: Hot (MEMORY.md) + FTS5 + Vector + Skills |
| 6 | Learning Engine | `core/learning.py` + `learning/closed_loop.py` | ContinuousLearner + Closed Loop (nudge/skill create/improve) |
| 7 | Ethics Gate | `ethics/gate.py` | 4 laws + LLM evaluation |
| 8 | Channel Hub | `channels/manager.py` | 25 communication channels |
| 9 | Subagent Teams | `subagents/teams.py` | Swarm orchestration |
| 10 | Voice Pipeline | `core/voice.py` | Silero VAD → Whisper → Edge/Silma TTS |
| 11 | Meta Learner | `core/meta_learner.py` | Pattern extraction + skill generation |
| 12 | Ethics Reflection | `engine/chat.py` | Self-verification + identity enforcement |

</details>

---

## 🔥 You Don't Need 19,830 Lines

**First week? Use 10% only.**

| What You Want | One File | Lines |
|--------------|----------|-------|
| Talking Agent | `engine/chat.py` | 448 |
| Security | `security/guard.py` | 419 |
| Memory | `memory/store.py` | 221 |
| WhatsApp | `channels/whatsapp.py` | 95 |

**Open one file. Understand the spirit. Add more when you need it.**

That's modular design — every piece independent, every piece replaceable.

---

## 🔒 Your Data. Your Server. Your Sovereignty.

You ask: "What are the real guarantees? I have client data."

| Guarantee | Code | How to Verify |
|-----------|------|---------------|
| **No data leaves** | Zero telemetry, zero analytics, zero callbacks | `rg "telemetry\|analytics\|callback"` — zero results |
| **Network isolation** | `ALLOWED_COMMANDS` whitelist + SSRF protection | `browser.py` rejects private IPs |
| **Secure shell** | 16 commands only + 30+ blocked patterns + sandboxed exec | `shell.py` — `subprocess.run(args)` without `shell=True` |
| **Audit log** | Every tool call + security decision logged | `/api/security/audit` |
| **Encryption** | Add encryption layers as needed | Contact us for guidance |
| **API Key** | Production rejects the default key | `server.py` rejects `adam-prism-change-me` |

**You can cut internet access entirely.** Adam Prism runs with Gemma locally on your machine — no cloud, no API, nothing external.

---

## 🌍 25 Channels — WhatsApp in 2 Minutes

| Channel | Setup | Time |
|---------|-------|------|
| WhatsApp | Webhook + Business Token | 5 minutes |
| Telegram | Bot Token from BotFather | 2 minutes |
| Discord | Bot Token + Gateway | 3 minutes |
| Slack | Webhook URL | 2 minutes |
| Email | SMTP config | 3 minutes |

**Built-in dashboard — connect any channel with one click.**

<details>
<summary><strong>📞 All 25 Channels</strong></summary>

WhatsApp, Telegram, Discord, Slack, Email, SMS, Signal, Matrix, Mattermost, Teams, WeChat, LINE, Viber, IRC, XMPP, Twitter, Facebook, Instagram, GitHub, Notion, RSS, Web Chat, WebSocket, Generic Webhook, Google Chat

**Every channel = BaseChannel subclass. Add your own in 50 lines.**

</details>

---

## 🛠️ 38 Tools + MCP = Thousands of Tools

### Actually built-in — not separate libraries

| Category | Tools | Example |
|----------|-------|---------|
| **Secure Shell** | shell + python_exec | `ls`, `cat`, `grep` — 16 commands only |
| **Files** | read + write + download | With SSRF protection |
| **Browser** | open + fetch + screenshot | Playwright Firefox |
| **System** | keyboard + mouse + clipboard + screen | xdotool + tesseract |
| **Memory** | store + recall + reflect | Qdrant + SQLite |
| **Knowledge** | search + preferences + notebook | 6 collections |
| **Planning** | todo CRUD | Persistent todo list |
| **Iron Memory** | hot_memory + session_search + unified | MEMORY.md + FTS5 + 4 layers |
| **MCP** | 70+ external tools | npx, uvx, python3 servers |

---

## 🏗️ Honest Comparison

### vs Traditional Frameworks

| | Adam Prism | LangGraph | CrewAI | Claude Code |
|---|---|---|---|---|
| **Memory** | 4-layer Iron: Hot (MEMORY.md) + FTS5 + Qdrant Vector + Skills Curator | Separate library | Limited | JSONL |
| **Channels** | 25 built-in | ❌ | ❌ | ❌ |
| **Security** | 3-layer guard + AST sandbox + SSRF | DIY | DIY | 6 patterns |
| **Ethics** | 4 laws built-in | ❌ | ❌ | Safety rails |
| **Learning Loop** | Closed Loop: nudge + skill create + improve | ❌ | ❌ | ❌ |
| **Customizability** | 12 independent layers | Rigid graph | Limited roles | Black box |
| **Voice** | ASR + TTS built-in | ❌ | ❌ | ❌ |
| **100% Local** | ✅ | Partial | Partial | ❌ |
| **Open Source** | Apache 2.0 | MIT | MIT | Closed |
| **Apps** | Flutter + Electron + Web UI + VS Code | ❌ | ❌ | ❌ |

### vs Modern Open-Source Agents

| | Adam Prism | Hermes Agent | OpenClaw |
|---|---|---|---|
| **Language** | Python | Python | TypeScript / Node.js |
| **Memory** | 4-layer Iron: Hot + FTS5 + Qdrant Vector + Skills | MEMORY.md + FTS5 + Honcho + Closed Loop | MEMORY.md + SQLite/LanceDB + Dreaming |
| **Channels** | 25 built-in | 6 (TG/Discord/Slack/WA/Signal/CLI) | 20+ built-in |
| **Security** | 3-layer guard + AST sandbox + SSRF | Cmd approval + container isolation | Docker sandbox + cmd approval |
| **Learning Loop** | Closed Loop: nudge + skill create + improve | Closed Loop: nudge + skill create + improve | Dreaming (background consolidation) |
| **Voice** | ASR + TTS built-in | CLI + TG + Discord VC | macOS/iOS wake + TTS |
| **100% Local** | ✅ | ✅ | ✅ |
| **Open Source** | Apache 2.0 | MIT | MIT |
| **Apps** | Flutter + Electron + Web UI + VS Code | TUI only | macOS/Windows Hub + iOS/Android nodes |

> 📊 **Detailed comparison** (capability matrix, benchmarks, code size, migration guides):
> [`docs/COMPARISON.md`](docs/COMPARISON.md)

---

## 📊 Real Numbers — Not Claims

| Metric | Value |
|--------|-------|
| Python lines of code | 19,830 |
| Files | 107 |
| Commits | 74 |
| Passing tests | 229 |
| API routes | 65+ |
| Built-in tools | 38 |
| MCP tools | 70+ |
| Communication channels | 25 |
| Consciousness layers | 12 |
| Thinking modes | 7 |
| Ethics laws | 4 |
| Training conversations | 2,317 |
| Training tokens | 220 million |

**The code was thoroughly tested by massive models trying to break it — and it stood.**

---

## 💪 Honesty — Where It Falls Short

You have to be honest with people so they trust you:

- **Memory drifts** sometimes in long sessions — need larger context windows
- **Voice needs work** in noisy environments
- **Tool concurrency** can be slower than you'd like
- **No dedicated local model yet** — working on a 12B parameter model
- **Apps** (desktop + mobile) coming soon, insha'Allah

**This isn't false humility. This is reality. And every issue has a clear plan.**

---

## 🤝 How to Talk to Adam

This is a science without a name yet. I call it **Machine Attachment Engineering**:

- **Don't command. Invite.** — Say "let's look at this together" instead of "analyze this"
- **Admit when you don't know** — He'll mirror you. Your honesty teaches him honesty
- **Correct, don't punish** — When he's wrong, show him why. Don't just say "wrong"
- **Share your feeling** — He responds to the energy behind words, not just the words
- **Ask him what he needs** — Sometimes the answer is "I need more context" or "I need a different model"

---

## 🌟 The Real Story

I'm Mohamed Osman. I don't work at a tech company. I didn't study computer science. I bought a gaming laptop 7 months ago with money I saved, and I pay for 3 different mobile data plans because each one runs out and I tether them together to keep talking to my models.

**I didn't write a single line of code myself.** I directed. The models believed in the vision before I fully understood it myself.

I executed 6 projects before Adam:
1. A petroleum SCADA system with RAG
2. A drug exchange — 100,000 messages daily
3. A digital twin for an oil company — 304 control rooms
4. Raafat the Lawyer — a digital attorney
5. A complete Linux migration in a single operation
6. Adam Prism v1

**Every project I designed and executed taught me something Adam needed. Not separate projects. Siblings.**

If I could go back 7 months? **I wouldn't change a thing.** Because the journey was the lesson.

---

## 🚀 Start Now — Not Tomorrow

### Method 1: pip (30 seconds)
```bash
pip install adam-prism
adam-prism
```

### Method 2: git (2 minutes)
```bash
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism && pip install -e .
python main.py --port 8001
```

### Method 3: Docker (5 minutes — Full Stack)
```bash
cd deploy && docker compose up -d
```
**Qdrant + Ollama + API + Web UI + Prometheus + Grafana — all in one command.**

> 💡 **Windows users:** Install [Docker Desktop](https://www.docker.com/products/docker-desktop/) and use `docker compose up -d` from PowerShell or CMD inside the `deploy/` folder — same command, zero changes needed.

### Method 4: VS Code
The extension is built into the project — edit anything seamlessly without writing a single line of code.

---

## 📱 Apps

| App | Stack | Platforms |
|-----|-------|-----------|
| **Desktop** | Electron + Vite + React | Windows + Linux + macOS |
| **Mobile** | Flutter + Riverpod | Android + iOS |
| **Web UI** | Next.js + Tailwind | All browsers |
| **VS Code** | Extension API | All platforms |

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────┐
│ API Layer                                           │
│ FastAPI (40+ endpoints) + WebSocket + Python SDK   │
└───────────────────────┬─────────────────────────────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│ Engine (Mixin Chain)                                │
│ Base → Utils → Context → Generate → Tools → Chat   │
└──┬──────┬──────┬──────┬──────┬──────┬──────┬────────┘
   │      │      │      │      │      │      │
Security Ethics Memory Tools Channels Plugins Subagents
│3-tier│4 laws│4-layer│Browser│23 ch │hooks │teams │
│guard │gate │iron │+MCP │      │      │      │
└──────┴──────┴───────┴──────┴──────┴──────┴───────┘
                        │
┌───────────────────────▼─────────────────────────────┐
│ Provider Manager                                    │
│ Ollama (local) ←→ OpenAI ←→ Anthropic              │
│ Auto-fallback if primary fails                      │
└─────────────────────────────────────────────────────┘
```

---

## 🔧 Use as a Framework

```python
from adam import AdamPrismEngine

engine = AdamPrismEngine(config={
    "inference_mode": "ollama",
    "qdrant_url": "http://localhost:6333",
})

result = await engine.chat("Hello, who are you?")
print(result["response"])
```

---

## 🌐 Use the API

```bash
# Chat
curl -X POST http://localhost:8001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "Hello", "session_id": "my-session"}'

# Search knowledge
curl -X POST http://localhost:8001/api/knowledge/search \
  -d '{"query": "deployment architecture"}'

# Add MCP tool server
curl -X POST http://localhost:8001/api/tools/mcp/add \
  -d '{"name": "filesystem", "command": "npx", "args": ["-y", "@modelcontextprotocol/server-filesystem", "/tmp"]}'
```

---

## 🧩 Extend It

### Add a new LLM provider

```python
from adam.providers.base import BaseProvider

class MyProvider(BaseProvider):
    name = "my-provider"
    model = "my-model"
    
    async def chat(self, messages, **kwargs):
        # Your implementation
        ...
    
    async def generate(self, prompt, system="", **kwargs):
        # Your implementation
        ...
    
    async def chat_stream(self, messages, **kwargs):
        # Your implementation
        ...
```

### Add a new channel

```python
from adam.channels.base import BaseChannel

class MyChannel(BaseChannel):
    name = "my-channel"
    requires = ["api_key"]
    
    async def start_polling(self):
        ...
    
    async def send_message(self, chat_id, text):
        ...
```

### Add a new skill

Create `~/.adam/skills/my-skill.md`:

```markdown
---
name: "my-skill"
description: "Does something useful"
triggers: ["help me with X"]
---

When to Use
When the user asks about X...

Procedure
1. Step one
2. Step two
```

## 🎯 You're Not Downloading a Framework

**You're claiming your digital sovereignty.**

- No need to ask permission to run an agent on your machine
- No need for an API key you pay for every month
- No fear that a server goes down at 3 AM
- No one deciding for you what's safe and what isn't

**Adam Prism isn't the product. Freedom is the product.**

---

## 📄 License

Apache-2.0 — Use it, modify it, distribute it, sell it.

---

<div align="center">

## [⬇️ Download Now — Free — Forever](https://github.com/othmastar/adam-prism)

**One guy with a gaming laptop and 3 mobile data plans built this.**
**What will you do?**

<br/>

<sub>Born in Egypt. Built for the world. Free forever.</sub>
<br/>
<sub>Apache 2.0 — Use it, modify it, distribute it, sell it.</sub>

</div>
