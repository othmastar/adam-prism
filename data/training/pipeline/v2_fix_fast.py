#!/usr/bin/env python3
"""
v2_fix_fast.py — تقطيع ردود الـ assistant لـ v2 حقيقي
=====================================================
ميكانيكي بحت — لا LLM، لا JSON، لا waiting.
يطلع في ثانية.
"""

import json, os, random, re
from pathlib import Path

DATA_DIR = "/home/z/my-project/download/adam_prism_v2/final_dataset"
OUTPUT_DIR = "/home/z/my-project/download/adam_prism_v2/final_dataset_v2_fixed"
MAX_ASST_CHARS = 150

os.makedirs(OUTPUT_DIR, exist_ok=True)


def trim_to_last_sentence(text, max_chars=MAX_ASST_CHARS):
    """يقطع النص عند أول جملة كاملة تحت الـ max_chars"""
    if len(text) <= max_chars:
        return text
    
    # جرب نقطة
    sentences = re.split(r'(?<=[.!?]) +', text)
    result = ""
    for s in sentences:
        if len(result) + len(s) + 1 <= max_chars:
            result += s + " "
        else:
            break
    
    result = result.strip()
    if result:
        return result
    
    # لو مفيش جملة كاملة — خد أول كلمات
    words = text.split()
    result = ""
    for w in words:
        if len(result) + len(w) + 1 <= max_chars:
            result += w + " "
        else:
            break
    
    return result.strip() + "..."


def smart_trim(text, max_chars=MAX_ASST_CHARS):
    """تقليص ذكي — يخلّي المعنى موجود"""
    if len(text) <= max_chars:
        return text
    
    # لو فيه نقاط أو فواصل — خد أول جزء
    for sep in ["\n", ". ", "! ", "? "]:
        idx = text.find(sep)
        if 0 < idx < max_chars:
            return text[:idx + (1 if sep == "\n" else 2)]
    
    # لو فيه رقم في الأول (زي "1/6:") — ده نمط DEEP
    if re.match(r'^\d+/\d+:', text):
        parts = text.split("\n")
        result = parts[0] if len(parts[0]) <= max_chars else parts[0][:max_chars]
        return result
    
    # تقطيع عند الكلمة
    return text[:max_chars].rsplit(" ", 1)[0] + "..."


print("=" * 50)
print("V2 FIX — FAST MODE")
print("=" * 50)

total_fixed = 0
total_skipped = 0
total_before_chars = 0
total_after_chars = 0

for split in ["train", "val", "test"]:
    in_path = os.path.join(DATA_DIR, f"{split}.jsonl")
    out_path = os.path.join(OUTPUT_DIR, f"{split}.jsonl")
    
    with open(in_path) as f:
        lines = f.readlines()
    
    fixed = 0
    skipped = 0
    before_chars = 0
    after_chars = 0
    
    with open(out_path, "w", encoding="utf-8") as fout:
        for line in lines:
            obj = json.loads(line)
            msgs = obj.get("messages", [])
            src = obj.get("metadata", {}).get("source", "?")
            
            for m in msgs:
                if m["role"] == "assistant":
                    original = m["content"]
                    before_chars += len(original)
                    
                    if len(original) > MAX_ASST_CHARS:
                        trimmed = smart_trim(original)
                        m["content"] = trimmed
                        after_chars += len(trimmed)
                        fixed += 1
                    else:
                        after_chars += len(original)
                        skipped += 1
            
            fout.write(json.dumps(obj, ensure_ascii=False) + "\n")
    
    total_fixed += fixed
    total_skipped += skipped
    total_before_chars += before_chars
    total_after_chars += after_chars
    
    print(f"  {split}: {fixed} fixed, {skipped} already short")
    print(f"         {before_chars:,} → {after_chars:,} chars ({before_chars-after_chars:,} saved)")

print(f"\n{'='*50}")
print(f"✅ TOTAL: {total_fixed} assistant responses trimmed")
print(f"   {total_skipped} already short (kept as-is)")
print(f"   {total_before_chars:,} → {total_after_chars:,} total chars")
print(f"   Saved: {total_before_chars - total_after_chars:,} chars")
print(f"{'='*50}")

# ── Merge back ──
print("\n🔗 Merging into final...")
FINAL = "/home/z/my-project/download/adam_prism_v2/final_dataset_v2_fixed"
os.makedirs(FINAL, exist_ok=True)

for split in ["train", "val", "test"]:
    convos = []
    with open(os.path.join(OUTPUT_DIR, f"{split}.jsonl")) as f:
        for line in f:
            convos.append(json.loads(line))
    
    random.shuffle(convos)
    
    with open(os.path.join(FINAL, f"{split}.jsonl"), "w") as f:
        for c in convos:
            f.write(json.dumps(c, ensure_ascii=False) + "\n")
    
    print(f"  {split}: {len(convos)} convos → {FINAL}/")

print(f"\n🏁 Ready for QLoRA: {FINAL}/")
