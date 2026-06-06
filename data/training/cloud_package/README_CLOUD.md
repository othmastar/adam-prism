# ADAM CLOUD PIPELINE

## Steps
1. Set your HuggingFace token:
   `export HF_TOKEN="your_token_here"`

2. Put your full rewritten data (2205 conversations) in:
   `./rewritten_full/train.jsonl`, `./rewritten_full/val.jsonl`, `./rewritten_full/test.jsonl`

3. Run:
   `python adam_cloud_pipeline.py`

This will:
- Evaluate ALL data quality (consciousness + v2 + rewritten)
- Merge into `./final_dataset/` (train/val/test)
- Show the QLoRA training command

## File Structure Expected:
```
cloud_package/
├── adam_cloud_pipeline.py    ← main pipeline
├── train_lora.py             ← QLoRA training script
├── consciousness_data/       ← 80 conversations (train/val/test)
├── raw_training_v2/          ← 396 v2 conversations
├── rewritten_full/           ← YOUR 2205 rewritten conversations
└── adam_eval_package.tar.gz  ← backup package
```

4. For QLoRA training specifically:
   `python train_lora.py --data-dir ./final_dataset --hf-token $HF_TOKEN`

Estimated time on cloud GPU: ~minutes for eval+merge, ~few hours for QLoRA
