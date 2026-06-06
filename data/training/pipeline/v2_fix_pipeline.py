#!/usr/bin/env python3
"""
v2_fix_pipeline.py — يحوّل v2_final لـ v2 حقيقي
===============================================
- يحافظ على user messages زي ما هي
- يعيد كتابة assistant responses فقط — قصير (<150 حرف)، v2 style
- يستخدم gemma4:e4b المحلي على السحابة
- يخلّص في دقيقة لأن GPU السحابة خارق
"""

import json, os, time, sys
import requests
from collections import Counter

# ── Config ─────────────────────────────────────
DATA_DIR = "/home/z/my-project/download/adam_prism_v2/final_dataset"
OUTPUT_DIR = "/home/z/my-project/download/adam_prism_v2/final_dataset_v2_fixed"
OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:e4b"
BATCH_SIZE = 50  # يرسل 50 محادثة مع بعض في prompt واحد

os.makedirs(OUTPUT_DIR, exist_ok=True)

SYSTEM_PROMPT_FIXER = """أنت خبير في تحويل المحادثات التقنية إلى نمط v2.
نمط v2 = المستخدم يحمل السياق (رسائل طويلة) والمساعد يرد قصير وطبيعي (<150 حرف).
مهمتك: للأسفل هتاخد محادثة كاملة، عيد كتابة ردود الـ assistant فقط.
- user messages: اتركها كما هي بالضبط
- assistant responses: اختصرها لأقل من 150 حرف، طبيعي، مثل آدم المنظار
- حافظ على نفس عدد الأدوار ونفس التسلسل"""

V2_FIX_PROMPT = """حول المحادثة التالية لنمط v2:
- المستخدم = يفضل طويل (لا تغير كلامه أبداً)
- المساعد = يرد قصير (<150 حرف)، طبيعي، مباشر، بدون شرح أو تحليل طويل

المحادثة (JSON):
{conversation}

أخرج نفس JSON مع تعديل assistant messages فقط.
لا تغير أي شيء آخر."""


def call_ollama(prompt, system=None):
    payload = {
        "model": MODEL,
        "prompt": prompt,
        "system": system or SYSTEM_PROMPT_FIXER,
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 4096}
    }
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
        return resp.json().get("response", "")
    except Exception as e:
        return f"ERROR: {e}"


def fix_conversation(conv):
    """إعادة كتابة assistant responses لمحادثة واحدة"""
    msgs = conv.get("messages", [])
    
    # لو مفيش حاجة عاوزين نصلحها — اسحب
    asst_indices = [i for i, m in enumerate(msgs) if m["role"] == "assistant"]
    if not asst_indices:
        return conv
    
    # لو كل الردود قصيرة أصلاً — اسحب
    if all(len(msgs[i]["content"]) < 150 for i in asst_indices):
        return conv
    
    prompt = V2_FIX_PROMPT.format(conversation=json.dumps(conv, ensure_ascii=False))
    result = call_ollama(prompt)
    
    if result.startswith("ERROR"):
        print(f"  ✗ {result}")
        return None
    
    try:
        # استخراج JSON من الرد
        # (الموديل ممكن يضيف كلام قبل وبعد الـ JSON)
        start = result.find("{")
        end = result.rfind("}")
        if start >= 0 and end > start:
            result = result[start:end+1]
        fixed = json.loads(result)
        return fixed
    except json.JSONDecodeError:
        print(f"  ✗ JSON parse error, len={len(result)}")
        return None


def process_split(split_name):
    """معالجة split كامل"""
    in_path = os.path.join(DATA_DIR, f"{split_name}.jsonl")
    out_path = os.path.join(OUTPUT_DIR, f"{split_name}.jsonl")
    
    if not os.path.exists(in_path):
        return
    
    with open(in_path) as f:
        lines = f.readlines()
    
    total = len(lines)
    fixed_count = 0
    skipped_count = 0
    error_count = 0
    
    print(f"\n📁 Processing {split_name}.jsonl ({total} conversations)...")
    
    with open(out_path, "w", encoding="utf-8") as fout:
        for idx, line in enumerate(lines):
            conv = json.loads(line)
            src = conv.get("metadata", {}).get("source", "unknown")
            
            # نصلح كل المصادر مش v2_final بس
            result = fix_conversation(conv)
            
            if result is None:
                error_count += 1
                # احتفظ بالأصل لو فشل
                fout.write(line)
            else:
                # تحقق من التغيير
                old_len = sum(len(m["content"]) for m in conv["messages"] if m["role"] == "assistant")
                new_len = sum(len(m["content"]) for m in result["messages"] if m["role"] == "assistant")
                
                if new_len < old_len:
                    fixed_count += 1
                    result["metadata"]["v2_fixed"] = True
                    result["metadata"]["v2_fixed_score"] = round(1 - new_len / max(old_len, 1), 2)
                else:
                    skipped_count += 1
                
                fout.write(json.dumps(result, ensure_ascii=False) + "\n")
            
            if (idx + 1) % 10 == 0:
                print(f"  {idx+1}/{total}...", end=" ", flush=True)
    
    print(f"\n  ✅ {split_name}: {fixed_count} fixed, {skipped_count} skipped, {error_count} errors")
    return fixed_count, skipped_count, error_count


if __name__ == "__main__":
    print("=" * 50)
    print("V2 FIX PIPELINE")
    print("=" * 50)
    
    # Test first
    print("\n🔍 Testing with 1 sample...")
    with open(os.path.join(DATA_DIR, "train.jsonl")) as f:
        sample = json.loads(f.readline())
    
    result = fix_conversation(sample)
    if result:
        old_len = sum(len(m["content"]) for m in sample["messages"] if m["role"] == "assistant")
        new_len = sum(len(m["content"]) for m in result["messages"] if m["role"] == "assistant")
        print(f"  Before: {old_len} chars asst → After: {new_len} chars asst")
        print("  ✅ Test passed!")
    else:
        print("  ❌ Test failed — check Ollama")
        sys.exit(1)
    
    # Process all splits
    fixed_total = 0
    for split in ["train", "val", "test"]:
        f, s, e = process_split(split)
        fixed_total += f
    
    print(f"\n{'='*50}")
    print(f"✅ DONE: {fixed_total} conversations fixed")
    print(f"📁 Output: {OUTPUT_DIR}/")
    print(f"{'='*50}")
    
    # Now merge back with consciousness and raw
    print("\n🔗 Merging all sources into final...")
    FINAL = "/home/z/my-project/download/adam_prism_v2/final_dataset_final"
    os.makedirs(FINAL, exist_ok=True)
    
    for split in ["train", "val", "test"]:
        all_convos = []
        
        # V2 fixed first
        with open(os.path.join(OUTPUT_DIR, f"{split}.jsonl")) as f:
            for line in f:
                all_convos.append(json.loads(line))
        
        import random
        random.shuffle(all_convos)
        
        with open(os.path.join(FINAL, f"{split}.jsonl"), "w") as f:
            for conv in all_convos:
                f.write(json.dumps(conv, ensure_ascii=False) + "\n")
        
        print(f"  {split}: {len(all_convos)} conversations → {FINAL}/")
    
    print(f"\n🏁 Final v2 dataset ready at: {FINAL}/")
