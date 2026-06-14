# Plan: Adam Prism "Showcase" Version

## Goal
Public-facing repo that demonstrates Adam Prism is real, working, installable,
and has the architecture. **Removes ~75% of features** that are:
- Proprietary (training data, fine-tuned model weights)
- Tenant-specific (real configs, secrets)
- Internally useful only (agent logs, internal docs)

**Keeps:**
- All code, tests, build pipeline
- Architecture documentation
- Example data (synthetic, no IP)
- Public-facing features (web UI shell, CLI, install script)
- One minimal "hello world" that proves the runtime works

## Removed in showcase branch

| Category | Removed | Reason |
|---|---|---|
| **Training data** | `data/training/ADAM_COMPLETE/*` (2,317 convos) | Private dataset, Adam's "soul" |
| **Model weights** | `checkpoints/*` (1.1 GB LoRA) | Proprietary fine-tuning |
| **Internal docs** | `AGENTS.md` (12 KB project log) | Internal dev notes |
| **Internal subagents** | `adam/subagents/*` (specific agents) | Business logic |
| **Plugin configs** | `adam/plugins/*` (real plugins) | Customer-specific |
| **Channel adapters** | `adam/channels/bulk.py` (Telegram specific) | Tenant configs |
| **Real notebooks** | `adam/notebook/*` (real user data) | Privacy |
| **Real reflections** | `data/learning/reflections.json` | Production learnings |
| **Internal skills** | `adam/skills/builtin/*` (most) | Org-specific |
| **Real OAuth configs** | Hardcoded test keys in `adam/auth/sso.py` | Replace with mocks |
| **Internal scripts** | `scripts/merge_lora.py` | Training pipeline |
| **Old .env** | `backend/.env` | Real keys |
| **CHANGES.md** | Internal changelog | Replaced with stub |

## Replaced with stubs

- `data/training/` → `data/training/.gitkeep` + `data/training/README.md` (explains the structure)
- `adam/skills/builtin/` → keep 1 example only (`explain-code.md`), remove 4
- `adam/notebook/` → `examples/notebook/` with synthetic data
- `adam/auth/sso.py` → mock providers, no real `client_id`/`secret`
- Internal scripts → keep `bin/install.sh`, remove training scripts

## Kept 100% as-is

- `backend/adam/{api,core,engine,security,observability,webhooks,voice,...}` — all engine code
- `tests/` — full test suite (336 tests)
- `deploy/` — docker, helm, kustomize, gitops
- `docs/adr/`, `docs/DISASTER_RECOVERY.md`, `docs/COMPARISON.md`
- `frontend/web-ui/src/` — all components
- `frontend/mobile-app-expo/`, `frontend/desktop-app/`, `frontend/vscode-extension/`
- `pyproject.toml`, `LICENSE`, `README.md`, `CHANGELOG.md`
- `bin/install.sh`, `examples/quickstart.sh`
- All CI/CD workflows

## Branch strategy

- `main` — full version (current, 802 files, 72k lines, includes data+checkpoints locally)
- `showcase` — clean public version (target: ~250 files, ~25k lines)

## CI

The `showcase` branch must:
- ✅ Pass all 336 tests
- ✅ `pip install -e .` works
- ✅ `python -m build` produces wheel + sdist
- ✅ Docker compose `up` starts
- ✅ `python main.py --port 8001` boots

The `showcase` branch explicitly does NOT:
- ❌ Need real Ollama running (uses mock LLM in tests)
- ❌ Need real Qdrant (uses in-memory fallback)
- ❌ Need real API keys (uses `test-key-for-ci-only`)

## Steps

1. ✅ Create branch `showcase` from `main`
2. ✅ Backup full data to `/tmp/adam-prism-archive/full-backup-20260615.tar.gz`
3. Remove files (see table above)
4. Replace training/learning/notebook with stubs
5. Update README + add `SHOWCASE.md` explaining what's removed
6. Verify: tests, ruff, build
7. Push `showcase` to origin
8. Set as default branch on GitHub (so visitors land on showcase)
9. Keep `main` as the "full" branch (visible but not default)
