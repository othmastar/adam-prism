#!/bin/bash
# آدم المنظار — تشغيل كل الخدمات
set -e

export HF_HOME="/mnt/Workspace/.huggingface"
export PYTORCH_CUDA_ALLOC_CONF="expandable_segments:True"
export TOKENIZERS_PARALLELISM="false"
export NO_HF_DOWNLOAD="1"

ROOT="/mnt/Workspace/Adam_Prism_Complete_v2"
LORA_VENV="/mnt/Workspace/جيما 4 12 مليار/.venv/bin/python3"
LORA_PORT=8080
API_PORT=8002
FRONTEND_PORT=3000

echo "=== آدم المنظار — Startup ==="

# 1) LoRA Inference Server
echo "[1/3] LoRA Server (port $LORA_PORT)..."
setsid $LORA_VENV python "$ROOT/scripts/inference_server.py" > /tmp/lora-server.log 2>&1 &
LORA_PID=$!
echo "  PID: $LORA_PID"

# Wait for LoRA to be ready
for i in $(seq 1 60); do
  if curl -s --max-time 2 "http://localhost:$LORA_PORT/health" 2>/dev/null | grep -q "ok"; then
    echo "  ✅ LoRA ready"
    break
  fi
  if [ $i -eq 60 ]; then
    echo "  ❌ LoRA failed to start"
    tail -5 /tmp/lora-server.log
    exit 1
  fi
  sleep 2
done

# 2) API Server
echo "[2/3] API Server (port $API_PORT)..."
setsid python3 "$ROOT/main.py" --port $API_PORT > /tmp/main-api.log 2>&1 &
API_PID=$!
echo "  PID: $API_PID"

for i in $(seq 1 30); do
  if curl -s --max-time 2 "http://localhost:$API_PORT/api/status" 2>/dev/null | grep -q "lora"; then
    echo "  ✅ API ready"
    break
  fi
  if [ $i -eq 30 ]; then
    echo "  ❌ API failed to start"
    tail -5 /tmp/main-api.log
    exit 1
  fi
  sleep 1
done

# 3) Frontend
echo "[3/3] Frontend (port $FRONTEND_PORT)..."
cd "$ROOT/frontend/web-ui" || exit 1
setsid npx next dev -p $FRONTEND_PORT > /tmp/frontend.log 2>&1 &
FE_PID=$!
echo "  PID: $FE_PID"

for i in $(seq 1 20); do
  if curl -s --max-time 2 "http://localhost:$FRONTEND_PORT" 2>/dev/null | grep -q "html"; then
    echo "  ✅ Frontend ready"
    break
  fi
  if [ $i -eq 20 ]; then
    echo "  ❌ Frontend failed to start"
    tail -5 /tmp/frontend.log
    exit 1
  fi
  sleep 1
done

echo ""
echo "=== All Services Running ==="
echo "  Frontend:  http://localhost:$FRONTEND_PORT  (PID $FE_PID)"
echo "  API:       http://localhost:$API_PORT       (PID $API_PID)"
echo "  LoRA:      http://localhost:$LORA_PORT       (PID $LORA_PID)"
echo ""
echo "  Logs: /tmp/lora-server.log / /tmp/main-api.log / /tmp/frontend.log"
echo "  Stop: kill $FE_PID $API_PID $LORA_PID"