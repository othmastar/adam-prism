# Adam Prism — Minimal Showcase

**This branch contains only 5 features** as proof of capability.

## What's here (5 endpoints)

| Method | Path | What it does |
|---|---|---|
| POST | `/chat` | Send a message, get a mock response |
| GET | `/healthz/live` | Liveness probe |
| GET | `/docs` | OpenAPI documentation |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/skills` | List 3 example skills |

## What you can do

```bash
# Install
pip install -e .

# Run
uvicorn adam.api.server_minimal:app --port 8000

# Chat
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "مرحبا"}'
```

## What you CANNOT do (full version only)

- Real LLM inference (this uses a mock)
- Memory / RAG / vector search
- 19 channels (Telegram, WhatsApp, etc.)
- 19+ tools
- Multi-tenant + RBAC
- WAF, webhooks, voice cloning
- Predictive monitoring
- Training data + model weights
- Real authentication
- Production observability

**For the full version, see `DISTRIBUTION.md`.**

## License

- **Code:** AGPL v3 (see `LICENSE`)
- **Commercial:** 3 tiers (see `COMMERCIAL_LICENSE.md`)
- **Rights summary:** see `RIGHTS.md`

## Verification

```bash
pytest tests/ backend/tests/test_phase7.py -q -k "not slow and not ollama"
```

The full version has 336 tests. This minimal version has fewer (subset).
