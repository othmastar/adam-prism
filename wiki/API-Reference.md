# API Reference

FastAPI server على port 8001/8002 — 39 route.

## Base URL

```
http://localhost:8001
```

## Routes

### Health

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/health` | Server status |
| `GET` | `/api/health` | Detailed health check |

### Chat

| Method | Path | Description |
|--------|------|-------------|
| `POST` | `/api/chat` | Send message, get response |
| `POST` | `/api/chat/stream` | Streaming chat via SSE |

**`POST /api/chat`**

```json
{
  "message": "السلام عليكم",
  "mode": "teacher",
  "stream": false,
  "context": {}
}
```

Response:
```json
{
  "response": "وعليكم السلام ورحمة الله وبركاته 🤍",
  "mode": "teacher",
  "cycle": 1,
  "duration_ms": 234,
  "tool_calls": 0
}
```

### Sessions

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/sessions` | List sessions |
| `POST` | `/api/sessions` | Create session |
| `GET` | `/api/sessions/{id}` | Get session |
| `DELETE` | `/api/sessions/{id}` | Delete session |
| `GET` | `/api/sessions/{id}/history` | Session history |

### Memory

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/memory` | Memory stats |
| `POST` | `/api/memory/store` | Store to memory |
| `POST` | `/api/memory/search` | Semantic search |
| `POST` | `/api/memory/recall` | Recall by ID |
| `DELETE` | `/api/memory/clear` | Clear memory |
| `GET` | `/api/memory/episodes` | Episodic memory |
| `POST` | `/api/memory/episodes` | Add episode |

### Tools

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/tools` | List all tools |
| `POST` | `/api/tools/execute` | Execute a tool |
| `GET` | `/api/tools/mcp` | List MCP tools |
| `POST` | `/api/tools/mcp/execute` | Execute MCP tool |

### Skills

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/skills` | List skills |
| `POST` | `/api/skills/load` | Load a skill |
| `POST` | `/api/skills/unload` | Unload a skill |
| `GET` | `/api/skills/{name}` | Get skill details |

### Sub-agents

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/subagents` | List sub-agents |
| `POST` | `/api/subagents` | Create sub-agent |
| `GET` | `/api/subagents/{id}` | Get sub-agent |
| `DELETE` | `/api/subagents/{id}` | Delete sub-agent |
| `POST` | `/api/subagents/{id}/chat` | Chat with sub-agent |

### Teams

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/teams` | List teams |
| `POST` | `/api/teams` | Create team |
| `GET` | `/api/teams/{id}` | Get team |
| `DELETE` | `/api/teams/{id}` | Delete team |
| `POST` | `/api/teams/{id}/run` | Run team |

### Providers

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/providers` | List providers |
| `POST` | `/api/providers/mode` | Set provider mode |

### Learning

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/learning/status` | Learning status |
| `POST` | `/api/learning/process` | Process interaction |
| `GET` | `/api/learning/stats` | Learning statistics |

### Config

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/config` | Get config |
| `POST` | `/api/config` | Update config |

## Error Format

```json
{
  "detail": {
    "error": "error_code",
    "message": "Human-readable message"
  }
}
```

HTTP Status Codes:
- `200` — Success
- `400` — Bad request
- `404` — Not found
- `500` — Internal error

## Authentication

No built-in auth (internal API).  
Put behind Nginx/Apache for production.
