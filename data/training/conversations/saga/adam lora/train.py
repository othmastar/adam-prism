#!/usr/bin/env python3
"""
آدم - سكريبت التدريب بـ LoRA
Adam - LoRA Fine-Tuning Training Script

يدعم طريقتين:
1. Unsloth (أسرع 2-5x، أقل في الذاكرة) - يُنصح به
2. HuggingFace PEFT (يعمل مع أي موديل) - fallback

المتطلبات:
- GPU بذاكرة 8GB على الأقل (أو Google Colab T4 مجاني)
- أو استئجار GPU من Vast.ai / RunPod
"""

import os
import sys
import json
import yaml
import argparse
import time
from pathlib import Path
from datetime import datetime

# ═══════════════════════════════════════════════════════════════
# إعدادات التدريب الافتراضية
# ═══════════════════════════════════════════════════════════════

DEFAULT_CONFIG = {
    # الموديل الأساسي
    "base_model": "unsloth/gemma-2-2b-it",  # أو أي موديل HuggingFace
    # أسماء موديلات بديلة:
    # "unsloth/gemma-2-9b-it"        - أقوى بس محتاج 16GB VRAM
    # "unsloth/Qwen2.5-3B-Instruct"  - بديل قوي
    # "unsloth/Qwen2.5-7B-Instruct"  - أقوى بس محتاج 16GB VRAM
    # "unsloth/Meta-Llama-3.1-8B-Instruct" - محتاج 16GB VRAM

    # إعدادات LoRA
    "lora_r": 16,           # رتبة LoRA - أعلى = تعلم أكثر بس ذاكرة أكثر (8, 16, 32, 64)
    "lora_alpha": 16,       # عادة = lora_r
    "lora_dropout": 0,      # 0 = أفضل مع LoRA
    "target_modules": [
        "q_proj", "k_proj", "v_proj", "o_proj",
        "gate_proj", "up_proj", "down_proj"
    ],

    # إعدادات التدريب
    "max_seq_length": 2048,  # أقصى طول للتسلسل
    "per_device_train_batch_size": 2,
    "gradient_accumulation_steps": 4,  # batch_size فعلي = 2 × 4 = 8
    "warmup_steps": 10,
    "max_steps": 100,        # عدد خطوات التدريب - زوّد لو عندك بيانات كتير
    "learning_rate": 2e-4,
    "weight_decay": 0.01,
    "lr_scheduler_type": "cosine",
    "seed": 3407,

    # الدقة
    "fp16": False,
    "bf16": True,            # استخدم True لو GPU يدعم (Ampere+)

    # الحفظ
    "output_dir": "./output/adam-lora",
    "save_steps": 25,
    "logging_steps": 1,

    # البيانات
    "data_path": "./data/training_data.jsonl",
    "data_format": "sharegpt",  # "sharegpt" أو "alpaca"

    # النظام
    "system_prompt": "أنت آدم، المساعد الشخصي لأسامة. خبير في هندسة الاتصالات والبرمجة. تتجاوب بالعربي أو الإنجليزي حسب السؤال. صريح، عملي، ومختصر.",
}


# ═══════════════════════════════════════════════════════════════
# تحميل البيانات
# ═══════════════════════════════════════════════════════════════

