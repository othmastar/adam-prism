import torch
from transformers import AutoModelForCausalLM, AutoTokenizer
from peft import PeftModel

# السطر ده اللي كان فيه المشكلة.. اتصلح دلوقتى:
base_path = "/mnt/Workspace/.huggingface/hub/models--unsloth--gemma-4-E4B-it-unsloth-bnb-4bit/snapshots/91872ae26ac6bfbae6ee6a8acdc73d3370d1d227"
lora_path = "/mnt/Workspace/adam_v8_output/"

print("🔄 جاري تحميل المحرك الأساسي...")

try:
    # تحميل التوكنايزر والموديل
    tokenizer = AutoTokenizer.from_pretrained(base_path, use_fast=False)
    model = AutoModelForCausalLM.from_pretrained(
        base_path,
        torch_dtype=torch.float16,
        device_map="auto"
    )

    print("🚀 دمج أوزان آدم (v8)...")
    model = PeftModel.from_pretrained(model, lora_path)

    # الدمج النهائي اللي بيحل مشكلة الـ positional argument
    model = model.merge_and_unload() 

    output_path = "/mnt/Workspace/adam_final_engine"
    print(f"💾 حفظ في: {output_path}")
    model.save_pretrained(output_path)
    tokenizer.save_pretrained(output_path)

    print("✅ تم بنجاح يا هندسة!")

except Exception as e:
    print(f"❌ حصل خطأ: {e}")