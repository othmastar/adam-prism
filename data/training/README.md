# Training Data — Showcase Version

This directory is intentionally **empty** in the public showcase version.

## What lives here in the full version

The full Adam Prism deployment includes ~2,300+ real conversations between
users and the Adam agent, used for:

1. **Fine-tuning** the base LLM (Qwen 2.5 / Llama 3.x) with LoRA adapters
2. **Reflection memory** — when Adam makes a mistake, the correction goes here
3. **Curriculum learning** — selecting harder examples as Adam improves

## Why it's not in the showcase

These conversations are:
- **Private** — they may contain PII, business logic, or personal opinions
- **Proprietary** — they encode the "soul" of the Adam agent
- **Large** — ~15 MB of curated JSONL

## How to use Adam Prism without it

Adam Prism ships with:
- A base system prompt (`adam/prompts/system.md`)
- A reflection engine that learns from runtime corrections
- A self-improvement loop that creates new training examples on the fly

You don't need pre-existing training data. Run:

```bash
python main.py --port 8001
```

…and start chatting. Adam will learn from you.

## For the full version

The full version (private branch `main`) includes:
- 2,317 curated conversations (Arabic + English)
- 1.1 GB of LoRA adapter weights (`checkpoints/`)
- Reflection database with 12k+ entries
- Per-tenant memory partitions

Contact: othman@adam-prism.local
