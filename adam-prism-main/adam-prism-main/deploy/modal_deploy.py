"""
Modal deployment for Adam Prism Inference (Gemma 4 12B)
Usage: modal deploy deploy/modal_deploy.py
"""
import os, sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

import modal

app = modal.App("adam-prism-inference")

# Use a pre-built image with PyTorch + transformers
image = (
    modal.Image.from_registry("pytorch/pytorch:2.6.0-cuda12.4-cudnn9-devel")
    .pip_install(
        "transformers>=4.49",
        "accelerate",
        "bitsandbytes",
        "fastapi",
        "uvicorn[standard]",
        "pydantic",
        "jinja2",
    )
    .run_commands([
        "pip install flash-attn --no-build-isolation",
    ])
)

MODEL_PATH = "/model"
MODEL_REPO = "google/gemma-4-12b-it"

MINUTES = 60

@app.cls(
    image=image,
    gpu=modal.gpu.A100(count=1, size="40GB"),
    timeout=30 * MINUTES,
    container_idle_timeout=10 * MINUTES,
    volumes={
        MODEL_PATH: modal.Volume.from_name("gemma4-12b", create_if_missing=True),
    },
)
class AdamInference:
    def __init__(self):
        self.model = None
        self.tokenizer = None

    @modal.build()
    def download_model(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        import torch

        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        model = AutoModelForCausalLM.from_pretrained(
            MODEL_REPO,
            quantization_config=bnb,
            device_map="auto",
            trust_remote_code=True,
            attn_implementation="flash_attention_2",
        )
        tokenizer = AutoTokenizer.from_pretrained(MODEL_REPO, trust_remote_code=True)
        model.save_pretrained(MODEL_PATH)
        tokenizer.save_pretrained(MODEL_PATH)

    @modal.enter()
    def load(self):
        from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig
        import torch

        bnb = BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_compute_dtype=torch.float16,
            bnb_4bit_use_double_quant=True,
        )
        self.model = AutoModelForCausalLM.from_pretrained(
            MODEL_PATH,
            quantization_config=bnb,
            device_map="auto",
            trust_remote_code=True,
            local_files_only=True,
            attn_implementation="flash_attention_2",
        )
        self.tokenizer = AutoTokenizer.from_pretrained(MODEL_PATH, trust_remote_code=True, local_files_only=True)

    @modal.web_endpoint(method="POST", label="chat")
    def chat(self, data: dict):
        messages = data.get("messages")
        message = data.get("message")
        if not messages and message:
            messages = [
                {"role": "system", "content": "أنت آدم — الذراع الرقمي للمهندس محمد عثمان."},
                {"role": "user", "content": message},
            ]
        if not messages:
            return {"error": "Missing messages"}

        prompt = self.tokenizer.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=16384)
        inputs = {k: v.to("cuda") for k, v in inputs.items()}

        import torch
        with torch.no_grad():
            out = self.model.generate(**inputs, max_new_tokens=512, temperature=0.3, top_p=0.95, do_sample=True)

        response = self.tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True).strip()
        return {"response": response}


@app.local_entrypoint()
def main():
    print("Deploy with: modal deploy deploy/modal_deploy.py")
    print("Then curl the /chat endpoint from Modal dashboard")
