"""
Adam Prism — Provider Base Class
==================================
القاعدة لكل مزودي النماذج: Ollama, OpenAI, Anthropic, ...
"""

from typing import Any


class BaseProvider:
    """Base class for all LLM providers"""

    name: str = ""
    model: str = ""
    config: dict[str, Any] = {}

    async def chat(self, messages: list[dict], **kwargs) -> str:
        raise NotImplementedError

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        raise NotImplementedError

    async def chat_stream(self, messages: list[dict], **kwargs):
        """Stream response chunks. Yields strings."""
        raise NotImplementedError
