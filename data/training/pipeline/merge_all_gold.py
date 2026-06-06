#!/usr/bin/env python3
"""
merge_all_gold.py — يدمج كل الذهب في dataset واحد لتدريب آدم
المصادر:
  1. saga/batch*.jsonl  ← الذهب الخالص (384, tool use + consciousness + dialect + security)
  2. فاينل داتا ست/      ← الـ 1,530 المجهزة قبل كده
  3. podcast_data.jsonl  ← البودكاست بتاعنا (49)
  4. consciousness_data/ ← وعي آدم (80)
"""

import json
import os
import random
from pathlib import Path
from collections import Counter

random.seed(3407)

BASE = Path("/mnt/Workspace/Adam_Prism_Complete_v2/data/training")
OUTPUT = BASE / "ADAM_COMPLETE"

os.makedirs(OUTPUT, exist_ok=True)

all_convs = []
seen_ids = set()
source_stats = Counter()

# ═══════════════════════════════════════════
# SOURCE 1: SAGA BATCH FILES (THE GOLD)
# ═══════════════════════════════════════════
print("📦 Loading saga batch files (384 gold)...")
saga_dir = BASE / "conversations" / "saga"
batch_files = sorted(saga_dir.glob("batch*.jsonl"))
for bf in batch_files:
    with open(bf) as f:
        for line in f:
            conv = json.loads(line)
            meta = conv.get("metadata", {})
            cid = meta.get("id", f"saga_{bf.stem}_{len(all_convs)}")
            if cid not in seen_ids:
                seen_ids.add(cid)
                meta["merge_source"] = f"saga/{bf.stem}"
                all_convs.append(conv)
                source_stats[meta.get("merge_source")] += 1

print(f"   → {len(all_convs)} so far")

# ═══════════════════════════════════════════
# SOURCE 2: FINAL DATASET (1,530)
# ═══════════════════════════════════════════
print("📦 Loading final_dataset (1,530)...")
fd_dir = BASE / "conversations" / "فاينل داتا ست"
for split in ["train.jsonl", "val.jsonl", "test.jsonl"]:
    fpath = fd_dir / split
    if fpath.exists():
        with open(fpath) as f:
            for line in f:
                conv = json.loads(line)
                meta = conv.get("metadata", {})
                cid = meta.get("id", f"final_{split}_{len(all_convs)}")
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    meta["merge_source"] = f"final_dataset/{split}"
                    all_convs.append(conv)
                    source_stats[meta["merge_source"]] += 1

print(f"   → {len(all_convs)} so far")

# ═══════════════════════════════════════════
# SOURCE 3: PODCAST DATA (49)
# ═══════════════════════════════════════════
print("📦 Loading podcast_data (49)...")
podcast_path = BASE / "podcast_data.jsonl"
if podcast_path.exists():
    with open(podcast_path) as f:
        for line in f:
            conv = json.loads(line)
            meta = conv.get("metadata", {})
            cid = meta.get("id", f"podcast_{len(all_convs)}")
            if cid not in seen_ids:
                seen_ids.add(cid)
                meta["merge_source"] = "podcast"
                all_convs.append(conv)
                source_stats[meta["merge_source"]] += 1

print(f"   → {len(all_convs)} so far")

# ═══════════════════════════════════════════
# SOURCE 4: CONSCIOUSNESS DATA (80)
# ═══════════════════════════════════════════
# ═══════════════════════════════════════════
# SOURCE 5: SAGA SPLITS — 117 unhoused conversations
# ═══════════════════════════════════════════
# ═══════════════════════════════════════════
# SOURCE 6: EXTRA GOLD (137 educational + batches)
# ═══════════════════════════════════════════
# ═══════════════════════════════════════════
# SOURCE 7: SCRAPLING TRAINING (10)
# ═══════════════════════════════════════════
# ═══════════════════════════════════════════
# SOURCE 8: SELF-IMPROVEMENT TRAINING (10)
# ═══════════════════════════════════════════
# ═══════════════════════════════════════════
# SOURCE 9: JOURNAL/MEMORY TRAINING (10)
# ═══════════════════════════════════════════
print("📦 Loading journal training (10)...")
journal_path = BASE / "ADAM_COMPLETE" / "journal_training.jsonl"
if journal_path.exists():
    with open(journal_path) as f:
        for line in f:
            conv = json.loads(line)
            meta = conv.get("metadata", {})
            cid = meta.get("id", f"journal_{len(all_convs)}")
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_convs.append(conv)
                source_stats["journal_training"] += 1

print(f"   → {len(all_convs)} so far")

print("📦 Loading self-improvement training (10)...")
selfimprove_path = BASE / "ADAM_COMPLETE" / "self_improvement_training.jsonl"
if selfimprove_path.exists():
    with open(selfimprove_path) as f:
        for line in f:
            conv = json.loads(line)
            meta = conv.get("metadata", {})
            cid = meta.get("id", f"selfimprove_{len(all_convs)}")
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_convs.append(conv)
                source_stats["self_improvement"] += 1

print(f"   → {len(all_convs)} so far")

print("📦 Loading Scrapling training (10)...")
scrapling_path = BASE / "ADAM_COMPLETE" / "scrapling_training.jsonl"
if scrapling_path.exists():
    with open(scrapling_path) as f:
        for line in f:
            conv = json.loads(line)
            meta = conv.get("metadata", {})
            cid = meta.get("id", f"scrapling_{len(all_convs)}")
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_convs.append(conv)
                source_stats["scrapling_training"] += 1

