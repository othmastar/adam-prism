#!/usr/bin/env bash
echo "╔══════════════════════════════════════════╗"
echo "║     ADAM PRISM — إيقاف المنظومة          ║"
echo "╚══════════════════════════════════════════╝"

# 1. وقف الخدمات (الترتيب العكسي: UI ← API ← Model)
for port in 3000 8000 7860; do
    pid=$(lsof -ti:$port 2>/dev/null)
    if [ -n "$pid" ]; then
        kill $pid 2>/dev/null && echo "  ✅ أوقف :$port (PID $pid)" || echo "  ⚠️  فشل إيقاف :$port"
    else
        echo "  ➖ :$port — موقوف أصلاً"
    fi
done

# 2. وقف Qdrant (Docker)
if docker ps --format '{{.Names}}' 2>/dev/null | grep -q ^adam-qdrant$; then
    cd "$(cd "$(dirname "$0")" && pwd)"
    docker compose -f deploy/docker-compose.yml down qdrant 2>&1 && echo "  ✅ Qdrant أوقف" || echo "  ⚠️  فشل إيقاف Qdrant"
else
    echo "  ➖ Qdrant — موقوف أصلاً"
fi

echo ""
echo "✅ تم إيقاف Adam Prism — GPU فاضي"
