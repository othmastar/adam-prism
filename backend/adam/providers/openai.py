"""
Adam Prism — OpenAI Provider (also OpenRouter, Groq, etc.)
"""

import json
import logging
import os
from typing import Any

import httpx

from adam.providers.base import BaseProvider

logger = logging.getLogger("adam_prism.providers.openai")


class OpenAIProvider(BaseProvider):
    name = "openai"

    def __init__(self, config: dict[str, Any]):
        self.api_key = config.get("openai_api_key") or os.getenv("OPENAI_API_KEY", "")
        self.base_url = config.get("openai_base") or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        self.model = config.get("openai_model", "gpt-4o")
        self.context_window = config.get("context_window", 4096)

    async def chat(self, messages: list[dict], **kwargs) -> str:
        if not self.api_key:
            logger.warning("OpenAI API key مفقودة")
            return ""
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as c:
                r = await c.post(
                    f"{self.base_url.rstrip('/')}/chat/completions",
                    headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                    json={
                        "model": kwargs.get("model", self.model),
                        "messages": messages,
                        "temperature": kwargs.get("temperature", 0.7),
                        "max_tokens": kwargs.get("max_tokens", self.context_window),
                    },
                )
                r.raise_for_status()
                return r.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.warning(f"OpenAI chat failed: {e}")
            raise

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        messages = []
        if system:
            messages.append({"role": "system", "content": system})
        messages.append({"role": "user", "content": prompt})
        return await self.chat(messages, **kwargs)

    async def chat_stream(self, messages: list[dict], **kwargs):
        if not self.api_key:
            return
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as c, c.stream(
                "POST",
                f"{self.base_url.rstrip('/')}/chat/completions",
                headers={"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"},
                json={
                    "model": kwargs.get("model", self.model),
                    "messages": messages,
                    "temperature": kwargs.get("temperature", 0.7),
                    "stream": True,
                    "max_tokens": kwargs.get("max_tokens", self.context_window),
                },
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        if data:
                            try:
                                chunk = json.loads(data)
                                delta = chunk.get("choices", [{}])[0].get("delta", {})
                                content = delta.get("content", "")
                                if content:
                                    yield content
                            except Exception:
                                pass
        except Exception as e:
            logger.warning(f"OpenAI stream failed: {e}")
