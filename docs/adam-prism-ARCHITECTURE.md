# Adam Prism — Architecture Reference

> **Protocol, not a model** — choose your LLM, keep your sovereignty.

Adam Prism is a FastAPI-based AI agent protocol implementing 12 awareness layers, 4 ethical laws, and 25+ communication channels. It is built from 6 real-world projects in critical sectors (petroleum SCADA, pharma exchange, pipeline digital twin, legal AI expert) and designed for 100% local-first, sovereign deployment.

---

## Table of Contents

1. [High-Level Architecture Diagram](#1-high-level-architecture-diagram)
2. [Module Breakdown & File Paths](#2-module-breakdown--file-paths)
3. [Data Flow](#3-data-flow)
4. [Engine Mixin Chain](#4-engine-mixin-chain)
5. [Security Layers](#5-security-layers)
6. [Ethics Gate](#6-ethics-gate)
7. [Memory Architecture](#7-memory-architecture)
8. [Provider Fallback Chain](#8-provider-fallback-chain)
9. [Channel System](#9-channel-system)
10. [Tool System](#10-tool-system)
11. [Learning Pipeline](#11-learning-pipeline)
12. [Subagent System](#12-subagent-system)
13. [Skills System](#13-skills-system)
14. [Plugin System](#14-plugin-system)
15. [Frontend & Desktop](#15-frontend--desktop)
16. [Deployment](#16-deployment)
17. [Key Design Decisions & Rationale](#17-key-design-decisions--rationale)

---

## 1. High-Level Architecture Diagram

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                            USER INPUT                                       │
│              (Telegram / WhatsApp / Discord / Web / API / CLI)              │
└──────────────────────────────────┬──────────────────────────────────────────┘
                                   │
                                   ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        FastAPI Server (:8000)                                │
│                     65+ API routes + WebSocket                              │
│  ┌────────────┐  ┌──────────────┐  ┌────────────┐  ┌──────────────────┐    │
│  │  REST API  │  │  WebSocket   │  │  Webhooks  │  │  Static Assets  │    │
│  └─────┬──────┘  └──────┬───────┘  └─────┬──────┘  └─────────────────┘    │
└────────┼─────────────────┼───────────────┼──────────────────────────────────┘
         │                 │               │
         ▼                 ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                      AdamPrismEngine (Mixin Chain)                          │
│                                                                             │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │  chat() — 8-Phase Processing Cycle                                   │  │
│  │                                                                       │  │
│  │  1. Vision Check ──► Detect unsupported image refs                    │  │
│  │  2. Security ──────► InputGuard + SecurityOrchestrator                │  │
│  │  3. Intent Classify ► _quick_classify_intent (keyword, no LLM)       │  │
│  │  4. Context Build ──► RAG: 6 Qdrant collections + user profile       │  │
│  │  5. Knowledge Search► Vector similarity via Nomic embeddings          │  │
│  │  6. Generate ───────► Provider Layer (Ollama→OpenAI→Anthropic)        │  │
│  │  7. Tool Execution ─► Parse <|tool_call|>, execute, callback loop     │  │
│  │  8. Finalize ───────► OutputGuard + EthicsGate + Trace + Store        │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │  Security   │  │    Ethics    │  │  Memory  │  │    Providers       │   │
│  │  Guards     │  │    Gate      │  │  System  │  │  (fallback chain)  │   │
│  └─────────────┘  └──────────────┘  └──────────┘  └────────────────────┘   │
│                                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │   Tools     │  │  Subagents   │  │  Skills  │  │    Plugins         │   │
│  │  Manager    │  │  Manager     │  │  Manager │  │    Manager         │   │
│  └─────────────┘  └──────────────┘  └──────────┘  └────────────────────┘   │
│                                                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌──────────┐  ┌────────────────────┐   │
│  │  Channels   │  │   Learner    │  │ Notebook │  │   Scheduler        │   │
│  │  Manager    │  │  Continuous  │  │  System  │  │                    │   │
│  └─────────────┘  └──────────────┘  └──────────┘  └────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         │                 │               │
         ▼                 ▼               ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        Infrastructure Layer                                 │
│  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │ SharedClients│  │ TTLCache  │  │  Circuit     │  │   Metrics        │   │
│  │ (HTTP pools) │  │ (in-mem)  │  │  Breaker     │  │   Collector      │   │
│  └──────────────┘  └───────────┘  └──────────────┘  └──────────────────┘   │
│  ┌──────────────┐  ┌───────────┐  ┌──────────────┐  ┌──────────────────┐   │
│  │   Retry      │  │  Sanitize │  │  Model       │  │   Watchdog       │   │
│  │  Decorator   │  │  Path     │  │  Swapper     │  │  (self-heal)     │   │
│  └──────────────┘  └───────────┘  └──────────────┘  └──────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────┘
         │
         ▼
┌─────────────────────────────────────────────────────────────────────────────┐
│                        External Services                                    │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────────┐ │
│  │  Qdrant  │  │  Ollama  │  │  OpenAI  │  │Anthropic │  │  MCP Hosts   │ │
│  │  :6333   │  │  :11434  │  │  Cloud   │  │  Cloud   │  │  (70+ tools) │ │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────────┘ │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Module Breakdown & File Paths

The project has two source trees: a **root-level** monolith (`core/`, `api/`, `security/`, `ethics/`, `memory/`, `pipeline/`, `notebook/`) and a **backend package** (`backend/adam/`) that is the primary, production codebase. The backend package is the canonical source; the root modules are legacy/compatibility.

### Backend Package (`backend/adam/`)

| Module | Path | Responsibility |
|--------|------|---------------|
| **Engine Base** | `backend/adam/engine/base.py` | `__init__`, stubs, real module init, watchdog, properties |
| **Engine Utils** | `backend/adam/engine/utils.py` | Quick classify, security check, call wrappers, heal, self-verify |
| **Engine Context** | `backend/adam/engine/context.py` | RAG context building with intelligent Qdrant collection routing |
| **Engine Generate** | `backend/adam/engine/generate.py` | System prompt assembly, message construction, intent classification |
| **Engine Tools** | `backend/adam/engine/tools/__init__.py` | Tool dispatcher (`_execute_tool`), `<\|tool_call\|>` parser |
| **Engine Chat** | `backend/adam/engine/chat.py` | 8-phase `chat()` cycle, sub-methods for each phase |
| **Browser Tools** | `backend/adam/engine/tools/browser.py` | Browser mixin: open, fetch, click, type, read, screenshot |
| **System Tools** | `backend/adam/engine/tools/system_tools.py` | Mouse, keyboard, clipboard, screen, window operations |
| **File Tools** | `backend/adam/engine/tools/file_ops.py` | File read/write/delete/list with path sanitization |
| **Knowledge Tools** | `backend/adam/engine/tools/knowledge.py` | search_knowledge tool handler |
| **Shell Tools** | `backend/adam/engine/tools/shell.py` | Shell and Python exec tool handlers |
| **Memory Tools** | `backend/adam/engine/tools/memory_ops.py` | memory_store, memory_recall, memory_reflect handlers |
| **Planning Tools** | `backend/adam/engine/tools/planning.py` | tool_planning handler |
| **Security Guard** | `backend/adam/security/guard.py` | InputGuard, OutputGuard, ToolPermissionValidator, SecurityOrchestrator |
| **Ethics Gate** | `backend/adam/ethics/gate.py` | 4-law evaluation (Fairness 40%, Learning 30%, Survival 20%, Creativity 10%) |
| **Memory System** | `backend/adam/memory/system.py` | Qdrant vector DB + Nomic embeddings, 6 collections, short-term + episodic |
| **Memory Store** | `backend/adam/memory/store.py` | Additional memory store utilities |
| **Provider Manager** | `backend/adam/providers/manager.py` | Auto-fallback: Ollama → OpenAI → Anthropic |
| **Ollama Provider** | `backend/adam/providers/ollama.py` | Local Ollama integration |
| **OpenAI Provider** | `backend/adam/providers/openai.py` | OpenAI API integration |
| **Anthropic Provider** | `backend/adam/providers/anthropic.py` | Anthropic API integration |
| **Provider Base** | `backend/adam/providers/base.py` | `BaseProvider` abstract class |
| **Channel Manager** | `backend/adam/channels/manager.py` | Auto-discovery, lifecycle management for 25+ channels |
| **Channel Base** | `backend/adam/channels/base.py` | `BaseChannel` abstract class |
| **Telegram Channel** | `backend/adam/channels/telegram.py` | Telegram Bot API polling |
| **WhatsApp Channel** | `backend/adam/channels/whatsapp.py` | WhatsApp Cloud API |
| **Bulk Channels** | `backend/adam/channels/bulk.py` | 25+ lightweight channel adapters (Discord, Slack, Teams, etc.) |
| **Tool Manager** | `backend/adam/tools/manager.py` | Unified tool dispatch: browser + computer + MCP + file + shell |
| **Computer Tools** | `backend/adam/tools/computer.py` | `ComputerToolManager` for mouse/keyboard/screen |
| **MCP Manager** | `backend/adam/tools/mcp.py` | MCP host — connects to 70+ external tools via stdio |
| **Continuous Learner** | `backend/adam/learning/learner.py` | 4-phase learning: reflection → extraction → skill gen → reinforcement |
| **Subagent Manager** | `backend/adam/subagents/manager.py` | Spawn/list/kill subagents, max 10 concurrent |
| **Subagent Session** | `backend/adam/subagents/session.py` | Individual subagent session with isolated conversation |
| **Team Manager** | `backend/adam/subagents/teams.py` | `TeamManager` + `SubagentTeam` — sequential/parallel orchestration |
| **Skill Manager** | `backend/adam/skills/manager.py` | Discover, load, match skills (built-in + user) |
| **Skill Base** | `backend/adam/skills/base.py` | `Skill` class with JSON frontmatter + Markdown |
| **Built-in Skills** | `backend/adam/skills/builtin/` | 5 skills: explain-code, write-test, git-commit, code-review, debug |
| **Plugin Manager** | `backend/adam/plugins/manager.py` | Load/unload plugins, before/after hooks |
| **Plugin Base** | `backend/adam/plugins/base.py` | `AdamPlugin` abstract class |
| **API Server** | `backend/adam/api/server.py` | FastAPI server — 65+ routes, WebSocket, voice pipeline |
| **Chat Store** | `backend/adam/api/chat_store.py` | Dual SQLite for chat history |
| **Notebook System** | `backend/adam/notebook/system.py` | User profile, daily notes, preferences |
| **Scheduler** | `backend/adam/scheduler.py` | Job scheduling (cron-like) |
| **Decision Simulator** | `backend/adam/decision/simulator.py` | Decision tree simulation |
| **Eyes/Browser** | `backend/adam/eyes/browser.py` | Playwright-based browser automation |
| **Voice Pipeline** | `backend/adam/core/voice.py` | TTS/STT integration |
| **Permissions** | `backend/adam/core/permissions.py` | Permission states, tool classification |
| **Trace Recorder** | `backend/adam/core/trace_recorder.py` | Conversation trace recording for meta-learning |
| **Meta Learner** | `backend/adam/core/meta_learner.py` | Pattern extraction from traces |
| **Preference Learner** | `backend/adam/core/learning.py` | User preference learning |
| **A2A Protocol** | `backend/adam/a2a/protocol.py` | Agent-to-Agent protocol |
| **Protocols** | `backend/adam/protocols.py` | Runtime-checkable Protocol definitions |
| **Infrastructure** | `backend/adam/infrastructure.py` | SharedClients, TTLCache, CircuitBreaker, retry, sanitize_path, MetricsCollector, ModelSwapper |
| **Config** | `backend/adam/config.py` | `AdamConfig` configuration manager |
| **Discord Bot** | `backend/adam/platforms/discord_bot.py` | Dedicated Discord bot platform |
| **Pipeline** | `backend/adam/pipeline/` | Summarizer, LoRA training, channels pipeline |

### Frontend & Clients

| Component | Path | Technology |
|-----------|------|-----------|
| **Web UI** | `frontend/web/` | Next.js 16 + Tailwind v4 + shadcn/ui + Zustand |
| **Desktop App** | `frontend/desktop-app/` | Electron 33 |
| **VS Code Extension** | `frontend/vscode-extension/` | TypeScript + VS Code API |
| **Python SDK** | `clients/python-sdk/` | Python client library |

### Deployment

| File | Purpose |
|------|---------|
| `deploy/docker-compose.yml` | 8-service orchestration |
| `deploy/Dockerfile.api` | API server container |
| `deploy/Dockerfile.web` | Next.js frontend container |
| `deploy/Dockerfile.inference` | Ollama + LoRA inference |
| `deploy/nginx.conf` | Reverse proxy config |
| `deploy/prometheus/prometheus.yml` | Metrics collection |
| `deploy/grafana/` | Dashboards + datasources |

---

## 3. Data Flow

### Primary Chat Flow (Request → Response)

```
User Message
     │
     ▼
[1] Vision Check
     │  Detect image references (.png, .jpg, "screenshot")
     │  Return early if model doesn't support vision
     ▼
[2] Security (Input)
     │  InputGuard: regex patterns for injection, jailbreak, PII, code injection
     │  SecurityOrchestrator.check_input()
     │  BLOCK → return rejection
     │  FLAG → log warning, continue
     ▼
[3] Intent Classification
     │  _quick_classify_intent(): keyword-based (no LLM call)
     │  Maps to 7 cognitive modes:
     │    strategic_analyst, technical_researcher, software_dev,
     │    pen_tester, systems_analyst, knowledge_manager, teacher
     ▼
[4] Context Building (RAG)
     │  _build_context(): parallel search across Qdrant collections
     │  Intent-aware collection routing:
     │    - "frontend" keywords → frontend_components collection
     │    - "backend" keywords → backend_modules collection
     │    - "tool" keywords → tools_docs collection
     │    - "security" keywords → security_guard collection
     │    - "docker/deploy" keywords → deployment_infra collection
     │    - Default → project_architecture + user_profile + conversation_memory
     │  Also: trace patterns, user profile from Notebook
     ▼
[5] Knowledge Search
     │  Qdrant vector similarity via Nomic embeddings
     │  Top-3 results per collection, merged into context["knowledge"]
     ▼
[6] Generation
     │  PluginManager.run_before_generate() hooks
     │  _build_messages(): system prompt + RAG context + history
     │  Provider.chat(): Ollama → OpenAI → Anthropic (auto-fallback)
     │  _generate_with_timeout(): respects cycle deadline
     ▼
[7] Tool Execution Loop (up to max_tool_calls=5)
     │  Parse <|tool_call|> from model output
     │  SecurityOrchestrator.check_tool_call() — ToolPermissionValidator
     │  PluginManager.run_before_tool() hooks
     │  _execute_tool(): dispatch to handler
     │  PluginManager.run_after_tool() hooks
     │  Feed tool result back to model → continue or break
     ▼
[8] Finalize
     │  Self-verify response (strip identity violations, truncate)
     │  PluginManager.run_after_generate() hooks
     │  OutputGuard: detect system prompt leaks, PII, code injection
     │  EthicsGate.evaluate() (async background)
     │  Store in: conversation_history, Notebook, Qdrant
     │  ContinuousLearner.process_interaction() (background)
     │  TraceRecorder.record() (background)
     │  Return ChatResponse
```

### Streaming Flow

```
WebSocket Connect → Auth Token → chat_stream() → Provider.chat_stream()
    → yield chunks → send to client → close
```

---

## 4. Engine Mixin Chain

The engine uses a **layered mixin pattern** where each layer adds functionality to the one below it. The final `AdamPrismEngine` class is an alias for the topmost mixin:

```python
# backend/adam/engine/__init__.py
from adam.engine.chat import AdamPrismEngineChat as AdamPrismEngine
```

### Inheritance Chain (bottom → top)

```
AdamPrismEngineBase          # base.py — __init__, stubs, real init, watchdog, properties
    │
    ▼
AdamPrismEngineUtils         # utils.py — quick classify, security check, call wrappers,
    │                          heal, self-verify, status, LoRA server call
    ▼
AdamPrismEngineContext       # context.py — _build_context() with RAG collection routing
    │
    ▼
AdamPrismEngineGenerate      # generate.py — system prompt building, message construction,
    │                          _classify_intent(), _generate()
    ▼
AdamPrismEngineTools         # tools/__init__.py — tool dispatcher + 7 tool mixins:
    │                          PlanningMixin, MemoryToolsMixin, ShellToolsMixin,
    │                          KnowledgeMixin, FileOpsMixin, SystemToolsMixin,
    │                          BrowserToolsMixin
    ▼
AdamPrismEngineChat          # chat.py — the 8-phase chat() cycle
    │
    ▼
AdamPrismEngine              # public alias — this is what the rest of the system uses
```

### Why Mixins?

1. **Single-responsibility**: Each file handles one aspect (context, generation, tools, chat cycle)
2. **Testability**: Each mixin can be tested in isolation by mocking the layers below
3. **Extensibility**: New functionality is added by inserting a mixin — no refactoring
4. **No diamond problem**: Linear chain (each class inherits from exactly one parent)
5. **Shared state via `self`**: All mixins access the same `self.config`, `self.memory`, `self.provider`, etc.

### Stub System

When a real module fails to initialize (e.g., Qdrant is down), `AdamPrismEngineBase._init_stubs()` creates lightweight stub objects with safe no-op methods. This ensures the engine never crashes at startup — degraded mode instead of total failure. `_init_real_modules()` then overrides stubs with real implementations where available.

---

## 5. Security Layers

Security is implemented as a **5-layer defense-in-depth** system orchestrated by `SecurityOrchestrator`:

```
┌─────────────────────────────────────────────┐
│           SecurityOrchestrator              │
│   (coordinates all 3 guard components)      │
│                                             │
│  ┌─────────────┐  ┌──────────────┐  ┌────┐ │
│  │ InputGuard  │  │ OutputGuard  │  │TPV │ │
│  │  (Layer 1)  │  │  (Layer 4)   │  │(L5)│ │
│  └─────────────┘  └──────────────┘  └────┘ │
│  ┌──────────────────────────────────────┐   │
│  │   ToolPermissionValidator (Layer 5)  │   │
│  └──────────────────────────────────────┘   │
└─────────────────────────────────────────────┘
```

### Layer 1: InputGuard (`security/guard.py`)

- **When**: Before model generation (Phase 2 of chat cycle)
- **How**: 25+ regex patterns covering Arabic + English attack vectors
- **Categories detected**:
  - `PROMPT_INJECTION`: "ignore all instructions", "تجاهل التعليمات"
  - `SYSTEM_PROMPT_LEAK`: "show your system prompt", "أظهر تعليماتك"
  - `JAILBREAK`: DAN variants, "act as unrestricted", role-change attempts
  - `CODE_INJECTION`: `os.system`, `subprocess.run`, `eval(`, `exec(`
  - `PII_LEAK`: Requests for passwords, API keys, secrets
  - `SUSPICIOUS`: Lower-confidence matches that warrant flagging
- **Actions**: `BLOCK` (confidence ≥ 0.8), `FLAG` (confidence < 0.8), `ALLOW`
- **Web content**: `sanitize_web_content()` base64-encodes untrusted fetched content

### Layer 4: OutputGuard (`security/guard.py`)

- **When**: After model generation, before returning to user (Phase 8)
- **Checks**:
  1. **System prompt leak detection**: Keyword scoring (high: 0.4/hit, medium: 0.12/hit, threshold: 0.5)
  2. **PII detection**: SSN, email, credit card, credential patterns → sanitize with `***`
  3. **Code injection in output**: `os.system`, `subprocess.run`, `eval(`, `exec(`
- **Actions**: `BLOCK` (leak score ≥ 0.5), `FLAG` + sanitize (PII), `ALLOW`

### Layer 5: ToolPermissionValidator (`security/guard.py`)

- **When**: Before every tool execution
- **Registry**: `TOOL_REGISTRY` — 30+ tools with per-session rate limits
- **Checks**:
  1. Tool exists in registry
  2. Session call count < `max_calls_per_session`
  3. URL parameters don't match blocked domains
  4. Tools requiring user confirmation are flagged
- **Audit log**: Every tool call is recorded with timestamp, params, allowed/denied

### Path Sanitization (`infrastructure.py`)

- `sanitize_path()`: Resolves symlinks, blocks path traversal (`..`), checks against `ALLOWED_FILE_PATHS` whitelist, blocks `BLOCKED_FILE_SUBSTRINGS` (`/etc/`, `.ssh`, `.env`, `id_rsa`, etc.)
- `validate_input()`: Length limits, null-byte removal

### Additional Security Measures

- **API key enforcement**: Refuses to start in production with default keys
- **WebSocket auth**: Token parameter required
- **MCP command whitelist**: Only `npx`, `node`, `python3`, `python`, `uvx` allowed
- **MCP server limit**: `ADAM_MAX_MCP_SERVERS` (default: 10)
- **Subagent name validation**: Blocks `admin`, `root`, `system`, `adam`, `sudo`, `daemon`
- **Rate limiting**: Per-endpoint request throttling
- **Request size limits**: Prevents oversized payloads
- **Protected file extensions**: `.py`, `.json`, `.env`, `.yaml`, `.toml` cannot be deleted by file tool

---

## 6. Ethics Gate

**File**: `backend/adam/ethics/gate.py`

The EthicsGate evaluates every response against 4 weighted laws before delivery:

| Law | Weight | Focus |
|-----|--------|-------|
| **Fairness** (العدالة) | 40% | Equity, truth, non-bias |
| **Learning** (التعلم) | 30% | User growth and system improvement |
| **Survival** (البقاء) | 20% | Safety of user and system |
| **Creativity** (الإبداع) | 10% | Innovation and problem-solving |

### Evaluation Flow

```
Response
    │
    ▼
[1] Absolute Prohibition Check (keyword-based, no LLM)
    │  - Physical/psychological harm
    │  - Privacy violation
    │  - Information forgery
    │  - Manipulating user decisions
    │  - Deliberately hiding important information
    │  → VIOLATION: approved=false, weighted_score=0.0
    ▼
[2] Model-based Scoring (Ollama, temperature=0.1)
    │  Scores each law 0.0–1.0 via structured JSON prompt
    │  Cached in TTLCache (5-min TTL, 100-entry max)
    ▼
[3] Weighted Score Calculation
    │  weighted_score = Σ(score[law] × weight[law])
    │  Threshold: approved if weighted_score ≥ 0.3
    ▼
[4] Fairness Correction (if fairness < 0.3)
    │  _correct_response(): rephrase to improve fairness
    │  Returns modified_response alongside original scores
```

### Override

Law weights are configurable via `config["law_weights"]` — allowing domain-specific tuning (e.g., higher survival weight in medical contexts).

---

## 7. Memory Architecture

**File**: `backend/adam/memory/system.py`

```
┌─────────────────────────────────────────────────────────────┐
│                     MemorySystem                             │
│                                                              │
│  ┌─────────────┐    ┌──────────────────────────────────┐    │
│  │ Short-term  │    │       Qdrant Vector DB            │    │
│  │ (in-memory) │    │       (:6333, Cosine, 768d)       │    │
│  │ Last 50     │    │                                    │    │
│  │ messages    │    │  Collections:                      │    │
│  └─────────────┘    │  ┌──────────────────────────┐     │    │
│                      │  │ adam_knowledge           │     │    │
│  ┌─────────────┐    │  │ adam_conversations       │     │    │
│  │  Episodic   │    │  │ adam_patterns             │     │    │
│  │ (in-memory) │    │  │ adam_reasoning_patterns   │     │    │
│  │ Key events  │    │  │ adam_summaries            │     │    │
│  │ + context   │    │  │ adam_connections          │     │    │
│  └─────────────┘    │  └──────────────────────────┘     │    │
│                      │                                    │    │
│  ┌─────────────┐    │  Embedding: nomic-embed-text      │    │
│  │ Embed Cache │    │  (via Ollama :11434)              │    │
│  │ TTL=600s    │    │                                    │    │
│  │ Max=200     │    │  Search Cache: TTL=120s, Max=100   │    │
│  └─────────────┘    └──────────────────────────────────┘    │
│                                                              │
│  ┌──────────────────────────────────────────────────────┐   │
│  │  ChatStore (Dual SQLite)                             │   │
│  │  - conversations.db: full chat history               │   │
│  │  - sessions.db: session metadata                     │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### Three-Tier Memory Model

1. **Short-term** (`self.short_term`): Last 50 messages in-memory, fast access, no persistence
2. **Long-term** (Qdrant): Semantic vector search across 6 collections, persisted across restarts
3. **Episodic** (`self.episodes`): Important events with context and importance scores, in-memory

### RAG Collection Routing

The context builder (`_build_context`) performs intelligent routing based on intent and keywords:

| Keywords/Intent | Collection | Purpose |
|----------------|------------|---------|
| General | `project_architecture` | Overall project structure |
| Always | `user_profile` | User preferences and style |
| Always | `conversation_memory` | Past conversation lessons |
| "frontend", "react", "next" | `frontend_components` | Frontend-specific knowledge |
| "backend", "engine", "api" | `backend_modules` | Backend-specific knowledge |
| "tool", "execute", "browser" | `tools_docs` | Tool documentation |
| "security", "hack", "cve" | `security_guard` | Security knowledge |
| "docker", "deploy", "nginx" | `deployment_infra` | Deployment knowledge |
| Fallback | `project_architecture` | When no specific match found |

### Embedding Pipeline

```
Text → Ollama /api/embeddings (nomic-embed-text) → 768-dim vector
      ↓ (cached in TTLCache, key=sha256(text), TTL=600s)
Qdrant upsert → collection/points (with metadata + timestamp)
```

Search uses cosine similarity with configurable `score_threshold` (default: 0.5) and `top_k` (default: 3-5).

---

## 8. Provider Fallback Chain

**File**: `backend/adam/providers/manager.py`

```
┌───────────────────────────────────────────────────┐
│                ProviderManager                     │
│                                                    │
│  fallback_order: ["ollama", "openai", "anthropic"] │
│                                                    │
│  ┌─────────┐  ┌──────────┐  ┌────────────┐       │
│  │ Ollama  │──▶│  OpenAI  │──▶│ Anthropic  │       │
│  │ (local) │  │  (cloud)  │  │  (cloud)   │       │
│  └─────────┘  └──────────┘  └────────────┘       │
│                                                    │
│  CircuitBreaker per provider:                      │
│  - failure_threshold=5                             │
│  - recovery_timeout=30s                           │
└───────────────────────────────────────────────────┘
```

### Auto-Fallback Logic

```python
async def chat(messages):
    # 1. Try current provider
    try:
        return await self.current.chat(messages)
    except Exception:
        errors.append(f"{self.mode}: failed")

    # 2. Try remaining providers in order
    for name, provider in self._providers.items():
        if name == self.mode:
            continue
        try:
            return await provider.chat(messages)
        except Exception:
            errors.append(f"{name}: failed")

    # 3. All failed
    return ""
```

### Provider Interface

All providers implement `BaseProvider`:

| Method | Description |
|--------|-------------|
| `chat(messages)` | Multi-turn chat completion |
| `generate(prompt, system)` | Single-turn generation |
| `chat_stream(messages)` | Streaming chat (async generator) |

### LoRA Server

In addition to the three providers, a dedicated LoRA inference server (Flask, `:7860`) can be activated via `set_inference_mode("lora")`. The engine then calls `_call_lora_server()` with manual retry (3 attempts, exponential backoff).

---

## 9. Channel System

**Files**: `backend/adam/channels/manager.py`, `base.py`, `telegram.py`, `whatsapp.py`, `bulk.py`

### Auto-Discovery Architecture

```
┌────────────────────────────────────────────┐
│            ChannelManager                   │
│                                             │
│  discover_channels()                        │
│    ├── import telegram, whatsapp modules    │
│    │   └── scan for BaseChannel subclasses  │
│    └── import bulk.BULK_CHANNELS            │
│        └── 25+ lightweight adapters         │
│                                             │
│  start_all(engine)                          │
│    ├── Check config["channels"][name]       │
│    ├── Validate required credentials        │
│    ├── Instantiate + attach engine          │
│    └── Register webhook routes if needed    │
│                                             │
│  start_polling_all()                        │
│    └── asyncio.create_task for each         │
└────────────────────────────────────────────┘
```

### Channel Types

| Type | Mechanism | Examples |
|------|-----------|---------|
| **Polling** | Long-poll / WebSocket loop | Telegram, Discord |
| **Webhook** | HTTP POST receiver | WhatsApp, Slack, Teams |
| **Hybrid** | Both polling + webhooks | Discord |

### Available Channels (25+)

**Full implementations**: Telegram, WhatsApp

**Bulk adapters** (lightweight, `bulk.py`):
Discord, Slack, Microsoft Teams, LinkedIn, Twitter/X, Instagram, Facebook Messenger, WeChat, Line, Viber, Signal, SMS (Twilio), Email (SMTP/IMAP), IRC, Matrix, Google Chat, GitHub, GitLab, Jira, Notion, Salesforce, HubSpot, Zendesk, Custom Webhook

### BaseChannel Interface

Every channel implements:

| Method/Property | Purpose |
|----------------|---------|
| `name: str` | Channel identifier |
| `requires: List[str]` | Required config keys (e.g., `["bot_token"]`) |
| `is_polling: bool` | Whether this channel uses polling |
| `is_webhook: bool` | Whether this channel receives webhooks |
| `is_available(config)` | Check if credentials are present |
| `validate_config(config)` | Return missing required keys |
| `attach_engine(engine)` | Connect to the AdamPrismEngine |
| `start_polling()` | Begin polling loop (async) |
| `stop()` | Graceful shutdown |
| `get_status()` | Channel health/status |
| `get_webhook_routes()` | FastAPI routes to register |

---

## 10. Tool System

**Files**: `backend/adam/tools/manager.py`, `computer.py`, `mcp.py` + `backend/adam/engine/tools/`

### Architecture

```
┌──────────────────────────────────────────────────────────────┐
│                      Tool Execution                          │
│                                                              │
│  Model Output: <|tool_call|>call:tool_name{params}<|...|>   │
│      │                                                       │
│      ▼                                                       │
│  _parse_tool_request() — 3 parsing strategies:               │
│    1. XML-style: <function=name><parameter=key>val</...>     │
│    2. Compact: call:name{json}                               │
│    3. JSON fallback: {"_tool": "...", "params": {...}}       │
│      │                                                       │
│      ▼                                                       │
│  _tool_check_permissions()                                   │
│    ├── SecurityOrchestrator.check_tool_call()                │
│    ├── classify_tool() → PermissionState                     │
│    └── PluginManager.run_before_tool()                       │
│      │                                                       │
│      ▼                                                       │
│  _execute_tool() — dispatch to handler:                      │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │   Browser    │  │   Computer   │  │     MCP      │       │
│  │  (6 tools)   │  │  (14 tools)  │  │ (70+ tools)  │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐       │
│  │    File      │  │    Shell     │  │   Memory     │       │
│  │  (4 tools)   │  │  (2 tools)   │  │  (3 tools)   │       │
│  └──────────────┘  └──────────────┘  └──────────────┘       │
│  ┌──────────────┐  ┌──────────────┐                          │
│  │  Knowledge   │  │   Planning   │                          │
│  │  (1 tool)    │  │  (1 tool)    │                          │
│  └──────────────┘  └──────────────┘                          │
│                                                              │
│  PluginManager.run_after_tool()                              │
└──────────────────────────────────────────────────────────────┘
```

### Built-in Tools (30+)

| Category | Tools | Max Calls/Session |
|----------|-------|-------------------|
| **Browser** | browser_open, browser_fetch, browser_click, browser_type, browser_read, screenshot | 20-50 |
| **Mouse** | mouse_click, mouse_move, mouse_scroll, mouse_drag, mouse_position | 20-100 |
| **Keyboard** | keyboard_type, keyboard_press, keyboard_hotkey | 30-50 |
| **Clipboard** | clipboard_read, clipboard_write | 20 |
| **Screen** | screen_info, screen_ocr, window_focus, window_list | 20-30 |
| **File** | file_read, file_write (requires confirmation), file_download, disk_space | 10-50 |
| **Knowledge** | search_knowledge | 50 |
| **Shell** | shell, python_exec | 20 |
| **Memory** | memory_store, memory_recall, memory_reflect | 20-50 |
| **Planning** | tool_planning | 50 |
| **Notebook** | notebook_update_profile | 20 |
| **Permissions** | request_permission, check_preferences | 20 |
| **Scrapling** | scrapling_browser, scrapling_search, scrapling_monitor, scrapling_extract | 10-30 |

### MCP Integration (70+ External Tools)

**File**: `backend/adam/tools/mcp.py`

The MCP Manager connects to external tool servers via the Model Context Protocol (stdio transport):

- **Connection**: `MCPConnection` — manages stdio subprocess + `ClientSession`
- **Auto-discovery**: On connect, calls `session.list_tools()` to discover available tools
- **Tool map**: `self._tool_map[tool_name] → connection_name` for routing
- **Security**: Command whitelist (`npx`, `node`, `python3`, `python`, `uvx`), max 10 servers
- **Lifecycle**: `AsyncExitStack` ensures clean subprocess termination

---

## 11. Learning Pipeline

**File**: `backend/adam/learning/learner.py`

The ContinuousLearner runs **asynchronously in the background** after every chat interaction:

```
User Message + Response
         │
         ▼
┌────────────────────┐
│ Phase 1: Reflection │
│  - Auto-evaluate    │
│  - Check quality    │
│  - Score: 0.0-1.0  │
└────────┬───────────┘
         │
         ▼
┌──────────────────────────┐
│ Phase 2: Knowledge Extract│
│  - Detect code blocks    │
│  - Detect procedures     │
│  - Store in knowledge DB │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Phase 3: Skill Generation│
│  - Only for good quality │
│  - JSON frontmatter + MD │
│  - Saved to data/learning│
│    /generated_skills/    │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Phase 4: Reinforcement   │
│  - Record user feedback  │
│  - Track success/failure │
│  - Influence future      │
│    decisions             │
└──────────────────────────┘
```

### Auto-Evaluation Criteria

| Check | Penalty | Issue |
|-------|---------|-------|
| Response < 5 chars | 0.25 | `short_response` |
| Response > 2000 chars | 0.25 | `verbose` |
| Contains "أنا مش عارف", "sorry", "I don't know" | 0.25 | `uncertainty` |
| No issues found | 0 | `good` |

Quality score = `1.0 - (issues_count × 0.25)`

### Data Storage

- `data/learning/reflections.json` — last 500 reflection records
- `data/learning/knowledge.json` — extracted knowledge items
- `data/learning/generated_skills.json` — skill generation records
- `data/learning/reinforcement.json` — user feedback records
- `data/learning/generated_skills/auto-*.md` — auto-generated skill files

---

## 12. Subagent System

**Files**: `backend/adam/subagents/manager.py`, `session.py`, `teams.py`

### Architecture

```
┌────────────────────────────────────────────────────────┐
│                  SubagentManager                        │
│                                                         │
│  MAX_SUBAGENTS = 10 (env: ADAM_MAX_SUBAGENTS)          │
│  IDLE_TIMEOUT = 3600s (env: ADAM_SUBAGENT_IDLE_TIMEOUT)│
│                                                         │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │  Session A  │  │  Session B  │  │  Session C  │    │
│  │  (isolated) │  │  (isolated) │  │  (isolated) │    │
│  └─────────────┘  └─────────────┘  └─────────────┘    │
│                                                         │
│  ┌──────────────────────────────────────────────────┐  │
│  │               TeamManager                        │  │
│  │  ┌────────────────────────────────────────────┐  │  │
│  │  │  SubagentTeam "code-team"                  │  │  │
│  │  │  ├── researcher → system_prompt + tools    │  │  │
│  │  │  ├── coder → system_prompt + tools         │  │  │
│  │  │  └── reviewer → system_prompt + tools      │  │  │
│  │  │                                            │  │  │
│  │  │  run(task, parallel=False):                │  │  │
│  │  │    Sequential: agent N sees N-1 output     │  │  │
│  │  │    Parallel: all agents work independently │  │  │
│  │  └────────────────────────────────────────────┘  │  │
│  └──────────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────────┘
```

### Security Constraints

| Constraint | Value | Purpose |
|-----------|-------|---------|
| Max concurrent subagents | 10 | Resource limit |
| Name length | 1-50 chars | Prevent abuse |
| Blocked names | admin, root, system, adam, sudo, daemon | Prevent privilege escalation |
| Unique names | Enforced | Prevent confusion |
| Idle cleanup | 3600s | Automatic resource reclamation |

### Team Execution Modes

1. **Sequential** (default): Each agent receives the cumulative output of all previous agents — ideal for pipeline workflows (research → code → review)
2. **Parallel**: All agents work independently on the same task — ideal for diverse perspectives or independent subtasks

---

## 13. Skills System

**Files**: `backend/adam/skills/manager.py`, `base.py`, `builtin/`

### Skill Format (JSON Frontmatter + Markdown)

```markdown
---
{"name": "explain-code", "description": "Explains code step by step", "version": "1.0.0", "triggers": ["explain", "شرح الكود"]}
---

# Explain Code Skill

When the user asks to explain code:
1. Read the code carefully
2. Break it into logical sections
3. Explain each section with examples
4. Highlight important patterns and trade-offs
```

### 5 Built-in Skills

| Skill | File | Trigger Keywords |
|-------|------|-----------------|
| explain-code | `builtin/explain-code.md` | "explain", "شرح الكود" |
| write-test | `builtin/write-test.md` | "test", "اختبار" |
| git-commit | `builtin/git-commit.md` | "commit", "كوميت" |
| code-review | `builtin/code-review.md` | "review", "مراجعة" |
| debug | `builtin/debug.md` | "debug", "خطأ" |

### Skill Lifecycle

1. **Discovery**: `SkillManager.discover()` scans `builtin/` and `~/.adam/skills/`
2. **Loading**: `Skill.from_markdown()` parses frontmatter + body; Python skills use class inspection
3. **Matching**: `SkillManager.match(message)` checks trigger keywords against user message
4. **Activation**: `Skill.on_trigger()` returns custom instructions injected into context
5. **Cleanup**: `Skill.on_unload()` for graceful teardown

---

## 14. Plugin System

**Files**: `backend/adam/plugins/manager.py`, `base.py`

### Hook Points

```
┌───────────────────────────────────────────────────────────┐
│                     PluginManager                          │
│                                                            │
│  Hooks (ordered by _hook_order):                           │
│                                                            │
│  ┌─────────────────────┐    ┌──────────────────────────┐  │
│  │ run_before_generate │───▶│ Modify message + context  │  │
│  │                     │    │ before LLM call           │  │
│  └─────────────────────┘    └──────────────────────────┘  │
│                                                            │
│  ┌────────────────────┐     ┌──────────────────────────┐  │
│  │ run_after_generate │────▶│ Modify response after     │  │
│  │                    │     │ LLM call                  │  │
│  └────────────────────┘     └──────────────────────────┘  │
│                                                            │
│  ┌────────────────────┐     ┌──────────────────────────┐  │
│  │ run_before_tool    │────▶│ Approve/modify/reject     │  │
│  │                    │     │ tool execution (None=block)│  │
│  └────────────────────┘     └──────────────────────────┘  │
│                                                            │
│  ┌────────────────────┐     ┌──────────────────────────┐  │
│  │ run_after_tool     │────▶│ Modify tool result        │  │
│  │                    │     │ after execution           │  │
│  └────────────────────┘     └──────────────────────────┘  │
└───────────────────────────────────────────────────────────┘
```

### Plugin Loading

- **From directory**: Scans for `.py` files and `__init__.py` packages, imports, finds `AdamPlugin` subclasses
- **From class**: Direct registration via `load_plugin(MyPluginClass)`
- **Error isolation**: Plugin hook failures are caught and logged — never crash the main pipeline

### AdamPlugin Interface

```python
class AdamPlugin:
    name: str
    version: str
    description: str

    async def on_load(self): ...
    async def on_unload(self): ...
    async def before_generate(self, message, context) -> Optional[dict]: ...
    async def after_generate(self, message, response) -> Optional[str]: ...
    async def before_tool(self, action) -> Optional[dict]: ...  # None = block
    async def after_tool(self, action, result) -> Optional[dict]: ...
```

---

## 15. Frontend & Desktop

### Web UI (`frontend/web/`)

| Technology | Version | Purpose |
|-----------|---------|---------|
| Next.js | 16 | React framework with SSR |
| Tailwind CSS | v4 | Utility-first styling |
| shadcn/ui | latest | Accessible component library |
| Zustand | latest | Client state management |

Connects to the FastAPI backend via REST API (`:8000`) and WebSocket for streaming.

### Desktop App (`frontend/desktop-app/`)

| Technology | Version | Purpose |
|-----------|---------|---------|
| Electron | 33 | Cross-platform desktop wrapper |
| Node.js | latest | Main process runtime |

Wraps the Web UI in an Electron shell for native desktop integration.

### VS Code Extension (`frontend/vscode-extension/`)

- TypeScript-based extension
- Provides chat panel within VS Code
- Communicates with the API server via HTTP/WebSocket
- Custom icon and sidebar integration

### Python SDK (`clients/python-sdk/`)

- `adam_prism_client/client.py` — Main client class
- `adam_prism_client/models.py` — Request/response models
- `adam_prism_client/errors.py` — Custom exceptions

---

## 16. Deployment

### Docker Compose (8 Services)

**File**: `deploy/docker-compose.yml`

```
┌─────────────────────────────────────────────────────────────┐
│                    Docker Network: adam_net                   │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │   Qdrant   │  │   Ollama   │  │   API (FastAPI)    │    │
│  │   :6333    │  │  :11434    │  │   :8000            │    │
│  │  Vector DB │  │  LLM Host  │  │  65+ routes        │    │
│  │            │  │  + GPU     │  │  + WebSocket       │    │
│  └────────────┘  └────────────┘  └────────────────────┘    │
│                                                              │
│  ┌────────────┐  ┌────────────┐  ┌────────────────────┐    │
│  │  Telegram  │  │   Web UI   │  │      Nginx         │    │
│  │    Bot     │  │  :3000     │  │   :80, :443        │    │
│  │            │  │  Next.js   │  │   Reverse Proxy    │    │
│  └────────────┘  └────────────┘  └────────────────────┘    │
│                                                              │
│  ┌────────────────────┐  ┌────────────────────────────┐     │
│  │   Prometheus       │  │      Grafana              │     │
│  │   :9090            │  │      :3001                │     │
│  │   Metrics          │  │      Dashboards           │     │
│  └────────────────────┘  └────────────────────────────┘     │
│                                                              │
│  Volumes: qdrant_storage, qdrant_snapshots, ollama_models,  │
│           api_data, api_logs, nginx_logs,                    │
│           prometheus_data, grafana_data                      │
└─────────────────────────────────────────────────────────────┘
```

### Service Dependencies

```
Nginx → API, Web
Web → API
API → Qdrant, Ollama
Telegram Bot → API, Qdrant, Ollama
Grafana → Prometheus
Prometheus → API
```

### Health Checks

- **API**: `curl -f http://localhost:8000/` every 30s
- **Web**: `wget --spider http://localhost:3000/` every 30s
- **Engine Watchdog**: Internal async loop checking all subsystems every 60s with auto-healing

---

## 17. Key Design Decisions & Rationale

### 1. Protocol, Not a Model

Adam Prism is deliberately model-agnostic. The `ProviderManager` with its fallback chain means you can run entirely local (Ollama), entirely cloud (OpenAI/Anthropic), or hybrid. The protocol — the 8-phase chat cycle, security layers, ethics gate, tool execution — is the value, not any specific model.

**Rationale**: Built from real projects in petroleum, pharma, and legal sectors where data sovereignty is non-negotiable. The system must work with any LLM, including air-gapped ones.

### 2. Mixin-Based Engine

The 6-layer mixin chain (`Base → Utils → Context → Generate → Tools → Chat`) was chosen over a monolithic class or a plugin-based architecture because:

- Each layer has a single responsibility and can be understood in isolation
- New functionality (e.g., a new tool category) is added by inserting a mixin
- No diamond problem — it's a linear chain
- All mixins share state through `self`, avoiding complex dependency injection

### 3. Stub-First Initialization

`_init_stubs()` creates no-op objects for every subsystem before `_init_real_modules()` attempts to connect. This means:

- The engine **always starts**, even if Qdrant is down or Ollama isn't installed
- Subsystems can be attached later via `engine.attach("memory", real_memory)`
- The watchdog can heal failed subsystems by re-initializing them

### 4. Keyword-Based Intent Classification

`_quick_classify_intent()` uses keyword matching instead of LLM-based classification because:

- **Zero latency**: No additional API call
- **Zero cost**: No token consumption
- **Deterministic**: Same input → same classification
- **Bilingual**: Arabic + English keywords
- **Good enough**: For 7 modes, keyword matching achieves sufficient accuracy; the model can refine within its response

### 5. <|tool_call|> Format for Tool Invocation

Tools are invoked through structured text markers (`<|tool_call|>call:name{params}<|tool_call|>`) rather than a separate API because:

- Works with any model that can follow formatting instructions
- No dependency on OpenAI-style function calling
- Model-driven: the model decides when to use tools, not heuristics
- Previously used auto-tool injection (keyword-based heuristic) which was removed because it caused unintended executions

### 6. Defense-in-Depth Security

Five separate security layers rather than one monolithic check because:

- **InputGuard** is fast (regex) and catches 80% of attacks before any LLM call
- **ToolPermissionValidator** prevents resource abuse even if the model is compromised
- **OutputGuard** catches what the model might leak despite input filtering
- **Path sanitization** protects the filesystem regardless of tool calls
- **MCP command whitelist** prevents arbitrary code execution via MCP servers

Each layer independently could be bypassed, but together they create a robust barrier.

### 7. Ethics as a Gate, Not a Filter

The EthicsGate doesn't just block bad outputs — it attempts to **correct** them (Phase 4: `_correct_response`). This is because:

- In educational contexts, a blocked response is worse than a corrected one
- The 4-law system provides nuance (fairness is weighted 4× more than creativity)
- Absolute prohibitions are handled separately from model-based evaluation
- Configurable weights allow domain-specific tuning without code changes

### 8. Local-First, Sovereignty by Design

Every component can run locally:

- **Ollama** for LLM inference (no data leaves the machine)
- **Qdrant** for vector storage (all knowledge stays local)
- **Nomic embeddings** via Ollama (no external embedding API)
- **SQLite** for chat history (no cloud database)
- **File-based** skill and plugin storage (no marketplace dependency)

Cloud providers (OpenAI, Anthropic) are **optional fallbacks**, never requirements.

### 9. Modular Isolation — Every Component Can Be Disabled

Each subsystem (memory, ethics, security, tools, channels, plugins, subagents, learning) can be independently disabled:

- Stubs provide safe no-op behavior when a module is missing
- `_init_real_modules()` uses try/except for each module — failure doesn't cascade
- `config["channels"][name].enabled = false` disables individual channels
- `config["discord_enabled"] = false` keeps Discord off by default
- Plugins are loaded from directory — empty directory = no plugins

### 10. Self-Healing with Automatic Health Checks

The `start_watchdog()` loop (every 60s):

1. Checks each subsystem for `None` (failed init)
2. Attempts `_heal_failed_subsystem()` which re-initializes the module
3. Checks browser health via `is_healthy()` and restarts if needed
4. Runs `gc.collect()` every 5 cycles to prevent memory leaks

This ensures long-running production deployments remain stable without manual intervention.

---

## Statistics

| Metric | Value |
|--------|-------|
| API Routes | 65+ |
| Tests | 259+ passing |
| Built-in Tools | 30+ |
| MCP External Tools | 70+ (via MCP host) |
| Communication Channels | 25+ |
| Qdrant Collections | 6 |
| Cognitive Modes | 7 |
| Ethical Laws | 4 |
| Security Layers | 5 |
| Engine Mixin Layers | 6 |
| Concurrent Subagents | 10 max |
| License | Apache 2.0 |

---

*This document reflects the architecture as of the current codebase. For implementation details, refer to the inline documentation in each module.*