def load_training_data(data_path: str, data_format: str = "sharegpt"):
    """تحميل بيانات التدريب من ملف JSONL"""

    if not os.path.exists(data_path):
        print(f"❌ ملف البيانات مش موجود: {data_path}")
        print(f"📌 شغّل prepare_data.py الأول لتحضير البيانات")
        sys.exit(1)

    data = []
    with open(data_path, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if line:
                data.append(json.loads(line))

    print(f"✅ تم تحميل {len(data)} مثال تدريبي من {data_path}")

    # التحقق من صحة البيانات
    valid = 0
    for i, item in enumerate(data):
        if data_format == "sharegpt":
            if "conversations" in item:
                valid += 1
            else:
                print(f"⚠️ مثال {i}: مش شكل ShareGPT - فيه 'conversations'؟")
        elif data_format == "alpaca":
            if "instruction" in item and "output" in item:
                valid += 1
            else:
                print(f"⚠️ مثال {i}: مش شكل Alpaca - فيه 'instruction' و 'output'?")

    print(f"✅ {valid}/{len(data)} مثال صالح للتدريب")
    return data


# ═══════════════════════════════════════════════════════════════
# الطريقة الأولى: Unsloth (الأسرع - يُنصح بها)
# ═══════════════════════════════════════════════════════════════

def train_with_unsloth(config: dict):
    """تدريب بـ Unsloth - أسرع 2-5x وأقل في الذاكرة"""

    try:
        from unsloth import FastLanguageModel
        from trl import SFTTrainer
        from transformers import TrainingArguments
    except ImportError:
        print("❌ Unsloth مش مثبت. حاول:")
        print("   pip install unsloth")
        print("   أو استخدم --method peft للتدريب بالطريقة العادية")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🚀 تدريب آدم بـ Unsloth (الطريقة السريعة)")
    print("=" * 60)

    # تحميل الموديل
    print(f"\n📥 تحميل الموديل: {config['base_model']}")
    print(f"   max_seq_length = {config['max_seq_length']}")
    print(f"   load_in_4bit = True (توفير الذاكرة)")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=config["base_model"],
        max_seq_length=config["max_seq_length"],
        dtype=None,  # auto-detect
        load_in_4bit=True,
    )

    # إضافة LoRA adapters
    print(f"\n🔧 إضافة LoRA adapters:")
    print(f"   r = {config['lora_r']}")
    print(f"   alpha = {config['lora_alpha']}")
    print(f"   target_modules = {config['target_modules']}")

    model = FastLanguageModel.get_peft_model(
        model,
        r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        target_modules=config["target_modules"],
        bias="none",
        use_gradient_checkpointing="unsloth",  # ذاكرة أقل
        random_state=config["seed"],
    )

    # تحميل البيانات
    data = load_training_data(config["data_path"], config["data_format"])

    # تحضير البيانات بصيغة التدريب
    def formatting_func(examples):
        texts = []
        for conv in examples["conversations"]:
            # بناء النص من المحادثة
            text = tokenizer.apply_chat_template(
                conv,
                tokenize=False,
                add_generation_prompt=False,
            )
            texts.append(text)
        return {"text": texts}

    # تحويل البيانات لـ Dataset
    from datasets import Dataset

    if config["data_format"] == "sharegpt":
        # ShareGPT format
        conversations_list = []
        for item in data:
            conversations_list.append(item["conversations"])
        dataset = Dataset.from_dict({"conversations": conversations_list})
    else:
        # Alpaca format - تحويل لـ ShareGPT
        conversations_list = []
        for item in data:
            conv = []
            if config.get("system_prompt"):
                conv.append({"role": "system", "content": config["system_prompt"]})
            conv.append({"role": "user", "content": item["instruction"]})
            if item.get("input"):
                conv[-1]["content"] += f"\n\n{item['input']}"
            conv.append({"role": "assistant", "content": item["output"]})
            conversations_list.append(conv)
        dataset = Dataset.from_dict({"conversations": conversations_list})

    print(f"\n📊 حجم الداتا: {len(dataset)} مثال")

    # إعدادات التدريب
    training_args = TrainingArguments(
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        warmup_steps=config["warmup_steps"],
        max_steps=config["max_steps"],
        learning_rate=config["learning_rate"],
        weight_decay=config["weight_decay"],
        lr_scheduler_type=config["lr_scheduler_type"],
        seed=config["seed"],
        fp16=config["fp16"],
        bf16=config["bf16"],
        logging_steps=config["logging_steps"],
        save_steps=config["save_steps"],
        output_dir=config["output_dir"],
        report_to="none",  # لو عايز wandb غيّرها
    )

    # إنشاء Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        formatting_func=formatting_func,
        max_seq_length=config["max_seq_length"],
        args=training_args,
    )

    # بدء التدريب
    print(f"\n🏋️ بدء التدريب:")
    print(f"   max_steps = {config['max_steps']}")
    print(f"   batch_size = {config['per_device_train_batch_size']} × {config['gradient_accumulation_steps']} = {config['per_device_train_batch_size'] * config['gradient_accumulation_steps']}")
    print(f"   learning_rate = {config['learning_rate']}")
    print()

    start_time = time.time()
    trainer.train()
    elapsed = time.time() - start_time

    print(f"\n⏱️ وقت التدريب: {elapsed/60:.1f} دقيقة")

    # حفظ الـ LoRA adapter
    adapter_path = os.path.join(config["output_dir"], "adam-lora-adapter")
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"✅ تم حفظ LoRA adapter في: {adapter_path}")

    # حفظ كموديل كامل (merged)
    merged_path = os.path.join(config["output_dir"], "adam-merged")
    model.save_pretrained_merged(merged_path, tokenizer, save_method="merged_16bit")
    print(f"✅ تم حفظ الموديل المدمج في: {merged_path}")

    return adapter_path, merged_path


