#!/bin/bash
# run.sh — كل حاجة بأمر واحد
# Usage: ./run.sh "hf_token"

set -e

HF_TOKEN="${1:-$HF_TOKEN}"
if [ -z "$HF_TOKEN" ]; then
    echo "الاستخدام: ./run.sh 'huggingface_token_here'"
    echo "أو: export HF_TOKEN='token' && ./run.sh"
    exit 1
fi

echo "🚀 ADAM FULL PIPELINE"
echo "======================"

# Step 1: Eval + Merge
echo ""
echo "📊 1/4 — تقييم ودمج البيانات..."
python adam_cloud_pipeline.py

# Step 2: Train
echo ""
echo "🚀 2/4 — تدريب QLoRA..."
python train_lora.py --data final_dataset --hf-token "$HF_TOKEN" --mode train

# Step 3: Merge Adapters
echo ""
echo "🔗 3/4 — دمج LoRA مع base model..."
python train_lora.py --data final_dataset --hf-token "$HF_TOKEN" --mode merge

# Step 4: Ollama
echo ""
echo "📦 4/4 — نشر في Ollama..."
python train_lora.py --mode ollama

echo ""
echo "✅ آدم جاهز!"
echo "شغّل: ollama run adam-prism 'مرحباً آدم'"
