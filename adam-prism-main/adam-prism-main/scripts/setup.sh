#!/bin/bash
# ═══════════════════════════════════════════════════════════
# Adam Prism — Setup Script for Novices
# Single command to get a working install on Linux/macOS/WSL
#
# Usage:
#   ./scripts/setup.sh          # interactive
#   ./scripts/setup.sh --quick  # non-interactive with defaults
#   ./scripts/setup.sh --docker # full Docker stack
#   ./scripts/setup.sh --k8s    # Kubernetes/Helm
# ═══════════════════════════════════════════════════════════

set -e

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(dirname "$SCRIPT_DIR")"
cd "$ROOT_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Flags
QUICK=0
DOCKER=0
K8S=0
SKIP_DEPS=0
SKIP_MODEL=0

while [[ $# -gt 0 ]]; do
    case $1 in
        --quick) QUICK=1; shift ;;
        --docker) DOCKER=1; shift ;;
        --k8s) K8S=1; shift ;;
        --skip-deps) SKIP_DEPS=1; shift ;;
        --skip-model) SKIP_MODEL=1; shift ;;
        --help)
            echo "Adam Prism Setup"
            echo ""
            echo "Usage: $0 [options]"
            echo ""
            echo "Options:"
            echo "  --quick        Non-interactive with sensible defaults"
            echo "  --docker       Full Docker stack (Qdrant + Ollama + API + Web)"
            echo "  --k8s          Deploy to Kubernetes via Helm"
            echo "  --skip-deps    Skip installing system dependencies"
            echo "  --skip-model   Skip downloading Ollama models"
            echo "  --help         Show this help"
            exit 0
            ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# ── Step 1: Detect OS ────────────────────────────────────────
detect_os() {
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        if [ -f /etc/os-release ]; then
            . /etc/os-release
            OS="$ID"
        else
            OS="linux"
        fi
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    else
        OS="unknown"
    fi
    echo -e "${BLUE}ℹ${NC} Detected OS: $OS"
}

# ── Step 2: Check Python ──────────────────────────────────────
check_python() {
    if command -v python3 >/dev/null 2>&1; then
        PYTHON=python3
    elif command -v python >/dev/null 2>&1; then
        PYTHON=python
    else
        echo -e "${RED}✗${NC} Python 3.10+ not found. Please install it first."
        echo "  - macOS: brew install python@3.12"
        echo "  - Ubuntu: sudo apt install python3.12"
        echo "  - Or use pyenv: https://github.com/pyenv/pyenv"
        exit 1
    fi
    PY_VERSION=$($PYTHON -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    echo -e "${GREEN}✓${NC} Found Python $PY_VERSION"
    if [[ $(echo "$PY_VERSION >= 3.10" | bc -l) == "0" ]] 2>/dev/null; then
        echo -e "${YELLOW}⚠${NC} Python 3.10+ recommended. You have $PY_VERSION"
    fi
}

# ── Step 3: Install dependencies ─────────────────────────────
install_deps() {
    if [[ "$SKIP_DEPS" == "1" ]]; then
        return
    fi
    echo -e "${BLUE}→${NC} Installing system dependencies..."
    case "$OS" in
        ubuntu|debian)
            sudo apt-get update -qq
            sudo apt-get install -y curl git build-essential libssl-dev
            ;;
        fedora|rhel|centos)
            sudo dnf install -y curl git gcc make openssl-devel
            ;;
        macos)
            if ! command -v brew >/dev/null 2>&1; then
                echo -e "${YELLOW}⚠${NC} Homebrew not found. Install from https://brew.sh"
            else
                brew install curl git
            fi
            ;;
    esac
}

# ── Step 4: Install Ollama ────────────────────────────────────
install_ollama() {
    if command -v ollama >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Ollama already installed"
        return
    fi
    echo -e "${BLUE}→${NC} Installing Ollama..."
    if [[ "$OS" == "macos" ]]; then
        brew install ollama
    else
        curl -fsSL https://ollama.com/install.sh | sh
    fi
    echo -e "${GREEN}✓${NC} Ollama installed"
}

# ── Step 5: Pull model ───────────────────────────────────────
pull_model() {
    if [[ "$SKIP_MODEL" == "1" ]]; then
        return
    fi
    echo -e "${BLUE}→${NC} Pulling default model (gemma3:8b)..."
    ollama pull gemma3:8b
    echo -e "${GREEN}✓${NC} Model pulled"
}

# ── Step 6: Start Ollama ─────────────────────────────────────
start_ollama() {
    if pgrep -f "ollama serve" >/dev/null; then
        echo -e "${GREEN}✓${NC} Ollama already running"
        return
    fi
    echo -e "${BLUE}→${NC} Starting Ollama in background..."
    if [[ "$OS" == "macos" ]]; then
        brew services start ollama
    else
        nohup ollama serve >/tmp/ollama.log 2>&1 &
        sleep 2
    fi
    # Wait for Ollama to be ready
    for i in {1..30}; do
        if curl -sf http://localhost:11434/api/tags >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Ollama running on http://localhost:11434"
            return
        fi
        sleep 1
    done
    echo -e "${YELLOW}⚠${NC} Ollama didn't start in 30s. Check logs at /tmp/ollama.log"
}

# ── Step 7: Install Python deps ──────────────────────────────
install_python_deps() {
    echo -e "${BLUE}→${NC} Creating virtual environment..."
    if [ ! -d "venv" ]; then
        $PYTHON -m venv venv
    fi
    source venv/bin/activate
    echo -e "${BLUE}→${NC} Upgrading pip..."
    pip install --upgrade pip -q
    echo -e "${BLUE}→${NC} Installing Adam Prism..."
    pip install -e . -q
    echo -e "${GREEN}✓${NC} Adam Prism installed"
}

