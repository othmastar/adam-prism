#!/bin/bash
# Adam Prism - سكريبت التثبيت التلقائي
# ========================================

set -e

echo "═══════════════════════════════════════════════"
echo "  آدم بريزم - التثبيت التلقائي"
echo "  Adam Prism - Automatic Setup"
echo "═══════════════════════════════════════════════"
echo ""

# 1. فحص المتطلبات
echo "🔍 [1/6] فحص المتطلبات..."

if command -v python3 &> /dev/null; then
    echo "  ✅ Python3: $(python3 --version)"
else
    echo "  ❌ Python3 غير مثبت. ثبته أولاً."
    exit 1
fi

if command -v docker &> /dev/null; then
    echo "  ✅ Docker: $(docker --version)"
else
    echo "  ⚠️  Docker غير مثبت. Qdrant يحتاج Docker."
fi

if command -v ollama &> /dev/null; then
    echo "  ✅ Ollama: مثبت"
else
    echo "  ⚠️  Ollama غير مثبت. ثبته من: https://ollama.com"
fi

echo ""

# 2. إنشاء البيئة الافتراضية
echo "🐍 [2/6] إنشاء البيئة الافتراضية..."
python3 -m venv venv
source venv/bin/activate
echo "  ✅ تم إنشاء البيئة الافتراضية"
echo ""

# 3. تثبيت المتطلبات
echo "📦 [3/6] تثبيت متطلبات Python..."
pip install --upgrade pip
pip install -r requirements.txt
echo "  ✅ تم تثبيت المتطلبات"
echo ""

# 4. تثبيت Playwright
echo "🌐 [4/6] تثبيت Playwright..."
playwright install chromium 2>/dev/null || echo "  ⚠️  Playwright: ثبته يدوياً: playwright install chromium"
echo ""

# 5. تحميل نماذج Ollama
echo "🧠 [5/6] تحميل نماذج Ollama..."
if command -v ollama &> /dev/null; then
    echo "  تحميل gemma3:4b (حوالي 3GB)..."
    ollama pull gemma3:4b || echo "  ⚠️  فشل التحميل. حمّله يدوياً: ollama pull gemma3:4b"
    
    echo "  تحميل nomic-embed-text (حوالي 274MB)..."
    ollama pull nomic-embed-text || echo "  ⚠️  فشل التحميل. حمّله يدوياً: ollama pull nomic-embed-text"
else
    echo "  ⚠️  Ollama غير مثبت. ثبته من: https://ollama.com"
fi
echo ""

# 6. تشغيل Qdrant
echo "🗄️ [6/6] تشغيل Qdrant..."
if command -v docker &> /dev/null; then
    if docker ps | grep -q qdrant; then
        echo "  ✅ Qdrant يعمل بالفعل"
    else
        docker run -d \
            --name qdrant \
            -p 6333:6333 \
            -p 6334:6334 \
            -v "$(pwd)/qdrant_data:/qdrant/storage" \
            qdrant/qdrant:latest 2>/dev/null || echo "  ⚠️  فشل تشغيل Qdrant. شغّله يدوياً."
        echo "  ✅ تم تشغيل Qdrant"
    fi
else
    echo "  ⚠️  Docker غير مثبت. ثبته لتشغيل Qdrant."
fi
echo ""

# إنشاء المجلدات
mkdir -p notebook/daily notebook/connections notebook/pending notebook/summaries
mkdir -p knowledge/qdrant_data

echo "═══════════════════════════════════════════════"
echo "  ✅ التثبيت اكتمل!"
echo ""
echo "  للتشغيل:"
echo "    source venv/bin/activate"
echo "    python main.py"
echo ""
echo "  الواجهة: http://localhost:3000"
echo "  API: http://localhost:8000"
echo "═══════════════════════════════════════════════"
