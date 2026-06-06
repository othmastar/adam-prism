#!/usr/bin/env bash
set -e

ROOT="$(cd "$(dirname "$0")" && pwd)"

echo "╔══════════════════════════════════════════╗"
echo "║     ADAM PRISM — تشغيل المنظومة كاملة     ║"
echo "╚══════════════════════════════════════════╝"

# ─── 0. Qdrant ───
echo ""
echo "[0/4] Qdrant — المتجهات على :6333"
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q ^adam-qdrant$; then
    echo "  ✅ Qdrant شغال بالفعل"
else
    cd "$ROOT"
    docker compose -f deploy/docker-compose.yml up -d qdrant 2>&1
    echo "  ⏳ انتظار Qdrant..."
    for i in $(seq 1 15); do
        if curl -s -o /dev/null -w '' http://localhost:6333/ 2>/dev/null; then
            echo "  ✅ Qdrant جاهز على :6333"
            break
        fi
        if [ $i -eq 15 ]; then echo "  ⚠️ Qdrant لم يستجب — تحقق من docker logs adam-qdrant"; fi
        sleep 1
    done
fi

# ─── 1. Model Server (Qwen3.5-4B + LoRA) ───
MODEL_PID=""
echo ""
echo "[1/4] Model — الموديل على :7860"
MODEL_PID=$(lsof -ti:7860 2>/dev/null)
if [ -n "$MODEL_PID" ]; then
    echo "  ✅ Model شغال بالفعل (PID $MODEL_PID)"
else
    cd /mnt/Workspace/adam_v8_output/Qwen-Adam-AR
    PYTHONPATH="/mnt/Workspace/python-lib/site-packages:$PYTHONPATH" \
    setsid /usr/bin/python3 scripts/flask_chat.py &>/tmp/adam_flask.log &
    MODEL_PID=$!
    echo "  ⏳ PID $MODEL_PID — تحميل الموديل (قد يستغرق دقيقة)..."
    for i in $(seq 1 90); do
        if curl -s -o /dev/null -w '' http://localhost:7860/ 2>/dev/null; then
            echo "  ✅ Model جاهز على :7860"
            break
        fi
        if [ $i -eq 90 ]; then echo "  ⚠️  Model لم يستجب — تحقق من /tmp/adam_flask.log"; fi
        sleep 2
    done
fi

# ─── 2. API Server ───
echo ""
echo "[2/4] API — الخادم على :8000"
API_PID=$(lsof -ti:8000 2>/dev/null)
if [ -n "$API_PID" ]; then
    echo "  ✅ API شغال بالفعل (PID $API_PID)"
else
    cd "$ROOT"
    source venv/bin/activate
    setsid python run_api.py &>/mnt/Workspace/Adam_Prism_Complete_v2/api.log &
    API_PID=$!
    echo "  ⏳ PID $API_PID — انتظار..."
    for i in $(seq 1 15); do
        if curl -s -o /dev/null -w '' http://localhost:8000/ 2>/dev/null; then
            echo "  ✅ API جاهز على :8000"
            break
        fi
        if [ $i -eq 15 ]; then echo "  ⚠️  API لم يستجب — تحقق من api.log"; fi
        sleep 1
    done
fi

# ─── 3. Frontend ───
echo ""
echo "[3/4] UI — الواجهة على :3000"
UI_PID=$(lsof -ti:3000 2>/dev/null)
if [ -n "$UI_PID" ]; then
    echo "  ✅ UI شغال بالفعل (PID $UI_PID)"
else
    cd "$ROOT/web-ui"
    setsid node node_modules/next/dist/bin/next dev -p 3000 &>/mnt/Workspace/Adam_Prism_Complete_v2/frontend.log &
    UI_PID=$!
    echo "  ⏳ PID $UI_PID — انتظار..."
    for i in $(seq 1 30); do
        if curl -s -o /dev/null -w '' http://localhost:3000/ 2>/dev/null; then
            echo "  ✅ UI جاهز على :3000"
            break
        fi
        if [ $i -eq 30 ]; then echo "  ⚠️  UI لم يستجب — تحقق من frontend.log"; fi
        sleep 1
    done
fi

echo ""
echo "╔══════════════════════════════════════════╗"
echo "║  ✅  ADAM PRISM — شغال بالكامل           ║"
echo "╠══════════════════════════════════════════╣"
echo "║  Qdrant :6333  متجهات آدم                ║"
echo "║  Model  :7860  Qwen3.5-4B + LoRA         ║"
echo "║  API    :8000  Adam Prism Engine          ║"
echo "║  UI     :3000  Next.js Frontend           ║"
echo "╠══════════════════════════════════════════╣"
echo "║  افتح:  http://localhost:3000             ║"
echo "╚══════════════════════════════════════════╝"
