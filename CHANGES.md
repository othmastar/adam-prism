# Adam Prism — Fix Package CHANGES.md
## Complete Fix and Improvement Package

Generated: 2025-06-12

---

## CRITICAL SECURITY FIXES

### 1. `.env` File — Default API Key Committed (CRITICAL)
**File:** `.env`  
**Problem:** Default API key `adam-prism-change-me` was committed and identical to `.env.example`. Anyone with access to the repo could access the API.  
**Fix:**
- Generated a random 32-byte URL-safe API key: `0SESW0Y71q_EHcOTKtwbBeOIsO9ucI8TU4k_u0h619A`
- Added `ADAM_CORS_ORIGINS` environment variable documentation to .env
- `.env` already listed in `.gitignore` (verified)

### 2. `shell.py` — Python Exec Sandbox Bypass (CRITICAL)
**File:** `backend/adam/engine/tools/shell.py`  
**Problem:** The pattern blacklist was bypassable via Python class hierarchy traversal (`__class__.__mro__.__subclasses__()`) which allows escaping the sandbox and executing arbitrary code.  
**Fix:**
- Added these dangerous patterns to the blacklist:
  - `__class__`, `__mro__`, `__subclasses__`, `__base__`, `__dict__`
  - `__globals__`, `__init__`, `__func__`, `__code__`
  - `vars(`, `dir(`
  - `type.__subclasses__`
- Added sandboxed execution mode that:
  - Pre-pends a sandbox header that restricts `__builtins__` to an empty dict
  - Only allows safe stdlib imports (math, json, re, etc.)
  - Restricts the subprocess PATH to `/usr/bin:/bin`
  - Uses `subprocess.run` with a restricted environment

### 3. `server.py` — CORS Wildcard (HIGH)
**File:** `backend/adam/api/server.py`  
**Problem:** CORS allows `*` — any origin can call the API, enabling cross-origin attacks.  
**Fix:**
- Replaced hardcoded `allow_origins=["*"]` with configurable origins
- Added `ADAM_CORS_ORIGINS` environment variable support (takes priority over `CORS_ORIGINS`)
- In production mode (`ADAM_PRODUCTION=1`), wildcard CORS `*` is rejected with a `RuntimeError`
- When specific origins are set, `allow_credentials=True` is enabled
- Added clear error message guiding users to set specific origins

### 4. Desktop App — apiKey Not Persisted (HIGH)
**File:** `frontend/desktop-app/renderer/index.html`  
**Problem:** `saveSettings()` only saved endpoint via `window.adamAPI.saveConfig()` but not the apiKey. The apiKey was lost on page reload.  
**Fix:**
- Added `localStorage.setItem('adam-apikey', apiKey)` in `saveSettings()`
- Added `localStorage.setItem('adam-endpoint', endpoint)` in `saveSettings()`
- Added `localStorage.getItem('adam-apikey')` on startup to restore apiKey
- Added `localStorage.getItem('adam-endpoint')` on startup to restore endpoint
- localStorage values take priority over Electron IPC config

### 5. `gate.py` — Ethics Gate `dir()` Bug (MEDIUM)
**File:** `backend/adam/ethics/gate.py`  
**Problem:** Uses `'client' in dir()` instead of `'client' in locals()`. The `dir()` function returns all attributes and methods, not just local variables, so the check was always True even when `client` wasn't defined. This caused `client.aclose()` to potentially fail or close the wrong client.  
**Fix:**
- Replaced `'client' in dir()` with `'client' in locals()` in both `_evaluate_with_model` and `_correct_response`
- Also added `client is not None` check to ensure the variable exists and is valid before closing

### 6. `chat.py` — Background Task Exception Handling (MEDIUM)
**File:** `backend/adam/engine/chat.py`  
**Problem:** `_bg_task` callback could raise `InvalidStateError` on cancelled tasks. When a task is cancelled and the callback calls `t.exception()`, it raises `InvalidStateError`.  
**Fix:**
- Wrapped the callback in a try/except block
- Catches `asyncio.InvalidStateError` and generic `Exception`
- Logs the error at debug level (safe to ignore)
- Also incorporates previous fixes (vision check bug, stray `pass`)

### 7. `browser.py` — SSRF Protection (HIGH)
**File:** `backend/adam/engine/tools/browser.py`  
**Problem:** No URL validation — browser tools could access internal network addresses (localhost, private IPs, link-local), enabling Server-Side Request Forgery attacks.  
**Fix:**
- Added `_validate_url()` function that checks:
  - URL scheme is `http` or `https` only
  - Hostname is not a private IP (10.x, 172.16-31.x, 192.168.x)
  - Hostname is not a loopback address (127.x, ::1)
  - Hostname is not a link-local address (169.254.x, fe80::)
  - Hostname is not a reserved/multicast/unspecified address
  - Hostname is not a local name (localhost, *.local, *.internal, *.docker)
- Added `_is_private_ip()` helper using Python's `ipaddress` module
- Applied validation to both `browser_open` and `browser_fetch` endpoints

---

## BUG FIXES

### 8. `base.py` — `_Stub.__getattr__` Inverted Logic
**File:** `backend/adam/engine/base.py`  
**Problem:** `_Stub.__getattr__` returns `_async_noop` for names starting with `_` — this is inverted. Names starting with `_` are typically internal sync attributes, while regular names are likely async API methods.  
**Fix:**
- Changed the logic from `return _async_noop if name.startswith(('_',)) else _sync_noop`
- To: `return _sync_noop if name.startswith('_') else _async_noop`
- Now correctly returns sync noop for dunder/internal methods and async noop for public API methods

