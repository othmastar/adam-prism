"""Adam Prism Inference Server — V87 checkpoint (أدوات + أخلاق + وعي)"""
import sys
import os
import gc
import logging
import torch
import warnings
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))

os.environ["PYTORCH_CUDA_ALLOC_CONF"] = "expandable_segments:True"
os.environ["TOKENIZERS_PARALLELISM"] = "false"
os.environ["HF_HOME"] = "/mnt/Workspace/.huggingface"
warnings.filterwarnings("ignore")

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("adam.lora.server")

try:
    import uvicorn
    from fastapi import FastAPI, HTTPException
    from pydantic import BaseModel
    from peft import PeftModel
    from transformers import AutoModelForCausalLM, AutoTokenizer
except ImportError as e:
    logger.error(f"Missing dep: {e}")
    sys.exit(1)

app = FastAPI(title="Adam Prism V87 Inference", version="1.0.0-beta")

class ChatRequest(BaseModel):
    messages: list[dict]
    temperature: float = 0.4
    max_tokens: int = 512
    top_p: float = 0.95

model = None
tokenizer = None
device = None

def load_model():
    global model, tokenizer, device
    BASE = "unsloth/gemma-4-E4B-it-unsloth-bnb-4bit"
    V87_PATH = "/mnt/Workspace/adam_v8_output/تدريب_جيما_29-05-2026/output/checkpoint-500/"

    logger.info("🔥 Loading base E4B on GPU...")
    model = AutoModelForCausalLM.from_pretrained(BASE, device_map="cuda:0", trust_remote_code=True)
    tokenizer = AutoTokenizer.from_pretrained(BASE, trust_remote_code=True)

    for attr in ["vision_tower", "audio_tower"]:
        if hasattr(model.model, attr): delattr(model.model, attr)
    gc.collect(); torch.cuda.empty_cache()

    logger.info("🔄 Loading V87 adapter...")
    model = PeftModel.from_pretrained(model, V87_PATH, local_files_only=True)
    device = next(model.parameters()).device
    vram = torch.cuda.memory_allocated() / 1024**3
    logger.info(f"✅ Ready | VRAM: {vram:.2f} GB | device: {device}")

@app.post("/chat")
async def chat(req: ChatRequest):
    if model is None:
        raise HTTPException(500, "Model not loaded")
    try:
        inputs = tokenizer.apply_chat_template(req.messages, add_generation_prompt=True, return_tensors="pt", truncation=True, max_length=4096)
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.no_grad():
            out = model.generate(**inputs, max_new_tokens=req.max_tokens, temperature=req.temperature, top_p=req.top_p, do_sample=True)
        resp = tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return {"response": resp.strip()}
    except Exception as e:
        logger.error(f"Generation error: {e}")
        raise HTTPException(500, str(e))

@app.get("/health")
async def health():
    return {"status": "ok", "model_loaded": model is not None, "device": str(device) if device else None}

if __name__ == "__main__":
    load_model()
    port = int(os.environ.get("LORA_PORT", 8080))
    logger.info(f"🚀 Server ready on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")
