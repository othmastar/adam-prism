#!/usr/bin/env python3
"""
آدم - سكريبت سريع للتدريب والتصدير
Adam - Quick Start Script

استخدم ده لو عايز كل حاجة في أمر واحد
"""

import os
import sys
import subprocess


def main():
    print("\n" + "=" * 60)
    print("🤖 آدم - Quick Start")
    print("=" * 60)
    print()
    print("اختار اللي عايزه:")
    print()
    print("  1. 🏋️ تدريب على GPU محلي")
    print("  2. 📓 إنشاء Colab Notebook (GPU مجاني)")
    print("  3. 📊 تجهيز بيانات التدريب")
    print("  4. 💬 اختبار موديل (عبر Ollama)")
    print("  5. 📦 تصدير GGUF لـ Ollama")
    print("  6. 🔍 فحص GPU")
    print("  7. 📖 دليل شامل")
    print()

    choice = input("اختيارك (1-7): ").strip()

    if choice == "1":
        # تدريب محلي
        print("\n🏋️ بدء التدريب...")
        steps = input("عدد الخطوات (100 للتجربة، 500 للتدريب الجدّي): ").strip() or "100"
        method = input("الطريقة (unsloth/peft) [unsloth]: ").strip() or "unsloth"

        cmd = f"python3 train.py --method {method} --steps {steps}"
        print(f"\n📌 تشغيل: {cmd}")
        os.system(cmd)

    elif choice == "2":
        # Colab Notebook
        print("\n📓 إنشاء Colab Notebook...")
        os.system("python3 colab_notebook.py")

    elif choice == "3":
        # تجهيز البيانات
        print("\n📊 تجهيز البيانات...")
        print()
        print("  1. إنشاء بيانات مثال")
        print("  2. التحقق من بيانات موجودة")
        print("  3. تحويل Alpaca → ShareGPT")
        print("  4. دمج ملفات بيانات")
        data_choice = input("اختيارك: ").strip()

        if data_choice == "1":
            os.system("python3 prepare_data.py --create-example")
        elif data_choice == "2":
            path = input("مسار الملف: ").strip()
            os.system(f"python3 prepare_data.py --validate {path}")
        elif data_choice == "3":
            src = input("ملف Alpaca: ").strip()
            dst = input("ملف الإخراج [./data/training_data.jsonl]: ").strip() or "./data/training_data.jsonl"
            os.system(f"python3 prepare_data.py --convert-alpaca {src} --output {dst}")
        elif data_choice == "4":
            files = input("ملفات (مفصولة بمسافة): ").strip()
            dst = input("ملف الإخراج [./data/merged.jsonl]: ").strip() or "./data/merged.jsonl"
            os.system(f"python3 prepare_data.py --merge {files} --output {dst}")

    elif choice == "4":
        # اختبار
        model_name = input("اسم الموديل في Ollama [adam]: ").strip() or "adam"
        os.system(f"python3 chat.py --ollama --ollama-model {model_name}")

    elif choice == "5":
        # تصدير
        model_path = input("مسار الموديل المدمج: ").strip()
        model_name = input("اسم الموديل [adam]: ").strip() or "adam"
        register = input("تسجيل تلقائي في Ollama؟ (y/n) [n]: ").strip().lower() == 'y'
        reg_flag = "--register" if register else ""
        os.system(f"python3 export_gguf.py --model {model_path} --name {model_name} {reg_flag}")

    elif choice == "6":
        # فحص GPU
        os.system("python3 train.py --check-gpu")

    elif choice == "7":
        # الدليل
        print("""
╔══════════════════════════════════════════════════════════╗
║           🤖 آدم - دليل LoRA Fine-Tuning               ║
╚══════════════════════════════════════════════════════════╝

📌 إيه LoRA؟
═════════════
LoRA = Low-Rank Adaptation
تقنية بتسمح بتدريب موديل كبير بأقل ذاكرة ممكنة
بدل ما تدرب كل الأوزان (4 مليار)، بتدرب جزء صغير
فقط (~0.1% من الأوزان) بس التأثير بيكون كبير

📌 الفرق بيننا وبين قبل؟
══════════════════════════════
قبل: كنا بنحاول نخلي الموديل يتصرف بطريقة معينة
     بكلمات (Prompt Engineering) - الموديل ما تغيرش

دلوقتي: بنغيّر أوزان الموديل نفسه (LoRA Training)
        الموديل بيتعلم السلوك الجديد فعلاً

📌 البيانات المطلوبة:
════════════════════════
- أقل شيء: 50-100 مثال (للسلوك الأساسي)
- المثالي: 500-2000 مثال متنوع
- الصيغة: ShareGPT (محادثات متعددة الأدوار)

كل مثال = محادثة بين المستخدم وآدم:
  {
    "conversations": [
      {"role": "system", "content": "..."},
      {"role": "user", "content": "سؤال"},
      {"role": "assistant", "content": "جواب"}
    ]
  }

📌 إزاي تجمع بيانات؟
═══════════════════════
1. اكتب محادثات يدوياً (أدق طريقة)
2. استخدم ChatGPT/Claude لتوليد أمثلة
3. جمّع محادثاتك الحقيقية مع AI
4. حوّل مستنداتك لـ Q&A pairs
5. استخدم prepare_data.py للتحويل

📌 إزاي تشغّل؟
══════════════════
1. لو عندك GPU:
   ./setup.sh
   python3 train.py --method unsloth --steps 100

2. لو مش عندك GPU:
   python3 colab_notebook.py
   # يولّد notebook لـ Google Colab (مجاني!)

3. بعد التدريب:
   python3 export_gguf.py --model ./output/adam-lora/adam-merged --register
   ollama run adam

📌 إزاي تعرف إن التدريب نجح؟
═══════════════════════════════
- الـ loss لازم ينزل مع الوقت
- لو الـ loss نزل من ~2.5 لـ ~1.0 = ممتاز
- لو الـ loss نزل كتير أو لـ ~0.0 = overfitting
- جرّب الموديل بعد التدريب وشوف الردود
- لو الردود منطقية = نجاح

📌 نصائح مهمة:
════════════════
1. البيانات أهم من عدد الخطوات
2. ابدأ بـ 100 خطوة واختبر
3. لو محتاج أكتر زوّد تدريجياً
4. التنوع في البيانات أهم من الكمية
5. كل ما البيانات أقرب للاستخدام الحقيقي = نتائج أحسن
""")

    else:
        print("اختيار مش صحيح")


if __name__ == "__main__":
    main()
