# Adam Prism — Documentation

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                       User Interface                        │
│  ┌──────────┐  ┌──────────┐  ┌─────────┐  ┌─────────────┐  │
│  │  CLI     │  │  API     │  │  Web UI │  │  Telegram    │  │
│  │ (adam)   │  │ (FastAPI)│  │ (NextJS)│  │  /WhatsApp   │  │
│  └────┬─────┘  └────┬─────┘  └────┬────┘  └──────┬──────┘  │
│       └──────────────┼──────────────┼─────────────┘         │
└──────────────────────┼──────────────────────────────────────┘
                       │
┌──────────────────────┼──────────────────────────────────────┐
│              Adam Prism Engine (core)                       │
│  ┌─────────┐ ┌──────────┐ ┌────────┐ ┌──────────────────┐  │
│  │Security │ │  Ethics  │ │Memory  │ │  Skills System    │  │
│  │ Guard   │ │  Gate    │ │(Qdrant)│ │  (SkillManager)   │  │
│  ├─────────┤ ├──────────┤ ├────────┤ ├──────────────────┤  │
│  │Provider │ │  Browser │ │ Computer│ │  Channels         │  │
│  │Manager  │ │  (Eyes)  │ │  Tools │ │  (TG/WA/MCP)      │  │
│  ├─────────┤ ├──────────┤ ├────────┤ ├────────────────┤  │
│  │Plugins  │ │  Subagents│ │ Learning│ │  Trace Recorder  │  │
│  └─────────┘ └──────────┘ └────────┘ └──────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## API Endpoints

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/` | Health check |
| `GET` | `/api/engine/health` | Engine health + status |
| `POST` | `/api/chat` | Send message → get response |
| `GET` | `/api/engine/stream` | SSE streaming chat |
| `POST` | `/api/engine/mode` | Switch inference mode |
| `POST` | `/api/memory/search` | Search memories |
| `POST` | `/api/memory/store` | Store a memory |
| `GET` | `/api/skills` | List loaded skills |
| `POST` | `/api/skills/load` | Load a skill |
| `GET` | `/api/tools` | List available tools |
| `GET` | `/api/plugins` | List loaded plugins |
| `GET` | `/api/scheduler/jobs` | List scheduled jobs |
| `POST` | `/api/subagents/run` | Run a subagent task |
| `POST` | `/webhook/whatsapp` | WhatsApp webhook (GET=verify, POST=receive) |

## Quick Start

```bash
# Install
pip install adam-prism

# Run server (requires Ollama at localhost:11434)
adam-prism --port 8000

# Or with a different provider
INFERENCE_MODE=openai OPENAI_API_KEY=sk-... adam-prism

# Docker
cd deploy && docker compose up -d
```

## Configuration

Key environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_BASE` | `http://localhost:11434` | Ollama server URL |
| `QDRANT_URL` | `http://localhost:6333` | Qdrant vector DB |
| `INFERENCE_MODE` | `ollama` | LLM provider (`ollama`, `openai`, `anthropic`) |
| `OPENAI_API_KEY` | — | OpenAI API key |
| `ANTHROPIC_API_KEY` | — | Anthropic API key |
| `OPENAI_MODEL` | `gpt-4o` | OpenAI model name |
| `ANTHROPIC_MODEL` | `claude-sonnet-4-20250514` | Anthropic model name |
| `TELEGRAM_BOT_TOKEN` | — | Telegram bot token |

## Provider Fallback

آدم يدعم auto-fallback: لو provider وقع، يجرب التاني تلقائياً.

```json
{
  "provider_fallback": ["ollama", "openai", "anthropic"],
  "inference_mode": "ollama"
}
```

لو Ollama وقع → يحول على OpenAI → لو فشل بردو → على Anthropic.

## MCP Integration

Adam Prism يتكامل مع أي MCP host (Claude Desktop, VS Code, Cursor).

شوف `docs/mcp/README.md` للتفاصيل.
