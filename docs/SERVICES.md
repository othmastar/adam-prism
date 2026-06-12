# Adam Prism — Service Reference & Run Guide

## Quick Start (30 seconds)

```bash
# Option A: Full Docker stack (recommended)
cd deploy && docker compose up -d

# Option B: Bare metal
pip install -e .
python main.py --port 8000

# Option C: One-line setup
bash scripts/setup.sh
```

---

## 1. Core Backend

### API Server
| | |
---|---
**Description** | FastAPI server with 65+ routes — chat, memory, tools, channels, subagents, plugins, webhooks, voice, skills, scheduler, security
**Port** | `8000`
**Start** | `python main.py --port 8000` or `adam-prism`
**Depends on** | Ollama, Qdrant
**Docker** | `deploy/docker-compose.yml` → `api` service
**Routes** | `/api/chat`, `/api/knowledge/*`, `/api/memory/*`, `/api/tools/*`, `/api/voice/*`, `/webhook/*`, `/ws/chat`, `/api/engine/*`, `/api/subagents/*`, `/api/channels/*`, `/api/skills/*`, `/api/plugins/*`, `/api/scheduler/*`

### Ollama (LLM)
| | |
---|---
**Description** | Local LLM inference server — runs Gemma 4, Qwen, or any GGUF model
**Port** | `11434`
**Start** | `ollama serve` or Docker: `ollama/ollama:latest`
**Models** | `adam-prism-v13:latest` (default), `nomic-embed-text` (embeddings)
**Config** | `OLLAMA_BASE` env or `ollama_base` in config

### Qdrant (Vector Database)
| | |
---|---
**Description** | Persistent long-term memory — stores conversation embeddings for semantic recall
**Port** | `6333` (HTTP), `6334` (gRPC)
**Start** | `docker run -d -p 6333:6333 qdrant/qdrant` or Docker Compose
**Config** | `QDRANT_URL` env or `qdrant_url` in config
**Collections** | `adam_journal`, `adam_knowledge`, conversation memory

### LoRA Inference Server (Optional)
| | |
---|---
**Description** | Fine-tuned Gemma 4 E4B inference with LoRA weights — Egyptian Arabic specialized
**Port** | `8080` or `7861`
**Start** | `python scripts/inference_server.py`
**Depends on** | GPU (NVIDIA), `checkpoints/` LoRA adapter
**Docker** | `deploy/Dockerfile.inference` (not in compose by default)
**API** | `/chat`, `/health`, `/tools/execute`, `/subagents/chat`

---

## 2. Channels (Communication)

### Telegram Bot
| | |
---|---
**Type** | Long-polling or webhook
**Start** | `BOT_MODE=telegram python deploy/bot_entrypoint.py`
**Config** | `TELEGRAM_BOT_TOKEN` env
**Docker** | `telegram-bot` service in docker-compose

### WhatsApp
| | |
---|---
**Type** | Webhook (Meta API)
**Start** | Built into API server — auto-mounted at `/webhook/whatsapp`
**Config** | `WHATSAPP_PHONE_NUMBER_ID`, `WHATSAPP_ACCESS_TOKEN` env
**Verify** | GET `/webhook/whatsapp?hub.mode=subscribe&hub.verify_token=...`

