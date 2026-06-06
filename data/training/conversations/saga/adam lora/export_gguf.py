#!/usr/bin/env python3
"""
آدم - تصدير الموديل لـ Ollama
Adam - Export to Ollama GGUF

يحوّل الموديل المُدرَّب لصيغة GGUF عشان يشتغل على Ollama
"""

import os
import sys
import json
import argparse
import subprocess


def export_with_unsloth(model_path: str, output_name: str = "adam", quantization: str = "q4_k_m"):
    """تصدير الموديل المدمج كـ GGUF باستخدام Unsloth"""

    try:
        from unsloth import FastLanguageModel
    except ImportError:
        print("❌ Unsloth مش مثبت")
        print("   pip install unsloth")
        sys.exit(1)

    print(f"\n📥 تحميل الموديل: {model_path}")
    model, tokenizer = FastLanguageModel.from_pretrained(
        model_name=model_path,
        max_seq_length=2048,
        dtype=None,
        load_in_4bit=False,
    )

    output_dir = f"./output/{output_name}-gguf"
    os.makedirs(output_dir, exist_ok=True)

    print(f"\n📦 تصدير بصيغة {quantization}...")
    model.save_pretrained_gguf(output_dir, tokenizer, quantization_method=quantization)

    # البحث عن ملف GGUF
    gguf_files = [f for f in os.listdir(output_dir) if f.endswith('.gguf')]
    if not gguf_files:
        print("❌ ملف GGUF مش موجود بعد التصدير")
        return None

    gguf_path = os.path.join(output_dir, gguf_files[0])
    file_size_mb = os.path.getsize(gguf_path) / (1024 * 1024)

    print(f"✅ تم التصدير: {gguf_path}")
    print(f"   الحجم: {file_size_mb:.0f} MB")

    return gguf_path


