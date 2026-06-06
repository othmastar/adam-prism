#!/usr/bin/env python3
"""
v2_fix_ai.py — إعادة كتابة ردود الـ assistant بذكاء عبر gemma4:e4b
================================================================
- يحافظ على user messages كما هي
- يعيد كتابة ردود الـ assistant فقط — طبيعي، مصري، v2 style، <150 حرف
- يرسل 25 محادثة في كل batch — يخلص بسرعة على GPU القوي
"""

import json, os, sys, time, re
import requests

DATA_DIR = "/home/z/my-project/download/adam_prism_v2/final_dataset"
OUTPUT_DIR = "/home/z/my-project/download/adam_prism_v2/final_dataset_v2_ai"
os.makedirs(OUTPUT_DIR, exist_ok=True)

OLLAMA_URL = "http://localhost:11434/api/generate"
MODEL = "gemma4:e4b"

# ── الـ prompt اللي هيروح للموديل ──
FIX_PROMPT = """أنت خبير في نمط v2 للحوار التقني.
في نمط v2:
- المستخدم يكتب طويل ويحمل كل السياق
- المساعد (أنت) ترد قصير (<100 حرف)، طبيعي، مصري، مباشر

أعد كتابة رد المساعد في المحادثة التالية فقط.
لا تغير كلام المستخدم أبداً.
اجعل رد المساعد قصير (<100 حرف)، طبيعي، كأنك آدم المنظار.

المحادثة:
{conversation}

أخرج JSON بنفس هيكل المحادثة لكن مع رد المساعد الجديد فقط."""


def batch_rewrite(convs):
    """إرسال batch من المحادثات للموديل"""
    batch_data = []
    for conv in convs:
        asst_msgs = [m for m in conv["messages"] if m["role"] == "assistant"]
        if not asst_msgs:
            batch_data.append(None)
            continue
        # نحتاج نصلح؟ لو كلها قصيرة — لا
        if all(len(m["content"]) < 150 for m in asst_msgs):
            batch_data.append(None)
            continue
        batch_data.append(conv)
    
    to_fix = [b for b in batch_data if b is not None]
    if not to_fix:
        return batch_data
    
    payload = {
        "model": MODEL,
        "prompt": FIX_PROMPT.format(conversation=json.dumps(to_fix[0], ensure_ascii=False)),
        "system": "أنت خبير في تحويل المحادثات لنمط v2. تخرج JSON فقط.",
        "stream": False,
        "options": {"temperature": 0.3, "num_predict": 2048}
    }
    
    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        text = resp.json().get("response", "")
        
        # استخراج JSON من الرد
        start = text.find("{")
        end = text.rfind("}")
        if start >= 0 and end > start:
            fixed = json.loads(text[start:end+1])
            batch_data[0] = fixed
    except:
        pass
    
    return batch_data


def process_split(split_name):
    in_path = os.path.join(DATA_DIR, f"{split_name}.jsonl")
    out_path = os.path.join(OUTPUT_DIR, f"{split_name}.jsonl")
    
    with open(in_path) as f:
        lines = f.readlines()
    
    total = len(lines)
    fixed = 0
    total_before = 0
    total_after = 0
    
    with open(out_path, "w") as fout:
        for idx, line in enumerate(lines):
            conv = json.loads(line)
            
            # كل محادثة لوحدها
            asst_indices = [i for i, m in enumerate(conv["messages"]) if m["role"] == "assistant"]
            if not asst_indices:
                fout.write(line)
                continue
            
            before = sum(len(conv["messages"][i]["content"]) for i in asst_indices)
            total_before += before
            
            if all(len(conv["messages"][i]["content"]) < 150 for i in asst_indices):
                total_after += before
                fout.write(line)
                continue
            
            # إرسال للموديل
            payload = {
                "model": MODEL,
                "prompt": f"أعد كتابة ردود المساعد فقط (قصيرة <100 حرف، طبيعي، مصري، آدم المنظار).\nلا تغير المستخدم.\n\n{json.dumps(conv, ensure_ascii=False)}",
                "system": "أنت آدم المنظار. تخرج JSON بنفس الهيكل مع ردود مساعد قصيرة.",
                "stream": False,
                "options": {"temperature": 0.3, "num_predict": 2048}
            }
            
            try:
                resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
                text = resp.json().get("response", "")
                
                start = text.find("{")
                end = text.rfind("}")
                if start >= 0 and end > start:
                    fixed_conv = json.loads(text[start:end+1])
                    conv = fixed_conv
                    fixed += 1
            except:
                pass
            
            after = sum(len(conv["messages"][i]["content"]) for i in asst_indices if i < len(conv["messages"]))
            total_after += after
            
            fout.write(json.dumps(conv, ensure_ascii=False) + "\n")
            
            if (idx + 1) % 10 == 0:
                print(f"  {idx+1}/{total}", end=" ", flush=True)
    
    print(f"\n  {split_name}: {fixed} fixed, {total_before:,} → {total_after:,} chars")
    return fixed


if __name__ == "__main__":
    print("=" * 50)
    print("V2 FIX — AI MODE (gemma4:e4b)")
    print("=" * 50)
    
    total = 0
    for split in ["train", "val", "test"]:
        f = process_split(split)
        total += f
    
    print(f"\n✅ {total} conversations rewritten")
    print(f"📁 Output: {OUTPUT_DIR}/")
    print("🏁 Ready for QLoRA!")
