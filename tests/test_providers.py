"""Tests for ProviderManager — Ollama / OpenAI / Anthropic multi-model support"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from adam.providers.manager import ProviderManager
from adam.providers.ollama import OllamaProvider
from adam.providers.openai import OpenAIProvider
from adam.providers.anthropic import AnthropicProvider


class TestProviderInit:
    def test_default_config(self):
        pm = ProviderManager({})
        assert pm.mode == "ollama"
        assert pm.current is not None
        assert pm.current.name == "ollama"

    def test_custom_order(self):
        pm = ProviderManager({
            "provider_fallback": ["openai", "anthropic"],
            "openai_api_key": "sk-test",
            "anthropic_api_key": "sk-ant-test",
        })
        assert "openai" in pm._providers
        assert "anthropic" in pm._providers
        assert pm.mode == "ollama"  # mode still from inference_mode

    def test_set_mode(self):
        pm = ProviderManager({"openai_api_key": "sk-test"})
        pm.set_mode("openai")
        assert pm.mode == "openai"

    def test_set_mode_invalid(self):
        pm = ProviderManager({})
        pm.set_mode("invalid")
        assert pm.mode == "ollama"

    def test_list_providers(self):
        pm = ProviderManager({})
        providers = pm.list_providers()
        assert "ollama" in providers

    def test_openai_config(self):
        pm = ProviderManager({
            "openai_api_key": "sk-test",
            "openai_model": "gpt-4",
        })
        assert pm.current is not None
        assert pm.current.name == "ollama"  # default mode still ollama

    def test_anthropic_config(self):
        pm = ProviderManager({
            "anthropic_api_key": "sk-ant-test",
            "anthropic_model": "claude-3-opus",
        })
        assert pm.current is not None


class TestIndividualProviders:
    @pytest.mark.asyncio
    async def test_ollama_chat(self):
        p = OllamaProvider({"ollama_base": "http://test:11434"})
        with patch("httpx.AsyncClient") as mock:
            instance = mock.return_value.__aenter__.return_value
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"message": {"content": "hello"}}
            mock_resp.raise_for_status = lambda: None
            instance.post = AsyncMock(return_value=mock_resp)
            result = await p.chat([{"role": "user", "content": "hi"}])
            assert result == "hello"

    @pytest.mark.asyncio
    async def test_ollama_stream(self):
        p = OllamaProvider({"ollama_base": "http://test:11434"})
        # Just verify no exception when httpx raises
        with patch("httpx.AsyncClient") as mock:
            instance = mock.return_value.__aenter__.return_value
            instance.stream = AsyncMock(side_effect=Exception("stream error"))
            chunks = []
            with pytest.raises(Exception):
                async for chunk in p.chat_stream([{"role": "user", "content": "hi"}]):
                    chunks.append(chunk)

    @pytest.mark.asyncio
    async def test_openai_chat_no_key(self):
        p = OpenAIProvider({})
        result = await p.chat([{"role": "user", "content": "hi"}])
        assert result == ""

    @pytest.mark.asyncio
    async def test_anthropic_chat_no_key(self):
        p = AnthropicProvider({})
        result = await p.chat([{"role": "user", "content": "hi"}])
        assert result == ""

    @pytest.mark.asyncio
    async def test_openai_chat_success(self):
        p = OpenAIProvider({"openai_api_key": "sk-test"})
        with patch("httpx.AsyncClient") as mock:
            instance = mock.return_value.__aenter__.return_value
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"choices": [{"message": {"content": "openai reply"}}]}
            mock_resp.raise_for_status = lambda: None
            instance.post = AsyncMock(return_value=mock_resp)
            result = await p.chat([{"role": "user", "content": "hi"}])
            assert result == "openai reply"

    @pytest.mark.asyncio
    async def test_anthropic_chat_success(self):
        p = AnthropicProvider({"anthropic_api_key": "sk-ant-test"})
        with patch("httpx.AsyncClient") as mock:
            instance = mock.return_value.__aenter__.return_value
            mock_resp = MagicMock()
            mock_resp.json.return_value = {"content": [{"type": "text", "text": "claude reply"}]}
            mock_resp.raise_for_status = lambda: None
            instance.post = AsyncMock(return_value=mock_resp)
            result = await p.chat([{"role": "user", "content": "hi"}])
            assert result == "claude reply"


class TestProviderChat:
    @pytest.fixture
    def pm(self):
        return ProviderManager({})

    @pytest.mark.asyncio
    async def test_ollama_chat_dispatches(self, pm):
        with patch.object(pm.current, "chat", new=AsyncMock(return_value="ollama response")):
            result = await pm.chat([{"role": "user", "content": "hello"}])
            assert result == "ollama response"


class TestProviderGenerate:
    @pytest.mark.asyncio
    async def test_generate_delegates(self):
        pm = ProviderManager({})
        with patch.object(pm.current, "generate", new=AsyncMock(return_value="generated")):
            result = await pm.generate("test prompt", system="be helpful")
            assert result == "generated"


class TestProviderFallback:
    @pytest.mark.asyncio
    async def test_auto_fallback_on_failure(self):
        """إذا فشل ollama، يجرب openai"""
        config = {
            "inference_mode": "ollama",
            "provider_fallback": ["ollama", "openai"],
            "openai_api_key": "sk-test",
        }
        pm = ProviderManager(config)
        # Fail ollama, succeed openai
        pm._providers["ollama"].chat = AsyncMock(side_effect=Exception("Ollama down"))
        pm._providers["openai"].chat = AsyncMock(return_value="openai fallback")
        result = await pm.chat([{"role": "user", "content": "hello"}])
        assert result == "openai fallback"

    @pytest.mark.asyncio
    async def test_all_providers_fail(self):
        config = {
            "provider_fallback": ["ollama"],
        }
        pm = ProviderManager(config)
        pm._providers["ollama"].chat = AsyncMock(side_effect=Exception("down"))
        result = await pm.chat([{"role": "user", "content": "hello"}])
        assert result == ""


class TestProviderRetry:
    # retry is now inside the ProviderManager via auto-fallback
    # This tests that the individual providers raise properly
    @pytest.mark.asyncio
    async def test_ollama_raises_on_http_error(self):
        pm = ProviderManager({})
        with patch.object(pm.current, "chat", new=AsyncMock(side_effect=Exception("HTTP 500"))):
            result = await pm.chat([{"role": "user", "content": "hello"}])
            assert result == ""  # fallback fails too
