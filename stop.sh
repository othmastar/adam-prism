#!/bin/bash
# ⏹️  إيقاف كل خدمات آدم المنظار

PORTS=(3000 8002 8080)

echo "⏹️  إيقاف خدمات آدم المنظار..."
for PORT in "${PORTS[@]}"; do
  PID=$(lsof -ti :"$PORT" 2>/dev/null)
  if [ -n "$PID" ]; then
    kill "$PID" 2>/dev/null
    echo "  ✅ Port $PORT (PID $PID)"
  else
    echo "  ⏭️  Port $PORT مش شغال"
  fi
done

echo ""
echo "✅ تم إيقاف كل الخدمات"
