# Adam Prism — Showcase Version

This is the **public, minimal version** of Adam Prism.

## ⚠️ This is NOT the full version

This branch contains **only 5 features** (proof of capability).
The full version with all 93 routes, training data, and model
weights is **NOT on GitHub** and is distributed privately.

See `DISTRIBUTION.md` for details on getting full access.

---

## What's here (5 endpoints only)

| Method | Path | What it does |
|---|---|---|
| POST | `/chat` | Send a message, get a mock response |
| GET | `/healthz/live` | Liveness probe |
| GET | `/docs` | OpenAPI documentation |
| GET | `/metrics` | Prometheus metrics |
| GET | `/api/skills` | List 3 example skills |

## How to run

```bash
pip install -e .
uvicorn adam.api.server_minimal:app --port 8000
# Open http://localhost:8000/  (index.html chat UI)
# Or http://localhost:8000/docs (OpenAPI)
```

## What's NOT here (full version only)

The full version has:

- ✅ Real LLM (Ollama, OpenAI, Anthropic)
- ✅ 19 channels (Telegram, WhatsApp, Discord, Slack, etc.)
- ✅ 19+ tools (browser, shell, knowledge, etc.)
- ✅ Multi-tenant + RBAC
- ✅ 4-layer memory (hot, FTS5, Qdrant, skills)
- ✅ WAF (Web Application Firewall)
- ✅ Webhooks (HMAC-SHA256 + retry)
- ✅ Voice cloning (5 Arabic dialects)
- ✅ Hybrid search (BM25 + dense)
- ✅ Predictive monitoring (CruxSight.ai)
- ✅ SSO (Google, Microsoft, GitHub, Okta, etc.)
- ✅ AI observability (token tracking, cost)
- ✅ Mobile app (React Native + Expo)
- ✅ Desktop app (Electron)
- ✅ VSCode extension
- ✅ i18n (Arabic + English)
- ✅ Helm + Kustomize + ArgoCD
- ✅ SBOM (CycloneDX)
- ✅ And more...

Plus proprietary assets:
- 🔒 2,317 real training conversations
- 🔒 1.1 GB LoRA adapter weights
- 🔒 Real tenant configurations
- 🔒 Real customer subagents

---

## Stats comparison

| Metric | Full (private) | Showcase (public) |
|---|---:|---:|
| **Files tracked** | ~802 | ~200 |
| **API routes** | 93 | 5 |
| **Tests passing** | 336 | 134 |
| **Python code (backend/adam)** | 23,686 lines | ~5,000 |
| **TypeScript/TSX** | 23,839 lines | 0 |
| **Tracked data** | ~60 MB | 0 KB |
| **Model weights** | 1.1 GB | 0 KB |

---

## License

This public version: **AGPL v3** (see `LICENSE`)

The full version: **Custom Proprietary** (see `DISTRIBUTION.md`)

For commercial use (SaaS, embedded, enterprise), see `COMMERCIAL_LICENSE.md`.

---

## How to get the full version

The full version is available to:

1. **Selected developers** (3-5 invited)
   - Sign `templates/NDA.md`
   - Receive a signed license key
   - Receive an encrypted package (AES-256-CBC)
   - See `DISTRIBUTION.md` for the full workflow

2. **Commercial customers** (companies)
   - See `COMMERCIAL_LICENSE.md` for tiers
   - Email: othman@adam-prism.local
   - Includes: training data, weights, support, SLA

3. **Researchers** (academic / non-commercial)
   - Special terms available
   - Limited to non-commercial research only
   - Email: othman@adam-prism.local

---

## What you can do with this showcase

✅ Install in 30 seconds (`pip install -e .`)
✅ See the chat UI (`frontend/index.html`)
✅ Explore the 5 endpoints
✅ Read the code (it's a real, working application)
✅ Run the tests (134 passing)
✅ Build the wheel (`python -m build`)

## What you CANNOT do with this showcase

❌ Use a real LLM (mock responses only)
❌ Use 19 channels (none enabled)
❌ Use the training data (not in this branch)
❌ Use the model weights (not in this branch)
❌ Use WAF, webhooks, voice cloning, etc.
❌ Use the full multi-tenant system
❌ Reproduce the production Adam behavior

---

## License breakdown

- **`LICENSE`** — AGPL v3 (full text, this public version)
- **`COMMERCIAL_LICENSE.md`** — 3 commercial tiers (Startup, Growth, Enterprise)
- **`RIGHTS.md`** — Plain-language summary of your rights
- **`TRADEMARKS.md`** — "Adam Prism" mark policy
- **`DISTRIBUTION.md`** — How the full version is distributed privately
- **`templates/NDA.md`** — NDA template for full version access

---

## Verification

```bash
# Run tests
pytest tests/ -q -k "not slow and not ollama and not integration and not broken"

# Build
python -m build --wheel

# Run server
uvicorn adam.api.server_minimal:app --port 8000

# Open browser
# http://localhost:8000/        → chat UI
# http://localhost:8000/docs    → API docs
# http://localhost:8000/metrics → metrics
```

---

*Last updated: June 15, 2026 — Adam Prism v1.0.0b1 (showcase-minimal)*
*Maintainer: Mohamed Othman — othman@adam-prism.local*
