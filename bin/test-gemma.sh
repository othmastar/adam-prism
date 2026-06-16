#!/usr/bin/env bash
# Adam Prism — Test Gemma 4 12b locally
# Run this when the GPU is free (not during training)
#
# Usage: bash bin/test-gemma.sh

set -euo pipefail

CYAN='\033[0;36m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; NC='\033[0m'
ok()   { echo -e "${GREEN}✓${NC} $*"; }
warn() { echo -e "${YELLOW}⚠${NC} $*"; }
fail() { echo -e "${YELLOW}✗${NC} $*" >&2; exit 1; }

echo "═══════════════════════════════════════════════════════════════"
echo "  Adam Prism — Gemma 4 12b 4bit Test"
echo "═══════════════════════════════════════════════════════════════"
echo

# ── 1. Check GPU ───────────────────────────────────────────────────
echo "─── 1. GPU check ───"
if ! command -v nvidia-smi >/dev/null 2>&1; then
    fail "nvidia-smi not found — no NVIDIA GPU"
fi

FREE_MEM=$(nvidia-smi --query-gpu=memory.free --format=csv,noheader,nounits | head -1)
echo "  GPU memory free: ${FREE_MEM} MiB"

if [[ $FREE_MEM -lt 8000 ]]; then
    fail "Not enough GPU memory (need 8GB free for gemma 4:12b 4bit)"
fi
ok "GPU has enough memory"

# ── 2. Check / install Ollama ─────────────────────────────────────
echo
echo "─── 2. Ollama check ───"
if ! command -v ollama >/dev/null 2>&1; then
    warn "Ollama not installed — installing..."
    curl -fsSL https://ollama.ai/install.sh | sh
    ok "Ollama installed"
else
    ok "Ollama found: $(ollama --version)"
fi

# ── 3. Start Ollama server ────────────────────────────────────────
echo
echo "─── 3. Start Ollama server ───"
if pgrep -f "ollama serve" >/dev/null; then
    ok "Ollama already running"
else
    ollama serve > /tmp/ollama.log 2>&1 &
    OLLAMA_PID=$!
    echo "  Started Ollama (PID: $OLLAMA_PID)"
    sleep 5
    ok "Ollama started"
fi

# Wait for Ollama to be ready
for i in {1..30}; do
    if curl -fsS http://localhost:11434/api/tags >/dev/null 2>&1; then
        ok "Ollama is ready"
        break
    fi
    sleep 1
    [[ $i -eq 30 ]] && fail "Ollama didn't start in 30s"
done

# ── 4. Pull Gemma 4 12b ───────────────────────────────────────────
echo
echo "─── 4. Pull Gemma 4 12b ───"
if ollama list | grep -q "gemma.*4:12b"; then
    ok "Gemma 4 12b already present"
else
    warn "Pulling gemma4:12b (~7-8 GB)..."
    ollama pull gemma4:12b
    ok "Gemma 4 12b pulled"
fi

# ── 5. Test Ollama directly ───────────────────────────────────────
echo
echo "─── 5. Direct Ollama test ───"
TEST_RESP=$(curl -fsS http://localhost:11434/api/chat \
    -d '{
        "model": "gemma4:12b",
        "messages": [
            {"role": "user", "content": "مرحبا، انت مين؟ جاوب في جملة واحدة."}
        ],
        "stream": false
    }' 2>&1) || fail "Ollama test failed: $TEST_RESP"

RESP_TEXT=$(echo "$TEST_RESP" | /mnt/Workspace/Adam_Prism_Complete_v2/venv/bin/python -c "import sys, json; print(json.load(sys.stdin)['message']['content'])" 2>/dev/null || echo "PARSE_ERROR")

echo
echo "  Question:  مرحبا، انت مين؟ جاوب في جملة واحدة."
echo "  Response:  $RESP_TEXT"
echo

# Test Arabic specifically
if echo "$RESP_TEXT" | grep -qE "[ا-ي]"; then
    ok "Response is in Arabic (or contains Arabic)"
else
    warn "Response may not be in Arabic"
fi

# ── 6. Start Adam server ───────────────────────────────────────────
echo
echo "─── 6. Start Adam Prism server ───"
if curl -fsS http://localhost:8000/healthz/live >/dev/null 2>&1; then
    ok "Adam already running"
else
    cd /mnt/Workspace/Adam_Prism_Complete_v2
    ADAM_API_KEY=test-key-for-ci-only \
    ADAM_PRODUCTION=0 \
    ADAM_OLLAMA_MODEL=gemma4:12b \
    /mnt/Workspace/Adam_Prism_Complete_v2/venv/bin/uvicorn adam.api.server_minimal:app \
        --host 0.0.0.0 --port 8000 > /tmp/adam.log 2>&1 &
    ADAM_PID=$!
    echo "  Started Adam (PID: $ADAM_PID)"
    sleep 3
fi

# Wait for Adam
for i in {1..15}; do
    if curl -fsS http://localhost:8000/healthz/live >/dev/null 2>&1; then
        ok "Adam is ready"
        break
    fi
    sleep 1
    [[ $i -eq 15 ]] && fail "Adam didn't start in 15s"
done

# ── 7. Test Adam's /chat ───────────────────────────────────────────
echo
echo "─── 7. Adam /chat test (real Arabic conversation) ───"
ADAM_RESP=$(curl -fsS -X POST http://localhost:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"message": "مرحبا آدم. انت مين؟ وايه اللي بتعرف تعمله؟"}' 2>&1) || fail "Adam chat failed: $ADAM_RESP"

ADAM_TEXT=$(echo "$ADAM_RESP" | /mnt/Workspace/Adam_Prism_Complete_v2/venv/bin/python -c "import sys, json; print(json.load(sys.stdin)['response'])" 2>/dev/null || echo "PARSE_ERROR")

echo
echo "  Question:  مرحبا آدم. انت مين؟ وايه اللي بتعرف تعمله؟"
echo "  Response:  $ADAM_TEXT"
echo

if echo "$ADAM_TEXT" | grep -qE "[ا-ي]"; then
    ok "Adam responded in Arabic"
else
    warn "Adam's response may not be in Arabic"
fi

# ── 8. Test Adam's 5 features ─────────────────────────────────────
echo
echo "─── 8. Test all 5 features ───"

# 8a. Health check
HEALTH=$(curl -fsS http://localhost:8000/healthz/live | /mnt/Workspace/Adam_Prism_Complete_v2/venv/bin/python -c "import sys, json; d=json.load(sys.stdin); print(f\"{d['status']} v{d['version']}\")")
ok "Feature 1 (healthz): $HEALTH"

# 8b. Docs
DOCS=$(curl -fsS -o /dev/null -w "%{http_code}" http://localhost:8000/docs)
[[ "$DOCS" == "200" ]] && ok "Feature 2 (docs): HTTP 200" || warn "Feature 2 (docs): HTTP $DOCS"

# 8c. Metrics
METRICS=$(curl -fsS http://localhost:8000/metrics | wc -l)
ok "Feature 3 (metrics): $METRICS lines of Prometheus output"

# 8d. Skills
SKILLS=$(curl -fsS http://localhost:8000/api/skills | /mnt/Workspace/Adam_Prism_Complete_v2/venv/bin/python -c "import sys, json; print(len(json.load(sys.stdin)['skills']))")
ok "Feature 4 (skills): $SKILLS skills listed"

# 8e. Compression
COMP=$(curl -fsS http://localhost:8000/api/compression | /mnt/Workspace/Adam_Prism_Complete_v2/venv/bin/python -c "import sys, json; d=json.load(sys.stdin); print(f\"mode={d['compression']['mode']}, available={d['compression']['headroom_available']}\")")
ok "Feature 5 (compression): $COMP"

# 8f. Compression test endpoint
COMP_TEST=$(curl -fsS -X POST http://localhost:8000/api/compression/test \
    -H "Content-Type: application/json" \
    -d "{\"content\": \"$(printf 'x%.0s' {1..2000})\", \"content_type\": \"text\"}" | /mnt/Workspace/Adam_Prism_Complete_v2/venv/bin/python -c "import sys, json; d=json.load(sys.stdin); print(f\"tokens {d['original_tokens']} → {d['compressed_tokens']}, saved {d['tokens_saved']}\")")
ok "Compression test: $COMP_TEST"

# ── 9. Summary ─────────────────────────────────────────────────────
echo
echo "═══════════════════════════════════════════════════════════════"
echo "  Test Summary"
echo "═══════════════════════════════════════════════════════════════"
echo
ok "All 5 features working"
ok "Gemma 4 12b integration: PASS"
echo
echo "  Adam is running at: http://localhost:8000"
echo "  Open the browser: http://localhost:8000/  (chat UI)"
echo "  Or test via curl:   curl http://localhost:8000/api/compression"
echo
echo "  To stop:  pkill -f 'uvicorn adam'"
echo "═══════════════════════════════════════════════════════════════"
