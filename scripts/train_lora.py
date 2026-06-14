#!/usr/bin/env python3
"""
QLoRA Fine-tuning for gemma-4-E4B-it on OthMastar thinking patterns.
Updated per digital_twin_correction_guide.html:
  - LoRA rank 32, alpha 64
  - lr 1.5e-4, warmup 0.05, weight_decay 0.05
  - Label masking with -100 for user tokens
  - Data validation before training
"""

import json
import os
import sys
from pathlib import Path

import torch
from transformers import (
    AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig,
    TrainingArguments, Trainer, DataCollatorForSeq2Seq,
)
from peft import LoraConfig, get_peft_model, prepare_model_for_kbit_training
from datasets import Dataset

MODEL_NAME = "google/gemma-4-E4B-it"
DATASET_PATH = "train.jsonl"
EVAL_DATASET_PATH = "val.jsonl"
OUTPUT_DIR = "lora_othmastar"

# === Updated hyperparams (Step 2) ===
LORA_RANK = 32
LORA_ALPHA = 64
LORA_DROPOUT = 0.1
TARGET_MODULES = ["q_proj", "k_proj", "v_proj", "o_proj", "gate_proj", "up_proj", "down_proj"]
USE_4BIT = True
BATCH_SIZE = 4
GRADIENT_ACCUMULATION = 4
LEARNING_RATE = 1.5e-4
NUM_EPOCHS = 3
MAX_LENGTH = 2048
WARMUP_RATIO = 0.05
WEIGHT_DECAY = 0.05

# === Step 3: Conversation structure validation ===
def validate_conversation_structure(data):
    errors = []
    warnings = []
    for i, example in enumerate(data):
        msgs = example.get("messages", [])
        if len(msgs) < 2:
            errors.append(f"Conv {i}: less than 2 messages")
            continue
        if msgs[0].get("role") != "system":
            warnings.append(f"Conv {i}: no system message")
        roles = [m["role"] for m in msgs]
        for j in range(1, len(roles)):
            if roles[j] not in ("user", "assistant"):
                errors.append(f"Conv {i}: pos {j} has invalid role '{roles[j]}'")
        asst_count = sum(1 for r in roles if r == "assistant")
        if asst_count == 0:
            errors.append(f"Conv {i}: no assistant messages")
        for j, msg in enumerate(msgs):
            content = msg.get("content", "").strip()
            if not content:
                errors.append(f"Conv {i}: empty content in pos {j} ({msg.get('role')})")
    if errors:
        print(f"[!] {len(errors)} errors:")
        for e in errors[:15]:
            print(f"    {e}")
        sys.exit(1)
    if warnings:
        print(f"[~] {len(warnings)} warnings:")
        for w in warnings[:10]:
            print(f"    {w}")
    print(f"[OK] {len(data)} conversations validated")
    return True

def load_dataset(path):
    if not os.path.exists(path):
        print(f"[!] Dataset not found: {path}")
        sys.exit(1)
    with open(path, encoding="utf-8") as f:
        data = [json.loads(line) for line in f if line.strip()]
    print(f"[OK] Loaded {len(data)} examples")
    validate_conversation_structure(data)
    return data

def format_chat(examples, tokenizer):
    texts = []
    for messages in examples["messages"]:
        text = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        texts.append(text)
    return texts

# === Step 1: Label masking (handles multi-turn: only train on ASSISTANT tokens) ===
def tokenize_with_masking(examples, tokenizer):
    all_input_ids, all_labels, all_attention_mask = [], [], []

    role_markers = {
        "system": tokenizer.encode("<|system|>", add_special_tokens=False),
        "user": tokenizer.encode("<|user|>", add_special_tokens=False),
        "assistant": tokenizer.encode("<|assistant|>", add_special_tokens=False),
    }

    for messages in examples["messages"]:
        formatted = tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=False
        )
        tokenized = tokenizer(
            formatted,
            truncation=True,
            max_length=MAX_LENGTH,
            add_special_tokens=True,
        )
        input_ids = tokenized["input_ids"]
        labels = [-100] * len(input_ids)

        marker_positions = []
        for role, marker_ids in role_markers.items():
            ml = len(marker_ids)
            for pos in range(len(input_ids) - ml + 1):
                if input_ids[pos:pos + ml] == marker_ids:
                    marker_positions.append((pos, role))
        marker_positions.sort()

        for i, (pos, role) in enumerate(marker_positions):
            if role == "assistant":
                content_start = pos + len(role_markers["assistant"])
                content_end = len(input_ids)
                if i + 1 < len(marker_positions):
                    content_end = marker_positions[i + 1][0]
                for j in range(content_start, content_end):
                    labels[j] = input_ids[j]

        all_input_ids.append(input_ids)
        all_labels.append(labels)
        all_attention_mask.append(tokenized["attention_mask"])

    return {
        "input_ids": all_input_ids,
        "labels": all_labels,
        "attention_mask": all_attention_mask,
    }

