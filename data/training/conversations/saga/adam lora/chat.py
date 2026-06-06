#!/usr/bin/env python3
"""
آدم - اختبار الموديل بعد التدريب
Adam - Chat with the Fine-Tuned Model

اختبر الموديل المُدرَّب قبل تصديره لـ Ollama
"""

import os
import sys
import json
import argparse
import time

# ═══════════════════════════════════════════════════════════════
# الاختبار مع Unsloth
# ═══════════════════════════════════════════════════════════════

def chat_unsloth(model_path: str, system_prompt: str = ""):
    """محادثة تفاعلية مع الموديل المُدرَّب (Unsloth)"""

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
        load_in_4bit=True,
    )
    FastLanguageModel.for_inference(model)  # تفعيل وضع الاستنتاج

    print("\n" + "=" * 60)
    print("🤖 آدم - المحادثة التفاعلية")
    print("اكتب 'خروج' أو 'quit' للإنهاء")
    print("=" * 60 + "\n")

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})

    while True:
        try:
            user_input = input("أنت: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 مع السلامة!")
            break

        if not user_input:
            continue
        if user_input.lower() in ['خروج', 'quit', 'exit', 'q']:
            print("👋 مع السلامة!")
            break

        messages.append({"role": "user", "content": user_input})

        # توليد الرد
        start_time = time.time()
        inputs = tokenizer.apply_chat_template(
            messages,
            tokenize=True,
            add_generation_prompt=True,
            return_tensors="pt",
        ).to(model.device)

        outputs = model.generate(
            input_ids=inputs,
            max_new_tokens=1024,
            temperature=0.7,
            top_p=0.9,
            top_k=50,
            do_sample=True,
            use_cache=True,
        )

        # استخراج الرد الجديد بس
        response_ids = outputs[0][inputs.shape[-1]:]
        response = tokenizer.decode(response_ids, skip_special_tokens=True)
        elapsed = time.time() - start_time

        messages.append({"role": "assistant", "content": response})

        # حساب السرعة
        tokens = len(response_ids)
        speed = tokens / elapsed if elapsed > 0 else 0

        print(f"\nآدم: {response}")
        print(f"\n[⏱️ {elapsed:.1f}s | {tokens} tokens | {speed:.1f} tok/s]\n")


# ═══════════════════════════════════════════════════════════════
# اختبار مع Ollama API (بعد التصدير)
# ═══════════════════════════════════════════════════════════════

def chat_ollama(model_name: str = "adam", base_url: str = "http://localhost:11434"):
    """محادثة تفاعلية مع الموديل عبر Ollama API"""

    import urllib.request
    import urllib.error

    url = f"{base_url}/api/chat"

    messages = [{
        "role": "system",
        "content": "أنت آدم، المساعد الشخصي لأسامة. خبير في هندسة الاتصالات والبرمجة. تتجاوب بالعربي أو الإنجليزي حسب السؤال. صريح، عملي، ومختصر."
    }]

    print("\n" + "=" * 60)
    print(f"🤖 آدم (عبر Ollama - {model_name})")
    print("اكتب 'خروج' أو 'quit' للإنهاء")
    print("=" * 60 + "\n")

    while True:
        try:
            user_input = input("أنت: ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\n👋 مع السلامة!")
            break

        if not user_input:
            continue
        if user_input.lower() in ['خروج', 'quit', 'exit', 'q']:
            print("👋 مع السلامة!")
            break

        messages.append({"role": "user", "content": user_input})

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {
                "temperature": 0.7,
                "top_p": 0.9,
                "num_predict": 1024,
            }
        }

        try:
            start_time = time.time()
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - start_time

            assistant_msg = result.get("message", {}).get("content", "")
            messages.append({"role": "assistant", "content": assistant_msg})

            print(f"\nآدم: {assistant_msg}")
            print(f"\n[⏱️ {elapsed:.1f}s]\n")

        except urllib.error.URLError as e:
            print(f"\n❌ خطأ في الاتصال بـ Ollama: {e}")
            print("   تأكد إن Ollama شغال: ollama serve")
            messages.pop()  # شيل الرسالة اللي فشلت
        except Exception as e:
            print(f"\n❌ خطأ: {e}")
            messages.pop()


