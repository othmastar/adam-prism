"""
Adam Prism — Provider Base Class
==================================
القاعدة لكل مزودي النماذج: Ollama, OpenAI, Anthropic, ...
"""

from typing import Dict, Any, List, Optional


class BaseProvider:
    """Base class for all LLM providers"""

    name: str = ""
    model: str = ""
    config: Dict[str, Any] = {}

    async def chat(self, messages: List[Dict], **kwargs) -> str:
        raise NotImplementedError

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        raise NotImplementedError

    async def chat_stream(self, messages: List[Dict], **kwargs):
        """Stream response chunks. Yields strings."""
        raise NotImplementedError