def verify_masking(tokenized_batch):
    import numpy as np
    labels = np.array(tokenized_batch["labels"])
    masked = (labels == -100).sum()
    total = labels.size
    ratio = masked / total
    print(f"  Mask ratio: {ratio:.1%} ({masked}/{total})")
    assert 0.10 < ratio < 0.99, f"Mask ratio {ratio:.1%} out of range!"
    last_10 = labels[:, -10:]
    assert (last_10 != -100).any(), "End of sequence fully masked!"
    assert (labels != -100).any(), "No trainable tokens!"
    return True

def main():
    print("=" * 50)
    print("QLoRA Training — OthMastar Digital Twin")
    print("=" * 50)

    print("\n[1/5] Loading and validating datasets...")
    raw_train = load_dataset(DATASET_PATH)
    raw_eval = load_dataset(EVAL_DATASET_PATH)
    dataset = Dataset.from_list(raw_train)
    eval_dataset = Dataset.from_list(raw_eval)
    print(f"  Train: {len(raw_train)} | Eval: {len(raw_eval)}")

    print("\n[2/5] Loading model (4-bit)...")
    bnb_config = BitsAndBytesConfig(
        load_in_4bit=True,
        bnb_4bit_quant_type="nf4",
        bnb_4bit_compute_dtype=torch.bfloat16,
        bnb_4bit_use_double_quant=True,
    )
    model = AutoModelForCausalLM.from_pretrained(
        MODEL_NAME,
        quantization_config=bnb_config,
        device_map="auto",
        torch_dtype=torch.bfloat16,
        attn_implementation="flash_attention_2" if torch.cuda.is_available() else "sdpa",
        token=os.environ.get("HF_TOKEN", None),
    )
    tokenizer = AutoTokenizer.from_pretrained(
        MODEL_NAME, token=os.environ.get("HF_TOKEN", None),
    )
    if tokenizer.pad_token is None:
        tokenizer.pad_token = tokenizer.eos_token

    print("\n[3/5] Configuring LoRA (rank=32, alpha=64)...")
    model = prepare_model_for_kbit_training(model)
    lora_config = LoraConfig(
        r=LORA_RANK,
        lora_alpha=LORA_ALPHA,
        target_modules=TARGET_MODULES,
        lora_dropout=LORA_DROPOUT,
        bias="none",
        task_type="CAUSAL_LM",
    )
    model = get_peft_model(model, lora_config)
    model.print_trainable_parameters()

    print("\n[4/5] Tokenizing with label masking...")
    tokenized_train = dataset.map(
        lambda x: tokenize_with_masking(x, tokenizer),
        batched=True,
        remove_columns=dataset.column_names,
    )
    tokenized_eval = eval_dataset.map(
        lambda x: tokenize_with_masking(x, tokenizer),
        batched=True,
        remove_columns=eval_dataset.column_names,
    )
    verify_masking(tokenized_train[:2])
    print(f"  Train: {len(tokenized_train)} | Eval: {len(tokenized_eval)}")

    print("\n[5/5] Starting training...")
    training_args = TrainingArguments(
        output_dir=OUTPUT_DIR,
        per_device_train_batch_size=BATCH_SIZE,
        per_device_eval_batch_size=BATCH_SIZE,
        gradient_accumulation_steps=GRADIENT_ACCUMULATION,
        learning_rate=LEARNING_RATE,
        num_train_epochs=NUM_EPOCHS,
        warmup_ratio=WARMUP_RATIO,
        weight_decay=WEIGHT_DECAY,
        logging_steps=10,
        evaluation_strategy="steps",
        eval_steps=20,
        save_strategy="steps",
        save_steps=50,
        save_total_limit=2,
        load_best_model_at_end=True,
        metric_for_best_model="loss",
        greater_is_better=False,
        fp16=not torch.cuda.is_bf16_supported(),
        bf16=torch.cuda.is_bf16_supported(),
        report_to="none",
        remove_unused_columns=False,
        dataloader_num_workers=2,
        gradient_checkpointing=True,
        optim="paged_adamw_8bit",
    )

    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=tokenized_train,
        eval_dataset=tokenized_eval,
        tokenizer=tokenizer,
        data_collator=DataCollatorForSeq2Seq(tokenizer, pad_to_multiple_of=8),
    )

    trainer.train()

    final_output = Path(OUTPUT_DIR) / "final"
    trainer.model.save_pretrained(str(final_output))
    tokenizer.save_pretrained(str(final_output))
    size_mb = sum(f.stat().st_size for f in final_output.rglob("*")) / 1024 / 1024
    print(f"\n[OK] Adapter saved: {final_output} ({size_mb:.1f} MB)")

    print("\n    To use with Ollama:")
    print("    1. Convert to GGUF: python convert-lora-to-gguf.py " + str(final_output))
    print("    2. Modelfile:")
    print("       FROM gemma4:e4b")
    print("       ADAPTER ./lora.gguf")
    print("    3. ollama create othmastar -f Modelfile")

if __name__ == "__main__":
    main()
