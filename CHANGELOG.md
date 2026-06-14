# Changelog

All notable changes to Adam Prism will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased] - 2026-XX-XX

### ⚖️ License Change: AGPL v3 (dual-license model)

Adam Prism is now released under **AGPL v3** (was Apache 2.0) with a
**dual-license** commercial offering. See `LICENSE`, `COMMERCIAL_LICENSE.md`,
and `RIGHTS.md` for the full terms.

- **AGPL v3**: Free for personal, educational, research, and internal
  commercial use. If you serve Adam Prism as a SaaS to external users,
  you must either publish your source code (Section 13) or purchase a
  commercial license.
- **Commercial**: 3 tiers ($2,400 / $12,000 / $60,000 per year) for
  SaaS, embedded, and enterprise deployments that need source-code
  privacy and IP indemnification.

Why AGPL v3? To prevent big companies from forking Adam Prism and
hosting it as a paid SaaS without contributing back. Individual
developers and internal use are completely unaffected.

### 🎉 First Public Beta Release

This is the first community-ready release of Adam Prism. Three major hardening phases
were completed before this release:

- **Phase 1: Critical Security** — XSS fixes, CSP headers, ethics gate fail-closed,
  Pydantic models for all routes, structured JSON logging.
- **Phase 2: Production Hardening** — async subprocess, connection pooling,
  database backup, WebSocket heartbeat, PWA support, electron-updater.
- **Phase 3: Enterprise Features** — JWT auth + next-auth, Redis caching,
  Kubernetes Helm charts, OpenAPI 3.1, E2E tests, React Native mobile app.

### Added
- **SDK:** Production-grade Python client with retry, rate limiting, connection pooling, and SSE streaming
- **Auth:** Multi-user JWT authentication (register/login/refresh/me endpoints)
- **Auth:** next-auth integration in Web UI with login/register pages
- **Health:** Kubernetes-style probes at `/healthz/{live,ready,startup}` and `/health`
- **Storage:** PostgreSQL support with SQLAlchemy 2.0 + connection pooling
- **Cache:** Redis caching layer with automatic in-memory fallback
- **Kubernetes:** Full Helm chart + Kustomize manifests with HPA, PVC, RBAC, ServiceMonitor
- **Mobile:** React Native + Expo app for iOS and Android
- **Setup:** `scripts/setup.sh` single-command installer for novices
- **Diagnostics:** `adam-doctor` CLI for environment health checks
- **OpenAPI:** 3.1 spec generation (`scripts/export_openapi.py`)
- **PWA:** Service worker, manifest, offline page for mobile installation
- **E2E:** Playwright tests for Web UI (chromium, firefox, mobile)
- **Integration tests:** Full API coverage with `tests/test_integration.py`
- **Backup:** `deploy/backup.sh` + `deploy/restore.sh` for Qdrant + SQLite
- **Examples:** 5 working examples in `examples/` directory
- **Codespace:** `.devcontainer/devcontainer.json` for GitHub Codespaces
- **CI/CD:** Comprehensive matrix (lint, test, build, security scan, frontend)

### Changed
- **Breaking:** Ethics gate now fails CLOSED (returns 0.0) instead of failing open
- **Breaking:** `ignoreBuildErrors: true` removed from `next.config.ts` (TypeScript errors now block builds)
- **Breaking:** All subprocess calls migrated to `asyncio.create_subprocess_exec` (event-loop safe)
- **Breaking:** Pydantic models replace raw `dict` for 16 routes
- **Security:** XSS vulnerability in TerminalPanel fixed (was `dangerouslySetInnerHTML`)
- **Security:** Content Security Policy headers added to Electron, Web UI, VS Code extension
- **Security:** API key moved to OS-level encrypted storage via Electron `safeStorage`
- **Performance:** Qdrant client connection pooling (singleton per URL)
- **Performance:** `WebSocket` heartbeat (30s) + message size limit (64KB)
- **Dependencies:** Upper bounds added to all Python dependencies (supply chain hardening)
- **Dependencies:** `mcp`, `playwright`, `qdrant-client` etc. pinned to `<2.0.0`
- **Architecture:** Engine refactored to mixin chain in `backend/adam/engine/`

### Fixed
- **Critical:** XSS in Electron `TerminalPanel` (was `dangerouslySetInnerHTML` with regex parsing)
- **Critical:** Missing CSP in Electron, Web UI, VS Code extension
- **Critical:** API key stored in plaintext in Electron (now uses `safeStorage`)
- **High:** Race condition in MCP failed connections (now cleaned up)
- **High:** Ethics gate fail-open pattern (0.5 → 0.0 on error)
- **High:** 16 routes accepting raw `dict` (now use Pydantic models)
- **Medium:** GZip/brotli for SSE streaming responses
- **Medium:** TypeScript errors silently ignored (now fail builds)
- **Medium:** No `error.tsx` boundaries (white screen crashes possible)
- **Medium:** `train_lora.py` calling `load_model_and_processor` (typo for `load_model_and_tokenizer`)
- **Medium:** Absolute path `/mnt/Workspace/...` in `Dockerfile.inference`
- **Low:** Trailing whitespace in 50+ Python files
- **Low:** CI/CD workflows had multiple issues (Pinned action versions, no `|| true` on lint, etc.)

### Security
- **CVE-class:** No known CVEs at release time
- **Audit:** 22+ security fixes applied across all platforms
- **Reporting:** See [SECURITY.md](SECURITY.md) for vulnerability disclosure policy

## [Pre-release] - 2025-XX-XX

### Internal milestones (not released publicly)
- Initial framework design with 12 consciousness layers
- 2,317 training conversations for QLoRA fine-tuning
- 25 messaging channel integrations
- 38+ built-in tools
- 4-law ethics gate (Justice / Learning / Survival / Creativity)
- 4-layer Iron Memory (Hot/FTS5/Qdrant/Skills)

---

## Migration Guide

### From pre-release → 2.0.0

1. **API Key:** Set `ADAM_API_KEY` to a strong random value (e.g., `openssl rand -hex 32`)
2. **Database:** Either set `ADAM_DATABASE_URL` for PostgreSQL, or use default SQLite
3. **Cache:** Optionally set `ADAM_REDIS_URL` for distributed caching
4. **Auth:** Optionally set `ADAM_JWT_SECRET` for multi-user JWT auth
5. **Run:** `python main.py --port 8000` or use Docker

### Docker migration
```bash
# Old
docker run -d -p 8000:8000 adam-prism:latest

# New (with all defaults)
docker compose -f deploy/docker-compose.yml up -d
```

---

[Unreleased]: https://github.com/othmastar/adam-prism/compare/v1.0.0...HEAD