### All Channels (25 total)
| Channel | Type | Config Key | Start Method |
|---------|------|------------|-------------|
| **Discord** | Polling + Webhook | `DISCORD_TOKEN` | Via ChannelManager |
| **Slack** | Webhook | `SLACK_BOT_TOKEN` | Via ChannelManager |
| **Email** | IMAP Polling | `EMAIL_HOST`, `EMAIL_USER`, `EMAIL_PASS` | Via ChannelManager |
| **SMS/Twilio** | Outgoing + Webhook | `TWILIO_ACCOUNT_SID`, `TWILIO_AUTH_TOKEN` | Via ChannelManager |
| **Facebook** | Webhook | `FACEBOOK_PAGE_ACCESS_TOKEN` | Via ChannelManager |
| **Twitter** | Polling | `TWITTER_BEARER_TOKEN` | Via ChannelManager |
| **Matrix** | Polling | `MATRIX_HOMESERVER`, `MATRIX_ACCESS_TOKEN` | Via ChannelManager |
| **Signal** | CLI Polling | `SIGNAL_CLI_PATH` | Via ChannelManager |
| **Instagram** | Polling | `INSTAGRAM_USERNAME`, `INSTAGRAM_PASSWORD` | Via ChannelManager |
| **LINE** | Webhook | `LINE_CHANNEL_ACCESS_TOKEN` | Via ChannelManager |
| **Viber** | Webhook | `VIBER_AUTH_TOKEN` | Via ChannelManager |
| **Teams** | Webhook | `TEAMS_WEBHOOK_URL` | Via ChannelManager |
| **Google Chat** | Webhook | `GOOGLE_CHAT_WEBHOOK_URL` | Via ChannelManager |
| **IRC** | Polling | `IRC_SERVER`, `IRC_NICK` | Via ChannelManager |
| **XMPP** | Polling | `XMPP_JID`, `XMPP_PASSWORD` | Via ChannelManager |
| **Generic Webhook** | Webhook | — (optional secret) | Auto-mounted |
| **RSS** | Polling | `RSS_FEEDS` | Via ChannelManager |
| **Notion** | Polling | `NOTION_API_KEY` | Via ChannelManager |
| **GitHub** | Polling | `GITHUB_TOKEN` | Via ChannelManager |
| **WeChat** | Polling | `WECHAT_CORP_ID`, `WECHAT_CORP_SECRET` | Via ChannelManager |
| **WebChat** | Embedded | — | Built into API at `/chat/widget` |

Channels auto-start via `ChannelManager.start_all()` when configured.

---

## 3. Frontend

### Web UI
| | |
---|---
**Stack** | Next.js 16, Tailwind v4, shadcn/ui, Zustand, React 19, TypeScript 5
**Port** | `3000`
**Start (dev)** | `cd frontend/web-ui && npm run dev`
**Start (prod)** | `npm run build && npm run start`
**Docker** | `web` service in docker-compose
**Features** | Dark/light theme, Arabic/English RTL, voice chat, chat history, skills UI

### Desktop App (Electron)
| | |
---|---
**Stack** | Electron 33, preload.js security model
**Start** | `cd frontend/desktop-app && npm start`
**Build Linux** | `npm run build:linux` → AppImage
**Build macOS** | `npm run build:mac` → DMG
**Build Windows** | `npm run build:win` → NSIS installer

### VS Code Extension
| | |
---|---
**Commands** | `adam-prism.chat`, `adam-prism.explainCode`, `adam-prism.reviewCode`, `adam-prism.debugCode`, `adam-prism.writeTest`, `adam-prism.askAboutFile`
**Keybindings** | `ctrl+alt+a` (chat), `ctrl+alt+e` (explain)
**Start** | `cd frontend/vscode-extension && npm run compile`
**Install** | Via VSIX or VS Code Marketplace

---

## 4. Infrastructure

### Nginx
| | |
---|---
**Port** | `80`, `443`
**Routes** | `/api/*` → API:8000, `/` → Web:3000, `/webhook/*` → API:8000, `/ws/*` → API:8000
**Config** | `deploy/nginx.conf`
**Docker** | `nginx:alpine` in docker-compose

### Prometheus
| | |
---|---
**Port** | `9090`
**Docker** | `prom/prometheus:latest`
**Purpose** | Metrics collection from API server

### Grafana
| | |
---|---
**Port** | `3001`
**Docker** | `grafana/grafana:latest`
**Purpose** | Dashboard visualization from Prometheus
**Credentials** | admin / `${GF_SECURITY_ADMIN_PASSWORD}` (set in `.env`)

---

## 5. CLI & Scripts

### CLI Commands
| Command | Description |
|---------|-------------|
| `adam` | Start API server |
| `adam-prism` | Same as `adam` |
| `python -m adam` | Same as above |
| `python main.py --port 8000` | Start with custom port |
| `python run_api.py` | Start via runner script |