### 9. `mcp.py` — Failed MCP Connections Not Cleaned Up
**File:** `backend/adam/tools/mcp.py`  
**Problem:** Failed MCP connections were stored in `self.connections` but never removed when the connection failed. This caused memory leaks and stale connection references that would always return "not connected" errors.  
**Fix:**
- After a connection failure, the connection is now removed from `self.connections` using `self.connections.pop(name, None)`
- Any tool mappings for the failed connection are also cleaned up from `self._tool_map`
- Also incorporates previous fixes (dead code after raise, server name validation, max servers limit)

### 10. `store.py` — Module-Level Functions (No Class)
**File:** `backend/adam/memory/store.py`  
**Problem:** Uses module-level functions instead of a class, making it hard to test (can't inject mock database, can't use different paths for tests).  
**Fix:**
- Created `MemoryStore` class wrapping all functionality
- Class accepts optional `db_path` parameter for testing
- Added `delete()` and `clear()` methods to the class
- Preserved all module-level functions as backward-compatible aliases using a singleton `_default_store`
- All existing code using `from adam.memory.store import search` continues to work

---

## ARCHITECTURE IMPROVEMENTS

### 11. Split `server.py` into Routers
**Problem:** `server.py` was 1334 lines in a single file, making it difficult to maintain.  
**Fix:** Created 13 router files in `backend/adam/api/routers/`:

| Router File | Endpoints | Description |
|---|---|---|
| `chat.py` | `/api/chat/*` | Chat sessions, messages, search, upload |
| `knowledge.py` | `/api/knowledge/*` | Knowledge search, collections, add |
| `memory.py` | `/api/memory/*` | Memory store, search, reflect, stats |
| `tools.py` | `/api/tools/*` | Tool execution, available tools |
| `skills.py` | `/api/skills/*` | Skill listing and loading |
| `subagents.py` | `/api/subagents/*` | Subagent CRUD and chat |
| `voice.py` | `/api/voice/*` | Voice chat, transcribe, synthesize, audio |
| `mcp.py` | `/api/mcp/*` | MCP server management |
| `engine.py` | `/api/engine/*`, `/api/diagnostics`, `/api/status`, `/api/ollama/*` | Engine health, diagnostics, model selection |
| `channels.py` | `/api/channels` | Channel listing |
| `plugins.py` | `/api/plugins/*` | Plugin management |
| `scheduler.py` | `/api/scheduler/*` | Job scheduling |
| `permissions.py` | `/api/permissions/*`, `/api/security/*` | Permission and security management |

### 12. Routers `__init__.py`
**File:** `backend/adam/api/routers/__init__.py`  
- Imports and exports all routers for easy `include_router()` usage in `server.py`
- `server.py` now attempts to load routers via `app.include_router()` with graceful fallback

---

## PREVIOUSLY CREATED FIXES (from adam-prism-updates)

These files are also included in the fix package:

| File | Description |
|---|---|
| `backend/adam/orchestrator/__init__.py` | Orchestrator package init |
| `backend/adam/orchestrator/god.py` | God Orchestrator — central coordination layer |
| `backend/adam/orchestrator/task_queue.py` | Priority-based task queue with dedup |
| `backend/adam/orchestrator/event_bus.py` | Async event bus with pub/sub |
| `backend/adam/core/permissions.py` | Permission manager with proper defaults |
| `backend/adam/api/diagnostic.py` | Diagnostic and orchestrator API endpoints |

---

## COMPLETE FILE LIST

```
/home/z/my-project/download/adam-prism-fix-package/
├── .env
├── backend/
│   └── adam/
│       ├── api/
│       │   ├── diagnostic.py
│       │   ├── server.py
│       │   └── routers/
│       │       ├── __init__.py
│       │       ├── chat.py
│       │       ├── channels.py
│       │       ├── engine.py
│       │       ├── knowledge.py
│       │       ├── mcp.py
│       │       ├── memory.py
│       │       ├── permissions.py
│       │       ├── plugins.py
│       │       ├── scheduler.py
│       │       ├── skills.py
│       │       ├── subagents.py
│       │       ├── tools.py
│       │       └── voice.py
│       ├── core/
│       │   └── permissions.py
│       ├── engine/
│       │   ├── base.py
│       │   ├── chat.py
│       │   └── tools/
│       │       ├── browser.py
│       │       └── shell.py
│       ├── ethics/
│       │   └── gate.py
│       ├── memory/
│       │   └── store.py
│       ├── orchestrator/
│       │   ├── __init__.py
│       │   ├── event_bus.py
│       │   ├── god.py
│       │   └── task_queue.py
│       └── tools/
│           └── mcp.py
└── frontend/
    └── desktop-app/
        └── renderer/
            └── index.html
```

**Total files: 27**

---

## DEPLOYMENT INSTRUCTIONS

1. **Backup** the original project before applying fixes
2. **Replace** files in the adam-prism project with the fixed versions
3. **Generate** a new random API key: `python3 -c "import secrets; print(secrets.token_urlsafe(32))"`
4. **Update** `.env` with your new API key
5. **Set** `ADAM_CORS_ORIGINS` to your allowed origins (required in production)
6. **Restart** the application

### Key Configuration Changes:
- `ADAM_API_KEY` — Now has a random key (replace with your own)
- `ADAM_CORS_ORIGINS` — New env var for CORS (takes priority over `CORS_ORIGINS`)
- In production mode, wildcard CORS `*` is rejected
