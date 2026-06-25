"""
Adam Prism — Multi-Provider Manager
====================================
يدير كل providers، يدعم auto-fallback (لو واحد وقع، جرب التاني)
"""

import logging
from typing import Any

from adam.providers.anthropic import AnthropicProvider
from adam.providers.base import BaseProvider
from adam.providers.ollama import OllamaProvider
from adam.providers.openai import OpenAIProvider

logger = logging.getLogger("adam_prism.providers")

class ProviderManager:
    """مدير مقدمي النماذج — يدعم auto-fallback + streaming"""

    def __init__(self, config: dict[str, Any] | None = None):
        self.config = config or {}
        self.fallback_order = self.config.get("provider_fallback", ["ollama", "openai", "anthropic"])
        self.mode = self.config.get("inference_mode", "ollama")
        self._providers: dict[str, BaseProvider] = {}
        self._init_providers()

    def _init_providers(self):
        for name in self.fallback_order:
            provider = self._create_provider(name)
            if provider:
                self._providers[name] = provider

    def _create_provider(self, name: str) -> BaseProvider | None:
        try:
            if name == "ollama":
                return OllamaProvider(self.config)
            elif name == "openai":
                return OpenAIProvider(self.config)
            elif name == "anthropic":
                return AnthropicProvider(self.config)
        except Exception:
            logger.exception("Failed to init provider '{name}':")
        return None

    @property
    def current(self) -> BaseProvider | None:
        """الـ provider النشط حالياً"""
        return self._providers.get(self.mode)

    def set_mode(self, mode: str):
        if mode in self._providers:
            self.mode = mode
            logger.info(f"🔄 Switched to provider: {mode}")
        else:
            logger.warning(f"Provider '{mode}' غير متاح، المتاح: {list(self._providers.keys())}")

    def list_providers(self) -> list[str]:
        return list(self._providers.keys())

    async def chat(self, messages: list[dict], **kwargs) -> str:
        """يحاول مع الـ provider الحالي، لو تعذر يجرب الباقي (auto-fallback)"""
        errors = []

        # Try current mode first
        if self.current:
            try:
                return await self.current.chat(messages, **kwargs)
            except Exception as e:
                errors.append(f"{self.mode}: {e}")
                logger.exception("⚠️ {self.mode} failed, will fallback:")
        else:
            errors.append(f"{self.mode}: not initialized")

        # Auto-fallback للمتاحين
        for name, provider in self._providers.items():
            if name == self.mode:
                continue
            try:
                logger.info(f"🔄 Falling back to {name}")
                return await provider.chat(messages, **kwargs)
            except Exception as e:
                errors.append(f"{name}: {e}")

        logger.error(f"All providers failed: {'; '.join(errors)}")
        return ""

    async def generate(self, prompt: str, system: str = "", **kwargs) -> str:
        if self.current:
            try:
                return await self.current.generate(prompt, system, **kwargs)
            except Exception:
                logger.exception("⚠️ {self.mode} generate failed:")
        return ""

    async def chat_stream(self, messages: list[dict], **kwargs):
        """Streaming مع auto-fallback"""
        if self.current:
            try:
                async for chunk in self.current.chat_stream(messages, **kwargs):
                    yield chunk
                return
            except Exception:
                logger.exception("⚠️ {self.mode} stream failed:")

        for name, provider in self._providers.items():
            if name == self.mode:
                continue
            try:
                async for chunk in provider.chat_stream(messages, **kwargs):
                    yield chunk
                return
            except Exception:
                pass
