#!/usr/bin/env python3
"""Build othmastar_v6.zip — combine all batches 1-8 (327 DEEP conversations)"""
import json
import os
import random
import zipfile

BASE = "/mnt/Workspace/Adam_Prism_Complete_v2/data/training"
BATCHES = [f"batch{i}_total.json" for i in range(1, 9)]
OUT = os.path.join(BASE, "othmastar_v6.zip")

all_convos = []
for batch_file in BATCHES:
    path = os.path.join(BASE, batch_file)
    if not os.path.exists(path):
        print(f"⚠️  Missing: {batch_file}")
        continue
    with open(path) as f:
        data = json.load(f)
    print(f"📦 {batch_file}: {len(data)} conversations")
    all_convos.extend(data)

print(f"\n📊 Total: {len(all_convos)} conversations")

# Shuffle
random.seed(42)
random.shuffle(all_convos)

# Split 88/6/6
total = len(all_convos)
train_end = int(total * 0.88)
val_end = train_end + int(total * 0.06)

train = all_convos[:train_end]
val = all_convos[train_end:val_end]
test = all_convos[val_end:]

print(f"📊 Train: {len(train)} | Val: {len(val)} | Test: {len(test)}")

# Count tokens
train_tokens = sum(c.get('tokens_est', 0) for c in train)
val_tokens = sum(c.get('tokens_est', 0) for c in val)
test_tokens = sum(c.get('tokens_est', 0) for c in test)

metadata = {
    "version": "v6",
    "total_conversations": total,
    "splits": {"train": len(train), "val": len(val), "test": len(test)},
    "train_tokens": train_tokens,
    "val_tokens": val_tokens,
    "test_tokens": test_tokens,
    "description": f"{total} DEEP conversations — 8 batches, real sources, Arabic, DEEP framework",
    "batches": [b for b in BATCHES if os.path.exists(os.path.join(BASE, b))],
    "model_identity": "MODEL_IDENTITY.md — full persona definition"
}

# Write JSONL files
os.makedirs("/tmp/othmastar_v6/data", exist_ok=True)

def write_jsonl(convos, path):
    with open(path, 'w', encoding='utf-8') as f:
        for c in convos:
            f.write(json.dumps(c, ensure_ascii=False) + '\n')

write_jsonl(train, "/tmp/othmastar_v6/data/train.jsonl")
write_jsonl(val, "/tmp/othmastar_v6/data/val.jsonl")
write_jsonl(test, "/tmp/othmastar_v6/data/test.jsonl")

with open("/tmp/othmastar_v6/data/metadata.json", 'w') as f:
    json.dump(metadata, f, ensure_ascii=False, indent=2)

# Create ZIP
with zipfile.ZipFile(OUT, 'w', zipfile.ZIP_DEFLATED) as zf:
    for fname in ['train.jsonl', 'val.jsonl', 'test.jsonl', 'metadata.json']:
        path = os.path.join("/tmp/othmastar_v6/data", fname)
        zf.write(path, f"data/{fname}")

# Cleanup
import shutil
shutil.rmtree("/tmp/othmastar_v6")

import os
size_kb = os.path.getsize(OUT) / 1024
print(f"\n✅ v6.zip: {total} conversations, {size_kb:.0f} KB")
print(f"   Train: {len(train)} ({train_tokens} tokens)")
print(f"   Val:   {len(val)} ({val_tokens} tokens)")
print(f"   Test:  {len(test)} ({test_tokens} tokens)")
print(f"   Total tokens: {train_tokens + val_tokens + test_tokens}")
print(f"   Saved to: {OUT}")
