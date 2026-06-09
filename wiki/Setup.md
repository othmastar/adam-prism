# Setup

## المتطلبات / Requirements

- Python 3.12+
- pip / pipx
- Ollama (local inference)
- Qdrant (optional, SQLite fallback)
- Playwright (for browser automation)

## Installation

### From PyPI

```bash
pip install adam-prism
```

### From Source

```bash
git clone https://github.com/othmastar/adam-prism.git
cd adam-prism
pip install -e .
```

### Install Browser for Automation

```bash
playwright install firefox
```

## Configuration

```json
{
  "inference_mode": "ollama",
  "model_name": "adam-prism-v13:latest",
  "ollama_base": "http://localhost:11434",
  "qdrant_url": "http://localhost:6333",
  "channels": {
    "telegram": { "enabled": false, "bot_token": "" },
    "whatsapp": { "enabled": false },
    "discord": { "enabled": false },
    "webchat": { "enabled": true }
  },
  "context_window": 4096,
  "token_budget": 4000,
  "max_conversation_history": 10,
  "max_tool_calls": 2,
  "tool_timeout": 15,
  "cycle_timeout": 60
}
```

## Running

### API Server

```bash
python main.py --port 8001 --mode api
```

### CLI

```bash
# Chat
adam chat "السلام عليكم"

# Interactive shell
adam shell

# List tools
adam tools
```

### Web UI

```bash
cd web-ui
npm install
npm run dev
```

## Docker

```bash
cd deploy
docker-compose up -d
```

يطلق:
- Qdrant (vector DB)
- Ollama (LLM)
- API server
- Web UI
- Telegram Bot
- Nginx (reverse proxy)

### Modal Cloud Deployment

```bash
cd deploy
python modal_deploy.py
```

## Supported Models

| Model | Size | Notes |
|-------|------|-------|
| Gemma 4 E4B | 12B | SDPA Flash Attention — 34 tok/s on RTX 3060 |
| Qwen3.5 | 4.2B | Q4_K_M — current default |
| Any Ollama model | Any | Tested with llama, mistral, qwen |

## Memory System

- **Qdrant** — vector search for semantic memory (6 collections)
- **SQLite** — fallback storage for structured data
- **Journal** — extended memory via `adam_journal` collection
- **Cache** — TTL cache for embeddings and search results

## Troubleshooting

### ImportError: No module named adam

```bash
pip install -e .
```

### Playwright not found

```bash
playwright install firefox
```

### Qdrant connection refused

SQLite fallback is automatic. No action needed.

### Ollama not available

Engine tests will be skipped. Provider tests use mocks.
