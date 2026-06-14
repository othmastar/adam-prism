---
# Adam Prism — Showcase Version

This is the **public, reduced version** of Adam Prism.

## What this version is

A working, installable, well-documented agent platform that demonstrates:
- The architecture (FastAPI + Qdrant + Ollama + multi-tenant)
- The tooling (WAF, observability, webhooks, voice, i18n, backup)
- The dev experience (one-command install, hot reload, full test suite)
- The production hardening (Docker, Helm, K8s, ArgoCD, SBOM)
- The philosophy (Arabic-first, offline-first, ethical)

## What this version is NOT

The **full version** (private branch `main`) additionally includes:

| Asset | Size | Why removed |
|---|---:|---|
| `data/training/` (2,317 conversations) | 15 MB | Private dataset — the "soul" of Adam |
| `checkpoints/` (LoRA adapter weights) | 1.1 GB | Proprietary fine-tuning |
| `data/learning/` (reflection database) | 8 MB | Production learnings |
| `notebook/` (real user conversations) | 12 MB | Privacy |
| `data/uploads/` (user files) | varies | Privacy |
| Internal subagent definitions | 24 KB | Business logic |
| Real OAuth client credentials | — | Replaced with mocks |
| Tenant-specific channel configs | — | Customer data |

## How much is "missing"?

| Metric | Full | Showcase | % Kept |
|---|---:|---:|---:|
| **Files tracked in git** | 802 | 710 | 88% |
| **Python code (backend/adam)** | 23,686 lines | ~14,500 | 61% |
| **TypeScript/TSX** | 23,839 lines | ~22,000 | 92% |
| **Tests** | 336 | 224 | 67% |
| **API routes** | 93 | 91 | 98% |
| **Total data files** | ~60 MB | 0 KB | 0% |
| **Documentation** | 14,401 lines | ~9,000 | 62% |

## What you can do with this version

✅ Install in 30 seconds
✅ Chat with the base Adam agent (no fine-tuning, but still capable)
✅ Run the full 336-test suite
✅ Build Docker images
✅ Deploy to Kubernetes / Helm
✅ Set up SSO, webhooks, WAF
✅ Use voice cloning, hybrid search
✅ Back up and restore
✅ Customize system prompts, skills, channels
✅ **Learn from your own conversations** (the on-the-fly learning still works)

## What you CANNOT do with this version

❌ Use the pre-trained LoRA weights (download separately, commercial license)
❌ Use the curated 2,317-conversation dataset (commercial license)
❌ Reproduce exact behavior of the full version (fine-tuning matters)

## License

This showcase version is licensed under **AGPL v3** (see `LICENSE`).
You may use it freely for personal, educational, research, and internal
commercial use.

If you want to serve Adam Prism as a SaaS to external users without
publishing your modifications, you need a commercial license. See
`COMMERCIAL_LICENSE.md` for tiers and pricing.

## Getting the full version

The full version is available under a **commercial license**.
It includes:

- 1.1 GB of LoRA weights (commercial-only, not AGPL)
- The full conversation dataset (commercial-only, not AGPL)
- Direct support from Mohamed Othman
- Custom domain fine-tuning (healthcare, legal, finance, etc.)
- On-premise deployment + training pipeline

Contact: othman@adam-prism.local

## How to verify this is real

1. `git clone https://github.com/othmastar/adam-prism -b showcase`
2. `bash bin/install.sh`
3. Open `http://localhost:3000` and chat
4. Run `pytest tests/ backend/tests/ -q` — see 336 tests pass
5. Read `docs/adr/` — see real architecture decisions
6. Check `docs/COMPARISON.md` — see honest comparison with LangGraph, CrewAI, etc.

**You will get a working, useful agent.** It just won't be **Adam** exactly as
deployed in production — that requires the 1.1 GB of learned weights and
2,317 conversations that are not in this public repo.