### Setup & Management
| Script | Description |
|--------|-------------|
| `bash scripts/setup.sh` | One-line setup — checks deps, creates venv, pulls models, starts Qdrant |
| `bash start.sh` | Start LoRA + API + Frontend sequentially |
| `bash stop.sh` | Kill all services on ports 3000, 8002, 8080 |
| `python scripts/health_monitor.py` | Daemon — monitors Qdrant, Ollama, API, LoRA; auto-restarts on failure |
| `python scripts/inference_server.py` | Start LoRA inference server (GPU) |
| `python scripts/train_lora.py` | QLoRA fine-tuning on training data |
| `python scripts/merge_lora.py` | Merge LoRA adapter into base model |
| `python scripts/ingest_knowledge.py` | Ingest documents into Qdrant knowledge base |

### Docker Management
| Command | Description |
|---------|-------------|
| `cd deploy && docker compose up -d` | Start full stack |
| `docker compose up -d api` | Start only API + dependencies |
| `docker compose up -d telegram-bot` | Start only Telegram bot |
| `docker compose logs -f api` | Tail API logs |
| `docker compose down` | Stop everything |

---

## 6. Environment Variables

Copy `.env.example` → `.env` and configure:

```bash
cp .env.example .env
# Generate strong keys:
python3 -c "import secrets; print('ADAM_API_KEY=' + secrets.token_urlsafe(32))"
python3 -c "import secrets; print('ADAM_ADMIN_KEY=' + secrets.token_urlsafe(32))"
```

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `ADAM_API_KEY` | Production | `adam-prism-change-me` | API authentication key |
| `ADAM_ADMIN_KEY` | Production | (empty) | Admin key for MCP/privileged ops |
| `ADAM_PRODUCTION` | No | `0` | Enable production security mode |
| `ADAM_RATE_LIMIT` | No | `60` | Max requests/minute per IP |
| `ADAM_MAX_REQUEST_SIZE` | No | `10485760` | Max request body (bytes) |
| `ADAM_MAX_MCP_SERVERS` | No | `10` | Max MCP server connections |
| `ADAM_SUBAGENT_IDLE_TIMEOUT` | No | `3600` | Subagent idle timeout (seconds) |
| `INFERENCE_MODE` | No | `ollama` | LLM provider: ollama, openai, anthropic |
| `OLLAMA_BASE` | If ollama | `http://localhost:11434` | Ollama server URL |
| `QDRANT_URL` | No | `http://localhost:6333` | Qdrant vector DB URL |
| `CORS_ORIGINS` | No | `*` | Allowed CORS origins |

---

## 7. Architecture Diagram

```
                    ┌─────────────────────┐
                    │   Web UI (Next.js)  │ :3000
                    │  Desktop (Electron) │
                    │  VS Code Extension  │
                    └────────┬────────────┘
                             │ HTTP/WS
                    ┌────────▼────────────┐
                    │   Nginx (Reverse    │ :80/:443
                    │     Proxy)          │
                    └────────┬────────────┘
                             │
                    ┌────────▼────────────┐
                    │  API Server (FastAPI)│ :8000
                    │  65+ routes, 39+    │
                    │  webhooks, WebSocket │
                    └──┬──────┬───────┬───┘
                       │      │       │
              ┌────────▼─┐ ┌──▼────┐ ┌▼────────┐
              │ Ollama   │ │ Qdrant│ │ Provider │
              │ (LLM)    │ │(Vector│ │ Manager  │
              │ :11434   │ │ :6333 │ │ (OpenAI/ │
              │          │ │       │ │Anthropic)│
              └──────────┘ └───────┘ └──────────┘
                                       │
                              ┌────────▼────────┐
                              │  Channels (25)   │
                              │ TG/WA/Discord/   │
                              │ Slack/Email/...  │
                              └──────────────────┘
```

---

## 8. Service Dependency Graph

```
qdrant ──┐
         ├── api ──┬── web ──┐
ollama ──┘         │         │
                   │    nginx (front)
                   │         │
              telegram-bot ──┘
                   │
              prometheus ── grafana
```

---

## 9. Quick Test

```bash
# Verify API is running
curl http://localhost:8000/api/engine/health

# Send a chat message
curl -X POST http://localhost:8000/api/chat \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $ADAM_API_KEY" \
  -d '{"message": "قولي مرحبا يا آدم", "session_id": "test"}'

# Run test suite
pytest tests/ -k "not slow"
```
