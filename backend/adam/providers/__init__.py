"""
Adam Prism — Multi-Provider System
====================================
Supports: Ollama, OpenAI (and OpenRouter/Groq), Anthropic (Claude)
"""

from adam.providers.base import BaseProvider
from adam.providers.manager import ProviderManager
from adam.providers.ollama import OllamaProvider
from adam.providers.openai import OpenAIProvider
from adam.providers.anthropic import AnthropicProvider

__all__ = ["BaseProvider", "ProviderManager", "OllamaProvider", "OpenAIProvider", "AnthropicProvider"]
