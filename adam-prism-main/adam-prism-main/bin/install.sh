#!/usr/bin/env bash
# Adam Prism — one-command installer for Linux / macOS / WSL
# Run: curl -fsSL https://raw.githubusercontent.com/othmastar/adam-prism/main/bin/install.sh | bash
# Or:  bash bin/install.sh
#
# Installs: Docker (if missing), pulls repo, builds images, starts stack,
# creates a desktop launcher (Linux/Wayland only).
#
set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${YELLOW}✗${NC} $*" >&2; exit 1; }

# Detect OS
OS="$(uname -s)"
case "$OS" in
    Linux*)  PLATFORM=linux ;;
    Darwin*) PLATFORM=mac  ;;
    *)       fail "unsupported OS: $OS" ;;
esac
ok "platform: $PLATFORM"

# ── 1. Check prerequisites ──────────────────────────────────────────────────
command -v curl >/dev/null 2>&1 || fail "curl not found — please install curl first"
command -v git  >/dev/null 2>&1 || fail "git not found — please install git first"

# ── 2. Install Docker if missing ────────────────────────────────────────────
if ! command -v docker >/dev/null 2>&1; then
    warn "docker not found — installing…"
    if [[ $PLATFORM == mac ]]; then
        warn "please install Docker Desktop from https://docker.com/products/docker-desktop"
        warn "then re-run this script"
        exit 1
    fi
    if command -v apt-get >/dev/null 2>&1; then
        curl -fsSL https://get.docker.com | sh
        sudo usermod -aG docker "$USER"
        warn "you've been added to the docker group — please log out and back in"
    elif command -v dnf >/dev/null 2>&1; then
        sudo dnf -y install docker docker-compose
        sudo systemctl enable --now docker
        sudo usermod -aG docker "$USER"
    elif command -v pacman >/dev/null 2>&1; then
        sudo pacman -S --noconfirm docker docker-compose
        sudo systemctl enable --now docker
        sudo usermod -aG docker "$USER"
    else
        fail "no package manager found — install Docker manually"
    fi
    ok "docker installed"
else
    ok "docker already installed: $(docker --version)"
fi

# ── 3. Clone or update repo ─────────────────────────────────────────────────
INSTALL_DIR="${ADAM_HOME:-$HOME/adam-prism}"
if [[ -d "$INSTALL_DIR/.git" ]]; then
    warn "found existing install at $INSTALL_DIR — pulling latest"
    git -C "$INSTALL_DIR" pull --ff-only
else
    ok "cloning adam-prism to $INSTALL_DIR"
    git clone https://github.com/othmastar/adam-prism.git "$INSTALL_DIR"
fi
cd "$INSTALL_DIR"

# ── 4. Generate secrets ─────────────────────────────────────────────────────
mkdir -p backend deploy
if [[ ! -f backend/.env ]]; then
    KEY=$(openssl rand -hex 24 2>/dev/null || head -c 48 /dev/urandom | xxd -p -c 48)
    cat > backend/.env <<EOF
ADAM_API_KEY=$KEY
ADAM_PRODUCTION=1
ADAM_WAF_MODE=log
ADAM_OLLAMA_BASE=http://ollama:11434
ADAM_QDRANT_URL=http://qdrant:6333
EOF
    ok "generated secrets in backend/.env"
fi

# ── 5. Build & start ────────────────────────────────────────────────────────
ok "building images (first run is slow, ~3 min)…"
docker compose -f deploy/docker-compose.yml build --pull
docker compose -f deploy/docker-compose.yml up -d ollama qdrant
ok "starting ollama + qdrant…"

# ── 6. Wait for ollama + pull model ─────────────────────────────────────────
echo -n "waiting for ollama"
for i in {1..60}; do
    if docker exec adam-ollama ollama list >/dev/null 2>&1; then break; fi
    echo -n "."; sleep 2
    [[ $i -eq 60 ]] && fail "ollama didn't start in 2 min"
done
echo
ok "ollama is ready"
MODEL="${ADAM_MODEL:-qwen2.5:3b}"
if ! docker exec adam-ollama ollama show "$MODEL" >/dev/null 2>&1; then
    warn "pulling model $MODEL (~2 GB, this may take a few minutes)…"
    docker exec adam-ollama ollama pull "$MODEL"
fi
ok "model $MODEL ready"

# ── 7. Start API + UI ───────────────────────────────────────────────────────
docker compose -f deploy/docker-compose.yml up -d api web-ui nginx
ok "stack is up"

# ── 8. Wait for health ──────────────────────────────────────────────────────
echo -n "waiting for api"
for i in {1..30}; do
    if curl -fsS http://localhost:8000/healthz/live >/dev/null 2>&1; then break; fi
    echo -n "."; sleep 1
done
echo
ok "api healthy on :8000"

# ── 9. Desktop entry (Linux only) ───────────────────────────────────────────
if [[ $PLATFORM == linux ]] && [[ -d $HOME/.local/share/applications ]]; then
    cat > "$HOME/.local/share/applications/adam-prism.desktop" <<EOF
[Desktop Entry]
Name=Adam Prism
Comment=Conscious Digital Twin
Exec=xdg-open http://localhost:3000
Icon=utilities-terminal
Type=Application
Categories=Development;AI;
EOF
    ok "desktop launcher created"
fi

# ── 10. Done ────────────────────────────────────────────────────────────────
cat <<EOF

${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}
 ✅ Adam Prism installed successfully
${GREEN}━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━${NC}

 📂 Install:    $INSTALL_DIR
 🌐 Web UI:     http://localhost:3000
 🔌 API:        http://localhost:8000
 📖 Docs:       http://localhost:8000/docs
 📋 Logs:       cd $INSTALL_DIR && docker compose -f deploy/docker-compose.yml logs -f

 Manage:
   cd $INSTALL_DIR
   docker compose -f deploy/docker-compose.yml stop
   docker compose -f deploy/docker-compose.yml start
   docker compose -f deploy/docker-compose.yml down

 Update:
   cd $INSTALL_DIR && git pull && bash bin/install.sh

EOF
