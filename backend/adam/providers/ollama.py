"""
Adam Prism — Ollama Provider
"""

import json
import logging
from typing import Any

import httpx

from adam.providers.base import BaseProvider

logger = logging.getLogger("adam_prism.providers.ollama")

class OllamaProvider(BaseProvider):
    name = "ollama"
    supports_vision = False

    def __init__(self, config: dict[str, Any]):
        self.base_url = config.get("ollama_base", "http://localhost:11434")
        self.model = config.get("model_name", "adam-prism-v13:latest")
        self.context_window = config.get("context_window", 4096)
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            timeout=httpx.Timeout(180.0),
            limits=httpx.Limits(max_keepalive_connections=10, max_connections=20, keepalive_expiry=60.0),
        )

    async def aclose(self):
        """Close the persistent HTTP client"""
        if self._client and not self._client.is_closed:
            await self._client.aclose()

    async def chat(self, messages: list[dict], **kwargs) -> str:
        options = {
            "num_ctx": kwargs.get("context_window", self.context_window),
            "temperature": kwargs.get("temperature", 0.7),
            "top_p": kwargs.get("top_p", 0.9),
        }
        try:
            r = await self._client.post("/api/chat", json={
                "model": self.model,
                "messages": messages,
                "stream": False,
                "options": options,
            })
            if r.status_code == 400 and "does not support image" in r.text:
                raise ValueError("هذا الموديل لا يدعم الصور. استخدم موديل multimodal.")
            r.raise_for_status()
            return r.json().get("message", {}).get("content", "")
        except ValueError:
            raise
        except Exception:
            logger.exception("Ollama chat failed:")
            raise

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        try:
            r = await self._client.post("/api/generate", json={
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
            if r.status_code == 400 and "does not support image" in r.text:
                raise ValueError("هذا الموديل لا يدعم الصور. استخدم موديل multimodal.")
            r.raise_for_status()
            return r.json().get("response", "")
        except ValueError:
            raise
        except Exception:
            logger.exception("Ollama generate failed:")
            raise

    async def chat_stream(self, messages: list[dict], **kwargs):
        try:
            async with self._client.stream("POST", "/api/chat", json={
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
                            chunk = json.loads(line)
                            content = chunk.get("message", {}).get("content", "")
                            if content:
                                yield content
                        except Exception:
                            pass
        except Exception:
            logger.exception("Ollama stream failed:")
            raise
