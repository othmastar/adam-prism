"""
Adam Prism — Anthropic (Claude) Provider
"""

import json
import logging
import os
from typing import Any

import httpx

from adam.providers.base import BaseProvider

logger = logging.getLogger("adam_prism.providers.anthropic")


class AnthropicProvider(BaseProvider):
    name = "anthropic"

    def __init__(self, config: dict[str, Any]):
        self.api_key = config.get("anthropic_api_key") or os.getenv("ANTHROPIC_API_KEY", "")
        self.model = config.get("anthropic_model", "claude-sonnet-4-20250514")
        self.api_version = config.get("anthropic_api_version", "2023-06-01")
        self.context_window = config.get("context_window", 8192)

    async def chat(self, messages: list[dict], **kwargs) -> str:
        if not self.api_key:
            logger.warning("Anthropic API key مفقودة")
            return ""

        system_msg = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        try:
            body = {
                "model": kwargs.get("model", self.model),
                "messages": anthropic_messages,
                "max_tokens": kwargs.get("max_tokens", self.context_window),
            }
            if system_msg:
                body["system"] = system_msg

            async with httpx.AsyncClient(timeout=httpx.Timeout(180.0)) as c:
                r = await c.post(
                    "https://api.anthropic.com/v1/messages",
                    headers={
                        "x-api-key": self.api_key,
                        "anthropic-version": self.api_version,
                        "Content-Type": "application/json",
                    },
                    json=body,
                )
                r.raise_for_status()
                data = r.json()
                texts = [block["text"] for block in data.get("content", []) if block.get("type") == "text"]
                return "\n".join(texts)
        except Exception as e:
            logger.warning(f"Anthropic chat failed: {e}")
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

        system_msg = ""
        anthropic_messages = []
        for msg in messages:
            if msg["role"] == "system":
                system_msg = msg["content"]
            else:
                anthropic_messages.append({"role": msg["role"], "content": msg["content"]})

        body = {
            "model": kwargs.get("model", self.model),
            "messages": anthropic_messages,
            "max_tokens": kwargs.get("max_tokens", self.context_window),
            "stream": True,
        }
        if system_msg:
            body["system"] = system_msg

        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(300.0)) as c, c.stream(
                "POST", "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": self.api_key,
                    "anthropic-version": self.api_version,
                    "Content-Type": "application/json",
                },
                json=body,
            ) as r:
                async for line in r.aiter_lines():
                    if line.startswith("data: "):
                        data = line[6:].strip()
                        if data == "[DONE]":
                            break
                        if data:
                            try:
                                chunk = json.loads(data)
                                if chunk.get("type") == "content_block_delta":
                                    delta = chunk.get("delta", {})
                                    if delta.get("type") == "text_delta":
                                        yield delta.get("text", "")
                            except Exception:
                                pass
        except Exception as e:
            logger.warning(f"Anthropic stream failed: {e}")
