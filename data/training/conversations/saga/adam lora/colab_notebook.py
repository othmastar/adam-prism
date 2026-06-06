#!/usr/bin/env python3
"""
آدم - Colab Notebook Generator
يولّد ملف Jupyter Notebook لتدريب آدم على Google Colab (GPU مجاني)

الاستخدام:
1. شغّل السكريبت ده: python colab_notebook.py
2. ارفع الملف الناتج (adam_training.ipynb) على Google Colab
3. ارفع ملف training_data.jsonl على Colab
4. شغّل الخلايا بالترتيب
"""

import json
import os


def generate_colab_notebook(output_path: str = "./output/adam_training.ipynb"):
    """توليد Jupyter Notebook لتدريب آدم على Colab"""

    notebook = {
        "nbformat": 4,
        "nbformat_minor": 0,
        "metadata": {
            "colab": {"provenance": [], "gpuType": "T4"},
            "kernelspec": {
                "name": "python3",
                "display_name": "Python 3"
            },
            "language_info": {"name": "python"}
        },
        "cells": []
    }

    # ─── العنوان ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "# 🤖 آدم - تدريب LoRA على Google Colab\n",
            "\n",
            "## الخطوات:\n",
            "1. تأكد إن Runtime نوعه **T4 GPU** (Runtime → Change runtime type)\n",
            "2. ارفع ملف `training_data.jsonl` على Colab (السهم على الشمال)\n",
            "3. شغّل كل خلية بالترتيب\n",
            "\n",
            "## المتطلبات:\n",
            "- ملف `training_data.jsonl` في مجلد `/content/`\n",
            "- Runtime: T4 GPU (مجاني)"
        ]
    })

    # ─── الخلية 1: تفعيل GPU ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 1️⃣ فحص GPU"]
    })

    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "import torch\n",
            "if torch.cuda.is_available():\n",
            "    gpu_name = torch.cuda.get_device_name(0)\n",
            "    gpu_mem = torch.cuda.get_device_properties(0).total_mem / 1e9\n",
            "    print(f'✅ GPU: {gpu_name}')\n",
            "    print(f'   VRAM: {gpu_mem:.1f} GB')\n",
            "else:\n",
            "    print('❌ مش لاقي GPU! غيّر Runtime لـ T4 GPU')\n",
            "    print('   Runtime → Change runtime type → T4 GPU')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 2: تثبيت Unsloth ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 2️⃣ تثبيت المكتبات"]
    })

    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "# تثبيت Unsloth (الطريقة الأسرع)\n",
            "%%capture\n",
            "import os\n",
            "if not os.path.exists('/content/unsloth_installed'):\n",
            "    !pip install --no-deps trl peft accelerate bitsandbytes\n",
            "    !pip install --no-deps unsloth\n",
            "    !pip install datasets\n",
            "    !touch /content/unsloth_installed\n",
            "    print('✅ تم التثبيت')\n",
            "else:\n",
            "    print('✅ مكتبات مثبتة بالفعل')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 3: تحميل الموديل ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 3️⃣ تحميل الموديل الأساسي"]
    })

    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "from unsloth import FastLanguageModel\n",
            "import torch\n",
            "\n",
            "# اختار الموديل:\n",
            "# 'unsloth/gemma-2-2b-it' - أسرع، مناسب لـ T4\n",
            "# 'unsloth/gemma-2-9b-it' - أقوى، محتاج A100\n",
            "# 'unsloth/Qwen2.5-3B-Instruct' - بديل قوي\n",
            "\n",
            "MODEL_NAME = 'unsloth/gemma-2-2b-it'  # غيّر ده لو عايز موديل مختلف\n",
            "\n",
            "model, tokenizer = FastLanguageModel.from_pretrained(\n",
            "    model_name=MODEL_NAME,\n",
            "    max_seq_length=2048,\n",
            "    dtype=None,\n",
            "    load_in_4bit=True,\n",
            ")\n",
            "\n",
            "print(f'✅ تم تحميل: {MODEL_NAME}')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 4: إضافة LoRA ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 4️⃣ إضافة LoRA Adapters"]
    })

    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "model = FastLanguageModel.get_peft_model(\n",
            "    model,\n",
            "    r=16,              # رتبة LoRA (8, 16, 32, 64)\n",
            "    lora_alpha=16,\n",
            "    lora_dropout=0,\n",
            "    target_modules=[\n",
            "        'q_proj', 'k_proj', 'v_proj', 'o_proj',\n",
            "        'gate_proj', 'up_proj', 'down_proj',\n",
            "    ],\n",
            "    bias='none',\n",
            "    use_gradient_checkpointing='unsloth',\n",
            "    random_state=3407,\n",
            ")\n",
            "\n",
            "model.print_trainable_parameters()\n",
            "print('✅ تم إضافة LoRA adapters')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 5: تحميل البيانات ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 5️⃣ تحميل بيانات التدريب\n",
                    "\n",
                    "⚠️ لازم تكون رفعت `training_data.jsonl` على Colab أولاً!"]
    })

    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "import json\n",
            "from datasets import Dataset\n",
            "\n",
            "DATA_PATH = '/content/training_data.jsonl'  # مسار البيانات\n",
            "\n",
            "# تحميل البيانات\n",
            "data = []\n",
            "with open(DATA_PATH, 'r', encoding='utf-8') as f:\n",
            "    for line in f:\n",
            "        if line.strip():\n",
            "            data.append(json.loads(line.strip()))\n",
            "\n",
            "print(f'✅ تم تحميل {len(data)} مثال تدريبي')\n",
            "\n",
            "# تحويل لـ Dataset\n",
            "conversations_list = []\n",
            "for item in data:\n",
            "    conversations_list.append(item['conversations'])\n",
            "\n",
            "dataset = Dataset.from_dict({'conversations': conversations_list})\n",
            "\n",
            "# دالة التنسيق\n",
            "def formatting_func(examples):\n",
            "    texts = []\n",
            "    for conv in examples['conversations']:\n",
            "        text = tokenizer.apply_chat_template(\n",
            "            conv,\n",
            "            tokenize=False,\n",
            "            add_generation_prompt=False,\n",
            "        )\n",
            "        texts.append(text)\n",
            "    return {'text': texts}\n",
            "\n",
            "print('✅ البيانات جاهزة للتدريب')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 6: التدريب ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 6️⃣ التدريب 🏋️\n",
                    "\n",
                    "ده المكان اللي السحر بيحصل فيه! ⏱️ الوقت: ~30-60 دقيقة"]
    })

    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "from trl import SFTTrainer\n",
            "from transformers import TrainingArguments\n",
            "\n",
            "trainer = SFTTrainer(\n",
            "    model=model,\n",
            "    tokenizer=tokenizer,\n",
            "    train_dataset=dataset,\n",
            "    formatting_func=formatting_func,\n",
            "    max_seq_length=2048,\n",
            "    args=TrainingArguments(\n",
            "        per_device_train_batch_size=2,\n",
            "        gradient_accumulation_steps=4,\n",
            "        warmup_steps=10,\n",
            "        max_steps=100,          # زوّد لو عندك بيانات كتير\n",
            "        learning_rate=2e-4,\n",
            "        weight_decay=0.01,\n",
            "        lr_scheduler_type='cosine',\n",
            "        seed=3407,\n",
            "        fp16=False,\n",
            "        bf16=True,              # T4 مش بيدعم bf16، هيستخدم fp16 تلقائياً\n",
            "        logging_steps=1,\n",
            "        save_steps=25,\n",
            "        output_dir='/content/output',\n",
            "        report_to='none',\n",
            "    ),\n",
            ")\n",
            "\n",
            "print('🏋️ بدء التدريب...')\n",
            "trainer.train()\n",
            "print('🎉 انتهى التدريب!')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 7: اختبار ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 7️⃣ اختبار الموديل"]
    })

    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "FastLanguageModel.for_inference(model)\n",
            "\n",
            "test_messages = [\n",
            "    {'role': 'system', 'content': 'أنت آدم، المساعد الشخصي لأسامة. خبير في هندسة الاتصالات والبرمجة. تتجاوب بالعربي أو الإنجليزي حسب السؤال. صريح، عملي، ومختصر.'},\n",
            "    {'role': 'user', 'content': 'مين أنت؟'},\n",
            "]\n",
            "\n",
            "inputs = tokenizer.apply_chat_template(\n",
            "    test_messages,\n",
            "    tokenize=True,\n",
            "    add_generation_prompt=True,\n",
            "    return_tensors='pt',\n",
            ").to(model.device)\n",
            "\n",
            "outputs = model.generate(\n",
            "    input_ids=inputs,\n",
            "    max_new_tokens=256,\n",
            "    temperature=0.7,\n",
            "    top_p=0.9,\n",
            "    do_sample=True,\n",
            ")\n",
            "\n",
            "response_ids = outputs[0][inputs.shape[-1]:]\n",
            "response = tokenizer.decode(response_ids, skip_special_tokens=True)\n",
            "\n",
            "print(f'❓ مين أنت؟')\n",
            "print(f'💬 آدم: {response}')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 8: حفظ GGUF ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": ["## 8️⃣ تصدير GGUF وتحميل\n",
                    "\n",
                    "الملف الناتج هتحمّله وتشغّله على Ollama محلياً"]
    })

    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "# حفظ LoRA adapter\n",
            "model.save_pretrained('/content/output/adam-lora-adapter')\n",
            "tokenizer.save_pretrained('/content/output/adam-lora-adapter')\n",
            "print('✅ LoRA adapter محفوظ')\n",
            "\n",
            "# دمج وحفظ كموديل كامل\n",
            "model.save_pretrained_merged('/content/output/adam-merged', tokenizer, save_method='merged_16bit')\n",
            "print('✅ الموديل المدمج محفوظ')\n",
            "\n",
            "# تصدير GGUF (Q4_K_M - الأفضل)\n",
            "model.save_pretrained_gguf('/content/output/adam-gguf', tokenizer, quantization_method='q4_k_m')\n",
            "print('✅ GGUF Q4_K_M محفوظ')\n",
            "\n",
            "# تصدير GGUF (Q8_0 - جودة أعلى)\n",
            "model.save_pretrained_gguf('/content/output/adam-gguf-q8', tokenizer, quantization_method='q8_0')\n",
            "print('✅ GGUF Q8_0 محفوظ')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 9: تحميل الملف ───
    notebook["cells"].append({
        "cell_type": "code",
        "metadata": {},
        "source": [
            "# تحميل ملف GGUF\n",
            "from google.colab import files\n",
            "import glob\n",
            "\n",
            "# البحث عن ملف GGUF\n",
            "gguf_files = glob.glob('/content/output/adam-gguf/*.gguf')\n",
            "if gguf_files:\n",
            "    print(f'📦 تحميل: {gguf_files[0]}')\n",
            "    files.download(gguf_files[0])\n",
            "else:\n",
            "    print('❌ مش لاقي ملف GGUF')"
        ],
        "execution_count": None,
        "outputs": []
    })

    # ─── الخلية 10: تعليمات التشغيل ───
    notebook["cells"].append({
        "cell_type": "markdown",
        "metadata": {},
        "source": [
            "## 9️⃣ التشغيل على جهازك\n",
            "\n",
            "بعد تحميل ملف GGUF:\n",
            "\n",
            "1. ثبّت Ollama: https://ollama.com\n",
            "2. أنشئ ملف `Modelfile.adam`:\n",
            "```\n",
            "FROM ./unsloth.Q4_K_M.gguf\n",
            "TEMPLATE \"\"\"{{- if .System }}<start_of_turn>user\n",
            "{{.System }}<end_of_turn>\n",
            "{{- end }}\n",
            "<start_of_turn>user\n",
            "{{.Prompt }}<end_of_turn>\n",
            "<start_of_turn>model\n",
            "{{.Response }}<end_of_turn>\"\"\"\n",
            "SYSTEM \"\"\"أنت آدم، المساعد الشخصي لأسامة. خبير في هندسة الاتصالات والبرمجة. تتجاوب بالعربي أو الإنجليزي حسب السؤال. صريح، عملي، ومختصر.\"\"\"\n",
            "PARAMETER temperature 0.7\n",
            "PARAMETER top_p 0.9\n",
            "PARAMETER num_ctx 4096\n",
            "```\n",
            "3. شغّل:\n",
            "```bash\n",
            "ollama create adam -f Modelfile.adam\n",
            "ollama run adam\n",
            "```"
        ]
    })

    # حفظ الـ notebook
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(notebook, f, ensure_ascii=False, indent=2)

    print(f"✅ تم إنشاء Colab Notebook: {output_path}")
    print(f"\n📌 الخطوات:")
    print(f"   1. اذهب إلى https://colab.research.google.com")
    print(f"   2. ارفع الملف {output_path}")
    print(f"   3. ارفع training_data.jsonl")
    print(f"   4. شغّل Runtime → T4 GPU")
    print(f"   5. شغّل الخلايا بالترتيب")

    return output_path


if __name__ == "__main__":
    generate_colab_notebook()