# ═══════════════════════════════════════════════════════════════
# الطريقة الثانية: HuggingFace PEFT (يعمل مع أي موديل)
# ═══════════════════════════════════════════════════════════════

def train_with_peft(config: dict):
    """تدريب بـ HuggingFace PEFT - طريقة عامة تعمل مع أي موديل"""

    try:
        import torch
        from transformers import (
            AutoModelForCausalLM,
            AutoTokenizer,
            TrainingArguments,
            BitsAndBytesConfig,
        )
        from peft import LoraConfig, get_peft_model, TaskType
        from trl import SFTTrainer
        from datasets import Dataset
    except ImportError as e:
        print(f"❌ مكتبة ناقصة: {e}")
        print("   pip install torch transformers peft trl datasets bitsandbytes")
        sys.exit(1)

    print("\n" + "=" * 60)
    print("🚀 تدريب آدم بـ HuggingFace PEFT")
    print("=" * 60)

    # إعدادات الكمية (Quantization) لتوفير الذاكرة
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )

    # تحميل الموديل
    print(f"\n📥 تحميل الموديل: {config['base_model']}")
    tokenizer = AutoTokenizer.from_pretrained(config["base_model"])
    tokenizer.pad_token = tokenizer.eos_token
    tokenizer.padding_side = "right"

    model = AutoModelForCausalLM.from_pretrained(
        config["base_model"],
        quantization_config=bnb_config,
        device_map="auto",
        attn_implementation="eager",
    )

    # إعداد LoRA
    lora_config = LoraConfig(
        r=config["lora_r"],
        lora_alpha=config["lora_alpha"],
        lora_dropout=config["lora_dropout"],
        target_modules=config["target_modules"],
        bias="none",
        task_type=TaskType.CAUSAL_LM,
    )

    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    # تحميل البيانات
    data = load_training_data(config["data_path"], config["data_format"])

    # تحضير البيانات
    def format_to_text(item):
        """تحويل مثال واحد لنص تدريبي"""
        if config["data_format"] == "sharegpt" and "conversations" in item:
            text = tokenizer.apply_chat_template(
                item["conversations"],
                tokenize=False,
                add_generation_prompt=False,
            )
        else:
            # Alpaca format
            instruction = item.get("instruction", "")
            input_text = item.get("input", "")
            output = item.get("output", "")
            prompt = f"### Instruction:\n{instruction}\n"
            if input_text:
                prompt += f"### Input:\n{input_text}\n"
            prompt += f"### Response:\n{output}"
            text = prompt
        return text

    texts = [format_to_text(item) for item in data]
    dataset = Dataset.from_dict({"text": texts})

    # إعدادات التدريب
    training_args = TrainingArguments(
        per_device_train_batch_size=config["per_device_train_batch_size"],
        gradient_accumulation_steps=config["gradient_accumulation_steps"],
        warmup_steps=config["warmup_steps"],
        max_steps=config["max_steps"],
        learning_rate=config["learning_rate"],
        weight_decay=config["weight_decay"],
        lr_scheduler_type=config["lr_scheduler_type"],
        seed=config["seed"],
        fp16=config["fp16"],
        bf16=config["bf16"],
        logging_steps=config["logging_steps"],
        save_steps=config["save_steps"],
        output_dir=config["output_dir"],
        report_to="none",
        optim="paged_adamw_8bit",  # توفير الذاكرة
    )

    # إنشاء Trainer
    trainer = SFTTrainer(
        model=model,
        tokenizer=tokenizer,
        train_dataset=dataset,
        max_seq_length=config["max_seq_length"],
        args=training_args,
    )

    # بدء التدريب
    print(f"\n🏋️ بدء التدريب...")
    start_time = time.time()
    trainer.train()
    elapsed = time.time() - start_time
    print(f"\n⏱️ وقت التدريب: {elapsed/60:.1f} دقيقة")

    # حفظ
    adapter_path = os.path.join(config["output_dir"], "adam-lora-adapter")
    model.save_pretrained(adapter_path)
    tokenizer.save_pretrained(adapter_path)
    print(f"✅ تم حفظ LoRA adapter في: {adapter_path}")

    return adapter_path, None  # PEFT لا يدمج تلقائياً