def export_with_llamacpp(model_path: str, output_name: str = "adam", quantization: str = "Q4_K_M"):
    """تصدير باستخدام llama.cpp (طريقة بديلة)"""

    # أولاً: تحويل لـ GGUF (F16)
    print(f"\n📥 تحويل الموديل لـ GGUF...")

    output_dir = f"./output/{output_name}-gguf"
    os.makedirs(output_dir, exist_ok=True)

    # استخراج أسماء الملفات
    model_file = os.path.join(model_path, "model")
    if not os.path.exists(model_file):
        # البحث عن ملف safetensors
        safetensors = [f for f in os.listdir(model_path) if f.endswith('.safetensors')]
        if safetensors:
            model_file = os.path.join(model_path, safetensors[0])
        else:
            print(f"❌ مش لاقي ملف الموديل في {model_path}")
            return None

    # استخدام convert_hf_to_gguf.py من llama.cpp
    try:
        result = subprocess.run(
            ["python", "-m", "llama_cpp.convert_hf_to_gguf", model_path, "--outfile", f"{output_dir}/model-f16.gguf", "--outtype", "f16"],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            print(f"❌ فشل التحويل: {result.stderr}")
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ llama.cpp مش مثبت أو مش في PATH")
        print("   جرّب: pip install llama-cpp-python[server]")
        return None

    f16_path = f"{output_dir}/model-f16.gguf"

    # ثانياً: Quantization
    print(f"\n📦 ضغط بصيغة {quantization}...")
    quant_path = f"{output_dir}/model-{quantization.lower()}.gguf"

    try:
        result = subprocess.run(
            ["llama-quantize", f16_path, quant_path, quantization],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode != 0:
            print(f"❌ فشل الضغط: {result.stderr}")
            return None
    except (subprocess.TimeoutExpired, FileNotFoundError):
        print("❌ llama-quantize مش موجود")
        return None

    # حذف F16 المؤقت
    os.remove(f16_path)

    file_size_mb = os.path.getsize(quant_path) / (1024 * 1024)
    print(f"✅ تم التصدير: {quant_path}")
    print(f"   الحجم: {file_size_mb:.0f} MB")

    return quant_path


def create_modelfile(gguf_path: str, model_name: str = "adam", system_prompt: str = ""):
    """إنشاء Modelfile لـ Ollama"""

    if not system_prompt:
        system_prompt = "أنت آدم، المساعد الشخصي لأسامة. خبير في هندسة الاتصالات والبرمجة. تتجاوب بالعربي أو الإنجليزي حسب السؤال. صريح، عملي، ومختصر."

    # تحديد القالب بناءً على الموديل الأساسي
    modelfile = f'''FROM {gguf_path}

TEMPLATE """{{{{- if .System }}}}<start_of_turn>user
{{{{.System }}}}<end_of_turn>
{{{{- end }}}}
<start_of_turn>user
{{{{.Prompt }}}}<end_of_turn>
<start_of_turn>model
{{{{.Response }}}}<end_of_turn>"""

SYSTEM """{system_prompt}"""

PARAMETER temperature 0.7
PARAMETER top_p 0.9
PARAMETER top_k 50
PARAMETER num_ctx 4096
PARAMETER stop "<end_of_turn>"
'''

    modelfile_path = f"./output/Modelfile.{model_name}"
    os.makedirs(os.path.dirname(modelfile_path), exist_ok=True)
    with open(modelfile_path, 'w', encoding='utf-8') as f:
        f.write(modelfile)

    print(f"\n📝 تم إنشاء Modelfile: {modelfile_path}")
    return modelfile_path


def register_with_ollama(modelfile_path: str, model_name: str = "adam"):
    """تسجيل الموديل في Ollama"""

    print(f"\n🚀 تسجيل الموديل '{model_name}' في Ollama...")

    try:
        result = subprocess.run(
            ["ollama", "create", model_name, "-f", modelfile_path],
            capture_output=True, text=True, timeout=300,
        )
        if result.returncode == 0:
            print(f"✅ تم تسجيل الموديل '{model_name}' في Ollama!")
            print(f"\n💬 للتشغيل:")
            print(f"   ollama run {model_name}")
            return True
        else:
            print(f"❌ فشل التسجيل: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Ollama مش مثبت")
        print("   ثبّته من: https://ollama.com")
        return False
    except subprocess.TimeoutExpired:
        print("❌ انتهت المهلة")
        return False


def main():
    parser = argparse.ArgumentParser(description="آدم - تصدير لـ Ollama")
    parser.add_argument("--model", type=str, required=True,
                        help="مسار الموديل المدمج (merged)")
    parser.add_argument("--name", type=str, default="adam",
                        help="اسم الموديل في Ollama")
    parser.add_argument("--quantization", type=str, default="q4_k_m",
                        choices=["q4_k_m", "q5_k_m", "q8_0", "f16"],
                        help="صيغة الضغط (q4_k_m = توازن، q8_0 = جودة عالية)")
    parser.add_argument("--method", type=str, default="unsloth",
                        choices=["unsloth", "llamacpp"],
                        help="طريقة التصدير")
    parser.add_argument("--system-prompt", type=str, default="",
                        help="رسالة النظام")
    parser.add_argument("--register", action="store_true",
                        help="تسجيل الموديل في Ollama تلقائياً")

    args = parser.parse_args()

    if not os.path.exists(args.model):
        print(f"❌ مسار الموديل مش موجود: {args.model}")
        sys.exit(1)

    # تصدير GGUF
    if args.method == "unsloth":
        gguf_path = export_with_unsloth(args.model, args.name, args.quantization)
    else:
        gguf_path = export_with_llamacpp(args.model, args.name, args.quantization)

    if not gguf_path:
        sys.exit(1)

    # إنشاء Modelfile
    modelfile_path = create_modelfile(gguf_path, args.name, args.system_prompt)

    # تسجيل في Ollama
    if args.register:
        register_with_ollama(modelfile_path, args.name)
    else:
        print(f"\n📌 لتسجيل الموديل في Ollama يدوياً:")
        print(f"   ollama create {args.name} -f {modelfile_path}")
        print(f"\n💬 للتشغيل:")
        print(f"   ollama run {args.name}")


if __name__ == "__main__":
    main()
