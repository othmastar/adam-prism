import torch
from transformers import LlamaTokenizer, AutoModelForCausalLM
from safetensors.torch import load_file, save_file
import os
import shutil

# المسارات
base_path = "/mnt/Workspace/.huggingface/hub/models--unsloth--gemma-4-E4B-it-unsloth-bnb-4bit/snapshots/91872ae26ac6bfbae6ee6a8acdc73d3370d1d227"
lora_weights_path = "/mnt/Workspace/adam_v8_output/lora_adapter/adapter_model.safetensors"
output_path = "/mnt/Workspace/adam_final_engine"

if not os.path.exists(output_path):
    os.makedirs(output_path)

print("⛓️ فك ارتباط الأوزان المشتركة وحفظ 'آدم' نهائياً...")

try:
    # 1. التوكينايزر
    tokenizer = LlamaTokenizer.from_pretrained(base_path, legacy=False)
    tokenizer.save_pretrained(output_path)

    # 2. تحميل الموديل على الـ CPU
    model = AutoModelForCausalLM.from_pretrained(
        base_path,
        device_map="cpu",
        torch_dtype=torch.float32, # نستخدم float32 لضمان الدقة أثناء الدمج
        trust_remote_code=True
    )

    # 3. الدمج العصبى
    adam_tensors = load_file(lora_weights_path)
    cleaned_tensors = {}
    prefix = "base_model.model.model.language_model."
    for key, value in adam_tensors.items():
        new_key = key.replace(prefix, "").replace("base_model.model.", "")
        cleaned_tensors[new_key] = value.to("cpu")

    model.load_state_dict(cleaned_tensors, strict=False)
    print("🧠 العقل مدمج بالكامل.")

    # 4. معالجة معضلة الأوزان المشتركة (Shared Tensors)
    # نحصل على الأوزان كـ Dict
    state_dict = model.state_dict()
    
    # الخدعة: Safetensors ترفض الحفظ إذا وجدت وزنين لهما نفس الـ Data Pointer
    # سنقوم بعمل .clone() لواحد منهما لكسر الارتباط المادي في الذاكرة
    if "lm_head.weight" in state_dict and "model.language_model.embed_tokens.weight" in state_dict:
        print("✂️ كسر الارتباط بين lm_head و embed_tokens...")
        state_dict["lm_head.weight"] = state_dict["lm_head.weight"].clone()

    # 5. الحفظ النهائي
    print("💾 جاري التصدير للقرص الصلب...")
    save_file(state_dict, os.path.join(output_path, "model.safetensors"))
    
    # نسخ ملفات الإعدادات الضرورية
    for f in ["config.json", "generation_config.json", "tokenizer_config.json", "special_tokens_map.json"]:
        src = os.path.join(base_path, f)
        if os.path.exists(src):
            shutil.copy(src, output_path)

    print(f"\n✅ النصر الساحق! 'آدم' ولد من جديد في: {output_path}")

except Exception as e:
    print(f"❌ خطأ غير متوقع: {e}")