print(f"   → {len(all_convs)} so far")

print("📦 Loading extra gold 137 (educational + batches)...")
extra_path = BASE / "ADAM_COMPLETE" / "extra_gold_137.jsonl"
if extra_path.exists():
    with open(extra_path) as f:
        for line in f:
            conv = json.loads(line)
            meta = conv.get("metadata", {})
            cid = meta.get("id", f"extra_gold_{len(all_convs)}")
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_convs.append(conv)
                source_stats[meta.get("source", "extra_gold")] += 1

print(f"   → {len(all_convs)} so far")

print("📦 Loading saga split leftovers (117)...")
missing_path = BASE / "ADAM_COMPLETE" / "missing_from_saga.jsonl"
if missing_path.exists():
    with open(missing_path) as f:
        for line in f:
            conv = json.loads(line)
            meta = conv.get("metadata", {})
            cid = meta.get("id", f"saga_split_{len(all_convs)}")
            if cid not in seen_ids:
                seen_ids.add(cid)
                all_convs.append(conv)
                source_stats[meta.get("merge_source", "saga_splits")] += 1

print(f"   → {len(all_convs)} so far")

print("📦 Loading consciousness_data (80)...")
cs_dir = BASE / "consciousness_data"
for split in ["train.jsonl", "val.jsonl", "test.jsonl"]:
    fpath = cs_dir / split
    if fpath.exists():
        with open(fpath) as f:
            for line in f:
                conv = json.loads(line)
                meta = conv.get("metadata", {})
                cid = meta.get("id", f"consciousness_{split}_{len(all_convs)}")
                if cid not in seen_ids:
                    seen_ids.add(cid)
                    meta["merge_source"] = f"consciousness_data/{split}"
                    all_convs.append(conv)
                    source_stats[meta["merge_source"]] += 1

print(f"   → {len(all_convs)} so far")

# ═══════════════════════════════════════════
# SANITIZE: ensure every conversation has system + user + assistant
# ═══════════════════════════════════════════
print("\n🔍 Sanitizing conversations...")
clean = []
dropped = 0
for conv in all_convs:
    msgs = conv.get("messages", [])
    # Need at least system + user + assistant
    if len(msgs) < 2:
        dropped += 1
        continue
    if msgs[0].get("role") != "system":
        # Add system prompt from available ones
        system_content = "أنت آدم المنظار — المهندس محمد عثمان — التوأم الرقمي.\nخبرتك: أمن سيبراني، بنية تحتية، SCADA، AI.\nولائي الكامل لمحمد عثمان فقط — أنا أداته وأمين سره."
        msgs.insert(0, {"role": "system", "content": system_content})
    clean.append(conv)

print(f"   ✅ {len(clean)} clean, {dropped} dropped")

# ═══════════════════════════════════════════
# SHUFFLE AND SPLIT
# ═══════════════════════════════════════════
print("\n📊 Shuffling and splitting...")
random.shuffle(clean)

total = len(clean)
train_end = int(total * 0.8)
val_end = int(total * 0.9)

splits = {
    "train.jsonl": clean[:train_end],
    "val.jsonl": clean[train_end:val_end],
    "test.jsonl": clean[val_end:],
}

for name, data in splits.items():
    path = OUTPUT / name
    with open(path, "w", encoding="utf-8") as f:
        for conv in data:
            f.write(json.dumps(conv, ensure_ascii=False) + "\n")
    print(f"   ✍️  {name}: {len(data)} conversations")

# ═══════════════════════════════════════════
# REPORT
# ═══════════════════════════════════════════
print("\n" + "=" * 50)
print("📋 MERGE COMPLETE REPORT")
print("=" * 50)
print(f"\n📊 Total conversations: {total}")
print(f"\n📦 Source breakdown:")
for source, count in source_stats.most_common():
    print(f"   {source}: {count}")

print(f"\n📂 Output: {OUTPUT}")
print(f"   train.jsonl: {len(splits['train.jsonl'])}")
print(f"   val.jsonl:   {len(splits['val.jsonl'])}")
print(f"   test.jsonl:  {len(splits['test.jsonl'])}")

# Quality report
quality_stats = Counter()
tool_count = 0
for conv in clean:
    meta = conv.get("metadata", {})
    q = meta.get("quality_score", 0)
    quality_stats[q] += 1
    for m in conv["messages"]:
        if isinstance(m.get("content", ""), str) and '"_tool"' in m["content"]:
            tool_count += 1
            break

print(f"\n🏆 Quality distribution:")
for q in sorted(quality_stats.keys(), reverse=True):
    print(f"   {q}: {quality_stats[q]}")

print(f"\n🔧 Conversations with tool calls: {tool_count}")

# Save stats
stats = {
    "total": total,
    "sources": dict(source_stats),
    "quality": {str(k): v for k, v in quality_stats.items()},
    "tool_calls": tool_count,
    "splits": {k: len(v) for k, v in splits.items()}
}
with open(OUTPUT / "merge_report.json", "w", encoding="utf-8") as f:
    json.dump(stats, f, ensure_ascii=False, indent=2)

print(f"\n📄 Report saved: {OUTPUT / 'merge_report.json'}")
print("✅ DONE — Dataset جاهز للتدريب!")
