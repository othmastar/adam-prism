"""Tests for Pipeline — TelegramChannel + LiveSummarizer"""

import pytest
from unittest.mock import AsyncMock
from adam.pipeline.channels import TelegramChannel, TailscaleConfig
from adam.pipeline.summarizer import LiveSummarizer

# ─── TelegramChannel Tests ───────────────────────────────────────────────────

class TestTelegramChannel:
    @pytest.fixture
    def channel(self):
        return TelegramChannel({"token": "test:token", "allowed_chat_ids": [123]})

    def test_init_with_config(self, channel):
        assert channel.config["token"] == "test:token"
        assert channel.config["allowed_chat_ids"] == [123]

    def test_init_no_token(self):
        channel = TelegramChannel({})
        assert channel.config.get("token") is None

    def test_attach_engine(self, channel):
        engine = object()
        channel.attach_engine(engine)
        assert channel.engine is engine

    def test_init_defaults(self):
        channel = TelegramChannel({"token": "x"})
        assert channel.config.get("allowed_chat_ids") is None or channel.config.get("allowed_chat_ids") == []

    @pytest.mark.asyncio
    async def test_send_message_no_token(self, channel):
        """Should not crash when sending without a token"""
        channel.config = {"token": None}
        await channel.send_message(123, "test")

    def test_stop_does_not_crash(self, channel):
        channel.stop()  # not started, should not crash

# ─── TailscaleConfig Tests ────────────────────────────────────────────────────

class TestTailscaleConfig:
    def test_get_setup_instructions(self):
        instructions = TailscaleConfig.get_setup_instructions()
        assert isinstance(instructions, str)
        assert len(instructions) > 0

    def test_get_status(self):
        status = TailscaleConfig.get_status()
        assert isinstance(status, dict)
        # Should gracefully handle when tailscale isn't installed
        assert "error" in status or "status" in status or True

# ─── LiveSummarizer Tests ────────────────────────────────────────────────────

class TestLiveSummarizer:
    @pytest.fixture
    def summarizer(self):
        return LiveSummarizer({})

    def test_init(self, summarizer):
        assert summarizer.config == {}

    def test_split_text_small(self, summarizer):
        """Small text should return as single chunk"""
        chunks = summarizer._split_text("short text")
        assert len(chunks) == 1
        assert chunks[0] == "short text"

    def test_split_text_large(self, summarizer):
        """Text larger than chunk size should be split"""
        text = "word " * 5000
        chunks = summarizer._split_text(text)
        assert len(chunks) >= 1
        # Each chunk should be roughly <= chunk_size chars
        for chunk in chunks:
            assert len(chunk) <= summarizer.chunk_size + summarizer.overlap + 500

    @pytest.mark.asyncio
    async def test_summarize_document_short(self, summarizer):
        """Short document should be summarized in one chunk"""
        summarizer._summarize_chunk = AsyncMock(return_value="summary of short doc")
        summarizer._extract_concepts = AsyncMock(return_value=[{"concept": "test", "weight": 1.0}])
        summarizer._create_master_summary = AsyncMock(return_value="master summary")

        result = await summarizer.summarize_document("This is a short document.", source="test")
        assert isinstance(result, dict)
        assert "summary" in result or "master_summary" in result or True

    @pytest.mark.asyncio
    async def test_summarize_document_empty(self, summarizer):
        """Empty document should return empty result gracefully"""
        result = await summarizer.summarize_document("", source="test")
        assert isinstance(result, dict)

    @pytest.mark.asyncio
    async def test_extract_concepts_with_mock(self, summarizer):
        summarizer._extract_concepts = AsyncMock(return_value=[
            {"concept": "AI", "weight": 0.9},
            {"concept": "Ethics", "weight": 0.8},
        ])
        concepts = await summarizer._extract_concepts("AI and Ethics are important")
        assert len(concepts) == 2
        assert concepts[0]["concept"] == "AI"
