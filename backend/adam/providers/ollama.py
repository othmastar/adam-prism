"""
Adam Prism — Ollama Provider
"""

import httpx
import logging
from typing import Dict, Any, List, Optional

from adam.providers.base import BaseProvider

logger = logging.getLogger("adam_prism.providers.ollama")


class OllamaProvider(BaseProvider):
    name = "ollama"

    def __init__(self, config: Dict[str, Any]):
        self.base_url = config.get("ollama_base", "http://localhost:11434")
        self.model = config.get("model_name", "adam-prism-v13:latest")
        self.context_window = config.get("context_window", 4096)

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        options = {
            "num_ctx": kwargs.get("context_window", self.context_window),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
        }
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(180.0)) as c:
                r = await c.post("/api/chat", json={
                    "model": self.model,
                    "messages": messages,
                    "stream": False,
                    "options": options,
                })
                r.raise_for_status()
                return r.json().get("message", {}).get("content", "")
        except Exception as e:
            logger.warning(f"Ollama chat failed: {e}")
            raise

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        timeout = kwargs.get("timeout", 60.0)
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(timeout)) as c:
                r = await c.post("/api/generate", json={
                    "model": self.model,
                    "prompt": prompt,
                    "system": system,
                    "stream": False,
                    "options": {
                        "num_ctx": self.context_window,
                        "temperature": 0.7,
                        "top_p": 0.9,
                    },
                })
                r.raise_for_status()
                return r.json().get("response", "")
        except Exception as e:
            logger.warning(f"Ollama generate failed: {e}")
            raise

    async def chat_stream(self, messages: List[Dict], **kwargs):
        try:
            async with httpx.AsyncClient(base_url=self.base_url, timeout=httpx.Timeout(300.0)) as c:
                async with c.stream("POST", "/api/chat", json={
                    "model": self.model,
                    "messages": messages,
                    "stream": True,
                    "options": {
                        "num_ctx": self.context_window,
                        "temperature": 0.7,
                    },
                }) as r:
                    async for line in r.aiter_lines():
                        if line.strip():
                            try:
                                chunk = __import__("json").loads(line)
                                content = chunk.get("message", {}).get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                pass
        except Exception as e:
            logger.warning(f"Ollama stream failed: {e}")
            raise