# ═══════════════════════════════════════════════════════════════
# اختبار تلقائي - مقارنة قبل وبعد التدريب
# ═══════════════════════════════════════════════════════════════

def auto_test(model_name: str = "adam", base_url: str = "http://localhost:11434"):
    """اختبار تلقائي بأسئلة محددة"""

    import urllib.request
    import urllib.error

    test_questions = [
        "مين أنت؟",
        "إيه الفرق بين 4G و 5G؟",
        "اكتب Python function تحسب throughput",
        "إيه رأيك في LoRA fine-tuning؟",
        "ازاي أحل مشكلة coverage ضعيف؟",
    ]

    print("\n" + "=" * 60)
    print("🧪 اختبار تلقائي لآدم")
    print("=" * 60)

    url = f"{base_url}/api/chat"
    results = []

    for i, question in enumerate(test_questions, 1):
        messages = [
            {
                "role": "system",
                "content": "أنت آدم، المساعد الشخصي لأسامة. خبير في هندسة الاتصالات والبرمجة. تتجاوب بالعربي أو الإنجليزي حسب السؤال. صريح، عملي، ومختصر."
            },
            {"role": "user", "content": question},
        ]

        payload = {
            "model": model_name,
            "messages": messages,
            "stream": False,
            "options": {"temperature": 0.7, "num_predict": 512},
        }

        try:
            start_time = time.time()
            req = urllib.request.Request(
                url,
                data=json.dumps(payload).encode('utf-8'),
                headers={'Content-Type': 'application/json'},
            )
            with urllib.request.urlopen(req, timeout=60) as resp:
                result = json.loads(resp.read().decode('utf-8'))
            elapsed = time.time() - start_time

            response = result.get("message", {}).get("content", "")
            results.append({"question": question, "response": response, "time": elapsed})

            print(f"\n--- سؤال {i}/{len(test_questions)} ---")
            print(f"❓ {question}")
            print(f"💬 {response[:200]}...")
            print(f"⏱️ {elapsed:.1f}s")

        except Exception as e:
            print(f"\n❌ فشل السؤال {i}: {e}")
            results.append({"question": question, "response": str(e), "time": 0})

    print(f"\n\n{'=' * 60}")
    print(f"📊 ملخص الاختبار: {len([r for r in results if r['time'] > 0])}/{len(test_questions)} نجحوا")
    print(f"{'=' * 60}")

    # حفظ النتائج
    results_path = "./output/test_results.json"
    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"✅ تم حفظ النتائج: {results_path}")


# ═══════════════════════════════════════════════════════════════
# Main
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(description="آدم - اختبار الموديل")
    parser.add_argument("--model", type=str, default=None,
                        help="مسار الموديل (Unsloth) أو اسم الموديل (Ollama)")
    parser.add_argument("--ollama", action="store_true",
                        help="استخدام Ollama API بدل Unsloth المباشر")
    parser.add_argument("--ollama-model", type=str, default="adam",
                        help="اسم الموديل في Ollama")
    parser.add_argument("--auto-test", action="store_true",
                        help="اختبار تلقائي بدل محادثة تفاعلية")
    parser.add_argument("--system-prompt", type=str,
                        default="أنت آدم، المساعد الشخصي لأسامة. خبير في هندسة الاتصالات والبرمجة. تتجاوب بالعربي أو الإنجليزي حسب السؤال. صريح، عملي، ومختصر.",
                        help="رسالة النظام")

    args = parser.parse_args()

    if args.auto_test:
        auto_test(args.ollama_model)
    elif args.ollama:
        chat_ollama(args.ollama_model)
    elif args.model:
        chat_unsloth(args.model, args.system_prompt)
    else:
        print("📌 اختر طريقة الاختبار:")
        print("   --ollama             محادثة عبر Ollama API")
        print("   --model PATH         محادثة مباشرة مع موديل Unsloth")
        print("   --auto-test          اختبار تلقائي")
        print("\n📌 أمثلة:")
        print("   python chat.py --ollama --ollama-model adam")
        print("   python chat.py --model ./output/adam-merged")
        print("   python chat.py --auto-test --ollama-model adam")


if __name__ == "__main__":
    main()