# ═══════════════════════════════════════════════════════════════
# تصدير GGUF لـ Ollama
# ═══════════════════════════════════════════════════════════════

def export_gguf(merged_path: str, output_name: str = "adam"):
    """تصدير الموديل المدمج كـ GGUF لتشغيله على Ollama"""

    try:
        from unsloth import FastLanguageModel
    except ImportError:
        print("❌ التصدير يحتاج Unsloth")
        print("   pip install unsloth")
        return None

    print(f"\n📦 تصدير GGUF من: {merged_path}")

    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=merged_path,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=False,
    )

    # حفظ بأكتر من صيغة
    gguf_path = f"./output/{output_name}"

    # Q4_K_M - الأفضل للتوازن بين الحجم والجودة
    model.save_pretrained_gguf(gguf_path, tokenizer, quantization_method="q4_k_m")
    print(f"✅ Q4_K_M: {gguf_path}/unsloth.Q4_K_M.gguf")

    # Q8_0 - جودة أعلى بس حجم أكبر
    model.save_pretrained_gguf(
        gguf_path + "-q8", tokenizer, quantization_method="q8_0"
    )
    print(f"✅ Q8_0: {gguf_path}-q8/unsloth.Q8_0.gguf")

    return gguf_path


# ═══════════════════════════════════════════════════════════════
# إنشاء Modelfile لـ Ollama
# ═══════════════════════════════════════════════════════════════

def create_ollama_model(gguf_path: str, model_name: str = "adam"):
    """إنشاء Modelfile وتسجيل الموديل في Ollama"""

    modelfile_content = f'''FROM {gguf_path}/unsloth.Q4_K_M.gguf

TEMPLATE """{{{{- if .System }}}}<start_of_turn>user
{{{{.System }}}}<end_of_turn>
{{{{- end }}}}
<start_of_turn>user
{{{{.Prompt }}}}<end_of_turn>
<start_of_turn>model
{{{{.Response }}}}<end_of_turn>"""

SYSTEM """أنت آدم، المساعد الشخصي لأسامة. خبير في هندسة الاتصالات والبرمجة. تتجاوب بالعربي أو الإنجليزي حسب السؤال. صريح، عملي، ومختصر."""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 50
PARAMETER num_ctx 4096
'''

    modelfile_path = f"./output/Modelfile.{model_name}"
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile_content)

    print(f"\n📝 تم إنشاء Modelfile: {modelfile_path}")
    print(f"\n🚀 لتسجيل الموديل في Ollama:")
    print(f"   ollama create {model_name} -f {modelfile_path}")
    print(f"\n💬 للتشغيل:")
    print(f"   ollama run {model_name}")

    return modelfile_path


# ═══════════════════════════════════════════════════════════════
# تشخيص GPU
# ═══════════════════════════════════════════════════════════════

