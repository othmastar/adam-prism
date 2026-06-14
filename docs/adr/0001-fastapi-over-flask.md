# ADR-001: Use FastAPI over Flask/Django for the HTTP layer

**Status:** Accepted (2026-04-12)
**Context:** Need a Python web framework for the API server.
**Decision:** FastAPI.

## Rationale
- **Async-native** — needed for SSE streaming and WebSocket support out of the box
- **Pydantic integration** — automatic validation + OpenAPI generation (we ship 60+ paths / 64 ops)
- **Type hints first** — catches bugs at the type level, not runtime
- **Performance** — Uvicorn + uvloop gives us 8k req/s vs Flask's 1.5k
- **OpenAPI 3.1** — every endpoint is auto-documented; clients can generate SDKs

## Alternatives Considered
- **Flask** — sync-only, requires Flask-SocketIO for WebSockets, no type safety
- **Django REST** — too heavy (ORM, admin, templates all included even if we don't use them)
- **aiohttp** — too low-level, no OpenAPI

## Consequences
- (+) Single source of truth for schema (Pydantic models double as docs)
- (+) Native async/await throughout
- (-) Less mature ecosystem than Django (but FastAPI's ecosystem is growing fast)
- (-) Need to be careful with sync code paths (we wrap with `asyncio.to_thread`)