# ── Step 8: Setup .env ────────────────────────────────────────
setup_env() {
    if [ ! -f ".env" ]; then
        echo -e "${BLUE}→${NC} Creating .env from template..."
        cp .env.example .env 2>/dev/null || true
        # Generate strong random keys
        ADAM_KEY=$(openssl rand -hex 24)
        ADAM_ADMIN=$(openssl rand -hex 24)
        sed -i.bak "s/change-me-in-production/$ADAM_KEY/g" .env
        sed -i.bak "s/admin-change-me/$ADAM_ADMIN/g" .env
        rm -f .env.bak
        echo -e "${GREEN}✓${NC} .env created with random secrets"
    fi
}

# ── Step 9: Install Qdrant ───────────────────────────────────
install_qdrant() {
    if command -v qdrant >/dev/null 2>&1; then
        return
    fi
    if command -v docker >/dev/null 2>&1 && docker ps >/dev/null 2>&1; then
        echo -e "${BLUE}→${NC} Starting Qdrant via Docker..."
        docker run -d --name adam-qdrant -p 6333:6333 -p 6334:6334 \
            --restart unless-stopped qdrant/qdrant 2>/dev/null || true
        sleep 3
        if curl -sf http://localhost:6333/ >/dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Qdrant running on http://localhost:6333"
        fi
    else
        echo -e "${YELLOW}⚠${NC} Docker not available. Install Qdrant manually:"
        echo "  docker run -d -p 6333:6333 qdrant/qdrant"
        echo "  Or download from: https://github.com/qdrant/qdrant/releases"
    fi
}

# ── Step 10: Verify ───────────────────────────────────────────
verify() {
    echo ""
    echo -e "${BLUE}→${NC} Verifying installation..."
    if [ -f "venv/bin/adam-doctor" ] || [ -f "venv/bin/adam" ]; then
        source venv/bin/activate 2>/dev/null
        if command -v adam-doctor >/dev/null 2>&1; then
            adam-doctor || true
        elif command -v adam >/dev/null 2>&1; then
            adam --help >/dev/null 2>&1 && echo -e "${GREEN}✓${NC} adam CLI working"
        fi
    fi
    if curl -sf http://localhost:8000/healthz/live >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} Adam Prism API is running"
    else
        echo -e "${BLUE}ℹ${NC} To start the API: source venv/bin/activate && adam-prism --port 8000"
    fi
}

# ── Main flow ─────────────────────────────────────────────────
main() {
    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║   Adam Prism — Setup Wizard            ║"
    echo "║   التوأم الرقمي الواعي                 ║"
    echo "╚════════════════════════════════════════╝"
    echo ""

    detect_os
    check_python

    if [[ "$K8S" == "1" ]]; then
        echo -e "${BLUE}→${NC} Deploying to Kubernetes..."
        if ! command -v kubectl >/dev/null 2>&1; then
            echo -e "${RED}✗${NC} kubectl not found"
            exit 1
        fi
        if ! command -v helm >/dev/null 2>&1; then
            echo -e "${YELLOW}⚠${NC} helm not found. Install from https://helm.sh"
            exit 1
        fi
        # Generate secrets
        API_KEY=$(openssl rand -hex 32)
        ADMIN_KEY=$(openssl rand -hex 32)
        JWT_SECRET=$(openssl rand -hex 32)
        NEXTAUTH_SECRET=$(openssl rand -hex 32)
        GRAFANA_PASS=$(openssl rand -hex 16)
        helm install adam-prism deploy/helm/adam-prism \
            --set secrets.apiKey=$API_KEY \
            --set secrets.adminKey=$ADMIN_KEY \
            --set secrets.jwtSecret=$JWT_SECRET \
            --set secrets.nextauthSecret=$NEXTAUTH_SECRET \
            --set secrets.grafanaPassword=$GRAFANA_PASS \
            --set ingress.hosts[0].host=adam.local
        echo -e "${GREEN}✓${NC} Deployed! Check status with: kubectl get pods -l app.kubernetes.io/name=adam-prism"
        exit 0
    fi

    if [[ "$DOCKER" == "1" ]]; then
        echo -e "${BLUE}→${NC} Starting full Docker stack..."
        if ! command -v docker >/dev/null 2>&1; then
            echo -e "${RED}✗${NC} Docker not found"
            exit 1
        fi
        cp deploy/.env.example deploy/.env 2>/dev/null || true
        docker compose -f deploy/docker-compose.yml up -d
        echo -e "${GREEN}✓${NC} Docker stack started"
        echo "  API: http://localhost:8000"
        echo "  Web UI: http://localhost:3000"
        exit 0
    fi

    install_deps
    install_ollama
    start_ollama
    pull_model
    install_python_deps
    setup_env
    install_qdrant
    verify

    echo ""
    echo "╔════════════════════════════════════════╗"
    echo "║   ✅ Setup complete!                    ║"
    echo "╚════════════════════════════════════════╝"
    echo ""
    echo "Next steps:"
    echo "  1. source venv/bin/activate"
    echo "  2. adam-prism --port 8000   # start the API"
    echo "  3. Open http://localhost:8000/docs for API docs"
    echo ""
    echo "For Docker stack:"
    echo "  cd deploy && docker compose up -d"
    echo ""
    echo "For Kubernetes:"
    echo "  ./scripts/setup.sh --k8s"
    echo ""
}

main