def check_gpu():
    """فحص GPU المتاحة"""

    print("\n" + "=" * 60)
    print("🔍 فحص الأجهزة")
    print("=" * 60)

    try:
        import torch
        if torch.cuda.is_available():
            gpu_name = torch.cuda.get_device_name(0)
            gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1e9
            print(f"✅ GPU: {gpu_name}")
            print(f"   VRAM: {gpu_mem:.1f} GB")

            if gpu_mem < 8:
                print("⚠️  VRAM أقل من 8GB - التدريب هيكون صعب")
                print("   يُنصح باستخدام Google Colab (T4 GPU مجاني)")
            elif gpu_mem < 16:
                print("✅ مناسب لموديلات 2B-4B مع QLoRA")
            else:
                print("✅ ممتاز - يقدر يدرب موديلات لحد 9B")

            return True
        else:
            print("❌ مش لاقي GPU - التدريب على CPU مش عملي")
            print("\n📌 الخيارات المتاحة:")
            print("   1. Google Colab (T4 GPU مجاني) - النسخة واللصق")
            print("   2. Kaggle (P100/T4 GPU مجاني)")
            print("   3. Vast.ai (~$0.20/sاعة)")
            print("   4. RunPod (~$0.40/sاعة)")
            return False
    except ImportError:
        print("❌ PyTorch مش مثبت")
        return False


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="آدم - تدريب LoRA")
    parser.add_argument("--config", type=str, default=None, help="ملف YAML بالإعدادات")
    parser.add_argument("--method", type=str, default="unsloth", choices=["unsloth", "peft"],
                        help="طريقة التدريب: unsloth (أسرع) أو peft (عام)")
    parser.add_argument("--data", type=str, default=None, help="ملف البيانات JSONL")
    parser.add_argument("--model", type=str, default=None, help="اسم الموديل الأساسي")
    parser.add_argument("--steps", type=int, default=None, help="عدد خطوات التدريب")
    parser.add_argument("--export-gguf", action="store_true", help="تصدير GGUF بعد التدريب")
    parser.add_argument("--check-gpu", action="store_true", help="فحص GPU بس")
    parser.add_argument("--lora-r", type=int, default=None, help="رتبة LoRA (8, 16, 32, 64)")
    parser.add_argument("--max-seq", type=int, default=None, help="أقصى طول تسلسل")

    args = parser.parse_args()

    # تحميل الإعدادات
    config = DEFAULT_CONFIG.copy()

    if args.config and os.path.exists(args.config):
        with open(args.config, 'r') as f:
            user_config = yaml.safe_load(f)
            config.update(user_config)

    # تطبيق arguments من سطر الأوامر
    if args.data:
        config["data_path"] = args.data
    if args.model:
        config["base_model"] = args.model
    if args.steps:
        config["max_steps"] = args.steps
    if args.lora_r:
        config["lora_r"] = args.lora_r
        config["lora_alpha"] = args.lora_r  # alpha = r عادةً
    if args.max_seq:
        config["max_seq_length"] = args.max_seq

    # فحص GPU
    if args.check_gpu:
        check_gpu()
        return

    # فحص GPU قبل التدريب
    if not check_gpu():
        print("\n❌ لازم يكون عندك GPU عشان التدريب")
        print("   شغّل --check-gpu عشان تشوف الخيارات المتاحة")
        sys.exit(1)

    # التدريب
    if args.method == "unsloth":
        adapter_path, merged_path = train_with_unsloth(config)
    else:
        adapter_path, merged_path = train_with_peft(config)

    # تصدير GGUF
    if args.export_gguf and merged_path:
        gguf_path = export_gguf(merged_path)
        if gguf_path:
            create_ollama_model(gguf_path)
    elif args.export_gguf and not merged_path:
        print("\n⚠️  التصدير لـ GGuf يحتاج Unsloth أو دمج يدوي")
        print("   شغّل export_gguf.py بشكل منفصل بعد الدمج")

    print("\n" + "=" * 60)
    print("🎉 انتهى التدريب!")
    print("=" * 60)
    print(f"\n📁 LoRA Adapter: {adapter_path}")
    if merged_path:
        print(f"📁 الموديل المدمج: {merged_path}")
    print(f"\n📌 الخطوة الجاية:")
    print(f"   1. اختبر الموديل: python chat.py --model {adapter_path}")
    print(f"   2. صدّره لـ Ollama: python export_gguf.py --model {merged_path}")
    print(f"   3. شغّله: ollama run adam")


if __name__ == "__main__":
    main()
