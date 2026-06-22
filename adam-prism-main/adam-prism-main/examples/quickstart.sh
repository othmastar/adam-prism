#!/usr/bin/env bash
# Adam Prism — 30-second quickstart
# Run: bash examples/quickstart.sh
#
# Starts:
#   - Ollama (local LLM)  on :11434
#   - Qdrant (vector DB)  on :6333
#   - Adam API            on :8000
#   - Web UI              on :3000
#
# In another terminal you can chat with Adam:
#   curl -X POST http://localhost:8000/chat -H "Authorization: Bearer $ADAM_API_KEY" \
#        -H "Content-Type: application/json" -d '{"message":"أدهم انت مين؟"}'
#
set -euo pipefail

CYAN='\033[0;36m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

banner() {
    echo -e "${CYAN}"
    cat <<'EOF'
   ___      __    __  ___   __  ___
  / _ \____/ /_  /  |/  /  /  |/  /
 / ___/_  / __ \/ /|_/ /  / /|_/ /
/_/   /_/ /_/ /_/  /_/  /_/  /_/

The Conscious Digital Twin — v1.0.0b1
EOF
    echo -e "${NC}"
}

ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${YELLOW}✗${NC} $*" >&2; exit 1; }

banner

# ── 1. Sanity checks ────────────────────────────────────────────────────────
command -v docker >/dev/null 2>&1 || fail "docker not found — install Docker first (https://docker.com)"
command -v curl   >/dev/null 2>&1 || fail "curl not found"
ok "docker + curl available"

# ── 2. Working directory ────────────────────────────────────────────────────
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"
ok "workspace: $ROOT"

# ── 3. Generate API key if missing ──────────────────────────────────────────
if [[ ! -f backend/.env ]]; then
    KEY=$(openssl rand -hex 24 2>/dev/null || head -c 48 /dev/urandom | xxd -p -c 48)
    cat > backend/.env <<EOF
ADAM_API_KEY=$KEY
ADAM_OLLAMA_BASE=http://ollama:11434
ADAM_QDRANT_URL=http://qdrant:6333
ADAM_PRODUCTION=0
ADAM_WAF_MODE=log
EOF
    ok "generated backend/.env (API key: ${KEY:0:8}…)"
else
    ok "backend/.env exists"
fi

# ── 4. Pull the stack with docker-compose ───────────────────────────────────
if [[ -f deploy/docker-compose.yml ]]; then
    COMPOSE="docker compose -f deploy/docker-compose.yml"
elif [[ -f docker-compose.yml ]]; then
    COMPOSE="docker compose"
else
    fail "docker-compose.yml not found"
fi

ok "starting stack… (this is the slow part — ~60s first time)"
$COMPOSE up -d ollama qdrant

# ── 5. Wait for Ollama to be healthy ────────────────────────────────────────
echo -n "waiting for ollama"
for i in {1..40}; do
    if curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
        echo
        ok "ollama is up"
        break
    fi
    echo -n "."
    sleep 2
    [[ $i -eq 40 ]] && fail "ollama didn't start in 80s"
done

# ── 6. Pull the model (idempotent) ──────────────────────────────────────────
MODEL="${ADAM_MODEL:-qwen2.5:3b}"
if curl -fsS http://localhost:11434/api/show -d "{\"name\":\"$MODEL\"}" >/dev/null 2>&1; then
    ok "model $MODEL already present"
else
    warn "pulling $MODEL (~2 GB, first time)…"
    docker exec adam-ollama ollama pull "$MODEL" || warn "model pull failed — will retry on first chat"
fi

# ── 7. Start the API + UI ───────────────────────────────────────────────────
$COMPOSE up -d api web-ui

# ── 8. Wait for API ─────────────────────────────────────────────────────────
echo -n "waiting for api"
for i in {1..30}; do
    if curl -fsS http://localhost:8000/healthz/live >/dev/null 2>&1; then
        echo
        ok "api is up on :8000"
        break
    fi
    echo -n "."
    sleep 1
    [[ $i -eq 30 ]] && warn "api didn't start in 30s — check 'docker compose logs api'"
done

# ── 9. Done ─────────────────────────────────────────────────────────────────
cat <<EOF

${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
 Adam Prism is up.
${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

 🌐 Web UI:     http://localhost:3000
 🔌 API:        http://localhost:8000
 📖 API docs:   http://localhost:8000/docs
 🧠 Qdrant:     http://localhost:6333/dashboard
 🤖 Ollama:     http://localhost:11434

 Try it:
   curl -X POST http://localhost:8000/chat \\
        -H "Authorization: Bearer \$(grep ADAM_API_KEY backend/.env | cut -d= -f2)" \\
        -H "Content-Type: application/json" \\
        -d '{"message":"أدهم، انت مين؟"}'

 Stop everything:
   $COMPOSE down

 Logs:
   $COMPOSE logs -f api

EOF
