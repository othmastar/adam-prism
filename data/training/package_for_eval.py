#!/usr/bin/env python3
"""Package current state for cloud evaluation"""

import json
import os
import tarfile
import shutil
from datetime import datetime

BASE = "/mnt/Workspace/Adam_Prism_Complete_v2/data/training"
OUT = "/mnt/Workspace/Adam_Prism_Complete_v2/data/training/eval_package"
os.makedirs(OUT, exist_ok=True)

now = datetime.now().strftime("%Y%m%d_%H%M%S")
pkg = os.path.join(OUT, f"adam_eval_package_{now}.tar.gz")

# 1. Consciousness data (80 conversations)
shutil.copytree(
    f"{BASE}/consciousness_data",
    f"{OUT}/consciousness_data",
    dirs_exist_ok=True
)

# 2. Consciousness YAML files
yaml_src = f"{BASE}/conversations/كونسكونشز "
if os.path.exists(yaml_src):
    shutil.copytree(
        yaml_src,
        f"{OUT}/consciousness_yaml",
        dirs_exist_ok=True
    )

# 3. v2 raw data (396 conversations)
shutil.copytree(
    f"{BASE}/raw_training_v2",
    f"{OUT}/raw_training_v2",
    dirs_exist_ok=True
)

# 4. current state — what RTX 3060 processed so far
with open(f"{BASE}/bulk_rewrite_state.json") as f:
    state = json.load(f)
    processed_count = state["processed"]

src_dir = f"{BASE}/final_dataset"
os.makedirs(f"{OUT}/rewritten", exist_ok=True)
for fname in os.listdir(src_dir) if os.path.isdir(src_dir) else []:
    shutil.copy2(os.path.join(src_dir, fname), f"{OUT}/rewritten/{fname}")

# 5. Write evaluation manifest
manifest = {
    "generated": now,
    "contents": {
        "consciousness_data": "80 conversations (train=64, val=8, test=8)",
        "consciousness_yaml": "core_v2 + expansion_v3 (12 layers)",
        "raw_training_v2": f"396 v2-quality conversations",
        "rewritten": f"{processed_count}/2205 conversations rewritten so far",
        "total_ready": 396 + 80 + processed_count,
    },
    "rewrite_state": state.get("processed", 0),
    "instructions": "",
}

with open(f"{OUT}/manifest.json", "w") as f:
    json.dump(manifest, f, indent=2, ensure_ascii=False)

# Create tarball
with tarfile.open(pkg, "w:gz") as tar:
    tar.add(OUT, arcname=os.path.basename(OUT))

print(f"Package: {pkg}")
print(f"Size: {os.path.getsize(pkg) / 1024 / 1024:.1f} MB")
print(f"Consciousness: 80 conversations + 2 YAML files")
print(f"v2 raw: 396 conversations")
print(f"Rewritten: {processed_count} conversations (partial)")
print(f"Total: {396 + 80 + processed_count} conversations ready for eval")

# Cleanup temp files
for item in os.listdir(OUT):
    item_path = os.path.join(OUT, item)
    if item != os.path.basename(pkg):
        if os.path.isdir(item_path):
            shutil.rmtree(item_path)
        else:
            os.remove(item_path)

os.rename(pkg, os.path.join(OUT, "adam_eval_package.tar.gz"))
print(f"\nFinal: {OUT}/adam_eval_package.tar.gz")
