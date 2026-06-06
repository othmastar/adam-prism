#!/bin/bash
# ═══════════════════════════════════════════════════════════════
# آدم - سكريبت التثبيت
# Adam - Setup Script
# ═══════════════════════════════════════════════════════════════

set -e

echo "═══════════════════════════════════════════════════════════"
echo "🤖 آدم - LoRA Fine-Tuning Pipeline"
echo "═══════════════════════════════════════════════════════════"
echo ""

# ─── فحص GPU ───
echo "🔍 فحص GPU..."
if command -v nvidia-smi &> /dev/null; then
    GPU_INFO=$(nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null || echo "غير متاح")
    echo "✅ GPU: $GPU_INFO"
else
    echo "⚠️  مش لاقي nvidia-smi - ممكن مفيش GPU"
    echo "   التدريب على CPU مش عملي - استخدم Google Colab"
    echo ""
    read -p "عايز تكمل على أي حال؟ (y/n): " CONTINUE
    if [[ "$CONTINUE" != "y" ]]; then
        echo "👋 شغّل colab_notebook.py للتدريب على Colab"
        exit 0
    fi
fi

# ─── فحص Python ───
echo ""
echo "🔍 فحص Python..."
if command -v python3 &> /dev/null; then
    PY_VER=$(python3 --version)
    echo "✅ $PY_VER"
else
    echo "❌ Python3 مش مثبت"
    exit 1
fi

# ─── إنشاء venv ───
echo ""
echo "📦 إنشاء البيئة الافتراضية..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✅ تم إنشاء venv"
else
    echo "✅ venv موجود بالفعل"
fi

# تفعيل venv
source venv/bin/activate

# ترقية pip
echo ""
echo "📦 ترقية pip..."
pip install --upgrade pip -q

# ─── تثبيت المتطلبات ───
echo ""
echo "📦 تثبيت المتطلبات..."
echo "   ⏱️ ده هياخد شوية دقايق..."

# PyTorch أولاً (مع CUDA)
echo "   - PyTorch..."
if python3 -c "import torch; print(torch.cuda.is_available())" 2>/dev/null | grep -q "True"; then
    echo "   ✅ PyTorch مثبت بالفعل مع CUDA"
else
    pip install torch --index-url https://download.pytorch.org/whl/cu121 -q 2>/dev/null || \
    pip install torch -q
    echo "   ✅ تم تثبيت PyTorch"
fi

# Unsloth والباقي
echo "   - Unsloth + PEFT + TRL..."
pip install -r requirements.txt -q 2>/dev/null || {
    # تثبيت يدوي لو requirements.txt فشل
    pip install unsloth -q 2>/dev/null || pip install peft trl accelerate bitsandbytes -q
    pip install datasets pyyaml rich -q
}

echo "   ✅ تم تثبيت المكتبات"

# ─── فحص التثبيت ───
echo ""
echo "🔍 فحص التثبيت..."
python3 -c "
try:
    import torch
    has_cuda = torch.cuda.is_available()
    print(f'  PyTorch: {torch.__version__} (CUDA: {has_cuda})')
except ImportError:
    print('  ❌ PyTorch مش مثبت')

try:
    import transformers
    print(f'  Transformers: {transformers.__version__}')
except ImportError:
    print('  ❌ Transformers مش مثبت')

try:
    import peft
    print(f'  PEFT: {peft.__version__}')
except ImportError:
    print('  ❌ PEFT مش مثبت')

try:
    import trl
    print(f'  TRL: {trl.__version__}')
except ImportError:
    print('  ❌ TRL مش مثبت')

try:
    from unsloth import FastLanguageModel
    print('  Unsloth: ✅')
except ImportError:
    print('  ⚠️  Unsloth مش مثبت - هيتم استخدام PEFT كبديل')
"

# ─── إنشاء بيانات مثال ───
echo ""
echo "📊 تجهيز بيانات المثال..."
if [ ! -f "data/training_data.jsonl" ]; then
    python3 prepare_data.py --create-example
    echo "✅ تم إنشاء بيانات مثال"
else
    echo "✅ بيانات التدريب موجودة بالفعل"
fi

# ─── النتيجة ───
echo ""
echo "═══════════════════════════════════════════════════════════"
echo "🎉 التثبيت انتهى!"
echo "═══════════════════════════════════════════════════════════"
echo ""
echo "📌 الأوامر المتاحة:"
echo ""
echo "  # تدريب بـ Unsloth (الأسرع):"
echo "  source venv/bin/activate"
echo "  python3 train.py --method unsloth --steps 100"
echo ""
echo "  # تدريب بـ PEFT (بديل):"
echo "  python3 train.py --method peft --steps 100"
echo ""
echo "  # فحص GPU:"
echo "  python3 train.py --check-gpu"
echo ""
echo "  # تجهيز بياناتك:"
echo "  python3 prepare_data.py --create-example"
echo "  python3 prepare_data.py --validate ./data/training_data.jsonl"
echo ""
echo "  # اختبار بعد التدريب:"
echo "  python3 chat.py --model ./output/adam-lora/adam-merged"
echo ""
echo "  # تصدير لـ Ollama:"
echo "  python3 export_gguf.py --model ./output/adam-lora/adam-merged --register"
echo ""
echo "  # لو مش عندك GPU:"
echo "  python3 colab_notebook.py   # يولّد notebook لـ Google Colab"
echo ""
echo "💬 بعد التصدير: ollama run adam"
