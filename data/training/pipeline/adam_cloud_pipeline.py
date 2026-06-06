#!/usr/bin/env python3
"""
adam_cloud_pipeline.py — شغّل على السحابة مباشرة
=================================================
يقيّم، يدمج، ويبدأ QLoRA training
"""

import json
import os
import sys
from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIG
# ------------------------------------------------------------
WORKDIR = Path(os.path.dirname(os.path.abspath(__file__)))
HF_TOKEN = os.environ.get("HF_TOKEN", "")  # Set this before running

DATA_DIRS = {
    "consciousness": WORKDIR / "consciousness_data",
    "v2_raw": WORKDIR / "raw_training_v2",
    "rewritten": WORKDIR / "rewritten_full",  # Your 2205 from cloud
}
OUTPUT_DIR = WORKDIR / "final_dataset"
TRAIN_SCRIPT = WORKDIR / "train_lora.py"

# ------------------------------------------------------------
# 2. EVALUATE ALL DATA
# ------------------------------------------------------------
def evaluate_jsonl(path, label):
    if not path.exists():
        print(f"⚠️ {label}: path not found")
        return
    count = 0
    total_turns = 0
    user_len = 0
    asst_len = 0
    total_user_msgs = 0
    total_asst_msgs = 0
    with open(path) as f:
        for line in f:
            obj = json.loads(line)
            msgs = obj["messages"]
            count += 1
            turns = len([m for m in msgs if m["role"] != "system"])
            total_turns += turns
            for m in msgs:
                if m["role"] == "user":
                    user_len += len(m["content"])
                    total_user_msgs += 1
                elif m["role"] == "assistant":
                    asst_len += len(m["content"])
                    total_asst_msgs += 1
    avg_turns = total_turns / count if count else 0
    avg_user = user_len / total_user_msgs if total_user_msgs else 0
    avg_asst = asst_len / total_asst_msgs if total_asst_msgs else 0
    print(f"\n📊 {label}:")
    print(f"   Conversations: {count}")
    print(f"   Avg turns: {avg_turns:.1f}")
    print(f"   Avg user len: {avg_user:.0f} chars")
    print(f"   Avg asst len: {avg_asst:.0f} chars")
    v2_ratio = total_user_msgs / total_asst_msgs if total_asst_msgs else 0
    print(f"   User/Asst ratio: {v2_ratio:.2f}")
    return {"count": count, "avg_turns": avg_turns, "avg_user": avg_user, "avg_asst": avg_asst}

# ------------------------------------------------------------
# 3. MERGE ALL DATA
# ------------------------------------------------------------
def merge_all(consciousness_dir, v2_dir, rewritten_paths):
    OUTPUT_DIR.mkdir(exist_ok=True)
    all_data = []

    # Consciousness
    for split in ["train", "val", "test"]:
        f = consciousness_dir / f"{split}.jsonl"
        if f.exists():
            with open(f) as fh:
                for line in fh:
                    obj = json.loads(line)
                    obj["metadata"]["source"] = "consciousness"
                    all_data.append(obj)
            print(f"  + {split}.jsonl from consciousness")

    # v2 raw
    for f in sorted(v2_dir.glob("*.jsonl")):
        with open(f) as fh:
            for line in fh:
                obj = json.loads(line)
                obj["metadata"]["source"] = obj["metadata"].get("source", "v2_raw")
                all_data.append(obj)
        print(f"  + {f.name} from v2_raw")

    # Rewritten
    for f in rewritten_paths:
        if f.exists():
            with open(f) as fh:
                for line in fh:
                    obj = json.loads(line)
                    all_data.append(obj)
            print(f"  + {f.name} from rewritten")

    # Shuffle and split
    import random
    random.shuffle(all_data)
    n = len(all_data)
    train_end = int(n * 0.8)
    val_end = int(n * 0.9)
    splits = {
        "train": all_data[:train_end],
        "val": all_data[train_end:val_end],
        "test": all_data[val_end:],
    }

    for split_name, data in splits.items():
        out_path = OUTPUT_DIR / f"{split_name}.jsonl"
        with open(out_path, "w") as fh:
            for item in data:
                fh.write(json.dumps(item, ensure_ascii=False) + "\n")
        print(f"\n✅ {split_name}: {len(data)} conversations -> {out_path}")

    print(f"\n🎯 TOTAL: {n} conversations")
    return OUTPUT_DIR

# ------------------------------------------------------------
# 4. MAIN
# ------------------------------------------------------------
if __name__ == "__main__":
    print("=" * 50)
    print("ADAM CLOUD PIPELINE")
    print("=" * 50)

    # Step 1: Evaluate
    print("\n🔍 EVALUATION PHASE")
    consciousness_files = list(DATA_DIRS["consciousness"].glob("*.jsonl"))
    v2_files = list(DATA_DIRS["v2_raw"].glob("*.jsonl"))
    rewritten_files = list(DATA_DIRS["rewritten"].glob("*.jsonl"))

    for f in consciousness_files:
        evaluate_jsonl(f, f"consciousness/{f.name}")
    for f in v2_files:
        evaluate_jsonl(f, f"v2/{f.name}")
    for f in rewritten_files:
        evaluate_jsonl(f, f"rewritten/{f.name}")

    # Step 2: Merge
    print("\n\n🔗 MERGE PHASE")
    rewritten_paths = []
    for d in ["train", "val", "test"]:
        p = DATA_DIRS["rewritten"] / f"{d}.jsonl"
        if p.exists():
            rewritten_paths.append(p)
    if not rewritten_paths:
        rewritten_paths = list(DATA_DIRS["rewritten"].glob("*.jsonl"))

    merge_all(DATA_DIRS["consciousness"], DATA_DIRS["v2_raw"], rewritten_paths)

    # Step 3: Train
    if TRAIN_SCRIPT.exists():
        print(f"\n\n🚀 TRAINING PHASE — جاهز")
        print(f"python {TRAIN_SCRIPT} --data {OUTPUT_DIR} --hf-token $HF_TOKEN --mode train")
        import subprocess
        import sys
        hf_token = os.environ.get("HF_TOKEN", "")
        if hf_token:
            print("▶ بدء التدريب تلقائياً... (استخدم nohup لو عاوز تسيبها)")
            result = subprocess.run([
                sys.executable, str(TRAIN_SCRIPT),
                "--data", str(OUTPUT_DIR),
                "--hf-token", hf_token,
                "--mode", "train"
            ])
            if result.returncode == 0:
                print("✅ التدريب اكتمل!")
                print("▶ شغّل: python train_lora.py --mode merge --hf-token $HF_TOKEN")
                print("▶ بعدين: python train_lora.py --mode ollama")
            else:
                print(f"❌ التدريب فشل (كود: {result.returncode})")
        else:
            print("⚠️ HF_TOKEN مش موجود — شغّل التدريب يدوياً:")
            print(f"   python {TRAIN_SCRIPT} --data {OUTPUT_DIR} --hf-token 'your_token' --mode train")
    else:
        print(f"\n⚠️ train_lora.py not found at {TRAIN_SCRIPT}")
