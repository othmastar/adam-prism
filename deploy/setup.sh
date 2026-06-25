#!/bin/bash
# ═════════════════════════════════════════════════════════
# Adam Prism — VM Production Setup
# One-command deployment script
# ═════════════════════════════════════════════════════════
#
# Usage:
#   sudo bash deploy/setup.sh
#
# Prerequisites:
#   - Ubuntu 22.04+ (or Debian 12+)
#   - Domain (adam-prism.online) pointing to this VM's IP
#   - Ollama Cloud API key (for chat)
#
# ═════════════════════════════════════════════════════════

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT_DIR"

echo "══════════════════════════════════════════"
echo "  Adam Prism — Production Setup"
echo "══════════════════════════════════════════"

# ─── 1. System packages ───────────────────────────
echo "▶ [1/7] Installing system packages..."
sudo apt-get update -qq
sudo apt-get install -y -qq \
    curl ca-certificates openssl \
    apt-transport-https software-properties-common \
    python3 python3-pip

# ─── 2. Docker ────────────────────────────────────
echo "▶ [2/7] Installing Docker..."
if ! command -v docker &>/dev/null; then
    curl -fsSL https://get.docker.com | sudo bash
    sudo usermod -aG docker "$USER"
    echo "  ✅ Docker installed"
else
    echo "  ✅ Docker already installed"
fi

# ─── 3. Native Ollama (for embeddings) ────────────
echo "▶ [3/7] Installing native Ollama for embeddings..."
if ! command -v ollama &>/dev/null; then
    curl -fsSL https://ollama.ai/install.sh | sh
    echo "  ✅ Ollama installed"
else
    echo "  ✅ Ollama already installed"
fi

# Pull embedding model
echo "  Pulling nomic-embed-text..."
ollama pull nomic-embed-text 2>&1 | tail -1
echo "  ✅ Embedding model ready"

# ─── 4. Environment file ─────────────────────────
echo "▶ [4/7] Creating .env.production..."
if [ ! -f deploy/.env.production ]; then
    # Generate random secrets
    ADAM_API_KEY="adam-$(openssl rand -hex 32)"
    ADAM_ADMIN_KEY="adam-admin-$(openssl rand -hex 32)"
    JWT_SECRET="$(openssl rand -base64 48)"
    NEXTAUTH_SECRET="$(openssl rand -base64 32)"

    cat > deploy/.env.production << ENVEOF
# ═══════════════════════════════════════════
# Adam Prism — Production Environment
# ═══════════════════════════════════════════

# --- Ollama Cloud (for chat) ---
OLLAMA_BASE=https://api.ollama.cloud
OLLAMA_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxx
MODEL_NAME=gemma3:8b

# --- Local Ollama (for embeddings) ---
# داخل Docker: 172.17.0.1 هو gateway bridge يوصل للمضيف
EMBEDDING_BASE_URL=http://172.17.0.1:11434
EMBEDDING_MODEL=nomic-embed-text

# --- Domain ---
ADAM_DOMAIN=adam-prism.online
ADAM_ENV=production
ADAM_PRODUCTION=1

# --- API Keys (generated) ---
ADAM_API_KEY=${ADAM_API_KEY}
ADAM_ADMIN_KEY=${ADAM_ADMIN_KEY}
ADAM_JWT_SECRET=${JWT_SECRET}

# --- CORS ---
ADAM_CORS_ORIGINS=https://adam-prism.online

# --- Frontend ---
NEXTAUTH_SECRET=${NEXTAUTH_SECRET}
NEXTAUTH_URL=https://adam-prism.online

# --- Qdrant (optional — set when ready) ---
# QDRANT_URL=http://qdrant:6333

# --- Monitoring ---
GRAFANA_ADMIN_PASSWORD=CHANGE-ME-$(openssl rand -hex 8)
ENVEOF
    echo "  ✅ .env.production created with random keys"
    echo ""
    echo "  ⚠️  IMPORTANT: Edit deploy/.env.production and set:"
    echo "      - OLLAMA_API_KEY (your Ollama Cloud key)"
    echo "      - OLLAMA_BASE (Ollama Cloud API URL)"
    echo ""
    echo "  Your generated API keys:"
    echo "    ADAM_API_KEY=${ADAM_API_KEY}"
    echo "    ADAM_ADMIN_KEY=${ADAM_ADMIN_KEY}"
else
    echo "  ⏭️  .env.production already exists"
fi

# ─── 5. SSL Certificate (Let's Encrypt) ───────────
echo "▶ [5/7] Setting up SSL..."
mkdir -p deploy/ssl

if [ ! -f deploy/ssl/adam-prism.crt ]; then
    # Generate self-signed for now (replace with Let's Encrypt later)
    bash deploy/generate_ssl.sh
    echo ""
    echo "  ⚠️  Self-signed cert generated. For production:"
    echo "     sudo apt-get install certbot python3-certbot-nginx"
    echo "     sudo certbot --nginx -d adam-prism.online"
    echo ""
else
    echo "  ✅ SSL cert already exists"
fi

# ─── 6. Build & Start ────────────────────────────
echo "▶ [6/7] Building Docker images..."
# Copy env to compose context (يحتاج docker compose .env بالجذر)
cp deploy/.env.production deploy/.env
cp deploy/.env.production .env 2>/dev/null || true

docker compose -f deploy/docker-compose.prod.yml build --parallel
echo "  ✅ Build complete"

echo "▶ [7/7] Starting services..."
docker compose -f deploy/docker-compose.prod.yml up -d
echo "  ✅ Services started"

# ─── 7. Verify ────────────────────────────────────
echo ""
echo "══════════════════════════════════════════"
echo "  Verification"
echo "══════════════════════════════════════════"
sleep 5

echo ""
echo "  API health:"
curl -f http://localhost:8000/ && echo "  ✅" || echo "  ❌"

echo ""
echo "  Engine health:"
curl -f http://localhost:8000/api/engine/health 2>/dev/null && echo "  ✅" || echo "  ⚠️ (Qdrant may be offline)"

echo ""
echo "══════════════════════════════════════════"
echo "  Deployment Complete!"
echo "══════════════════════════════════════════"
echo ""
echo "  Frontend: https://adam-prism.online"
echo "  API:      https://adam-prism.online/api/status"
echo "  Grafana:  https://adam-prism.online:3001"
echo ""
echo "  Quick test:"
echo "    curl https://adam-prism.online/api/status"
echo ""
echo "  Create admin user:"
echo '    curl -X POST https://adam-prism.online/api/auth/register \'
echo '      -H "Content-Type: application/json" \'
echo '      -d '"'"'{"email":"admin@example.com","username":"admin","password":"your-strong-pass"}'"'"''
echo ""
echo "  Login & get token:"
echo '    curl -X POST https://adam-prism.online/api/auth/login \'
echo '      -H "Content-Type: application/json" \'
echo '      -d '"'"'{"email":"admin@example.com","password":"your-strong-pass"}'"'"''
echo ""
echo "  Chat:"
echo '    curl -X POST https://adam-prism.online/api/chat \'
echo '      -H "Authorization: Bearer <TOKEN>" \'
echo '      -H "Content-Type: application/json" \'
echo '      -d '"'"'{"message":"hello"}'"'"''
echo ""
echo "  View logs:"
echo "    docker compose -f deploy/docker-compose.prod.yml logs api"
echo "    docker compose -f deploy/docker-compose.prod.yml logs web"
echo ""
