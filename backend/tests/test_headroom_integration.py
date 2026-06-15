"""Tests for Headroom context compression integration.

Verifies:
  - AdamHeadroom wrapper works with/without headroom-ai installed
  - Short content is not compressed (under threshold)
  - Long content is compressed (or counted in audit mode)
  - Stats tracking is correct
  - Compression decorator works on tool functions
  - The /api/compression endpoints return valid data
"""
from __future__ import annotations

import json
import os

import pytest


# ── AdamHeadroom core ─────────────────────────────────────────────────
class TestAdamHeadroom:
    def test_headroom_available_flag(self):
        from adam.observability.headroom_integration import _HEADROOM_AVAILABLE
        # Should be a bool
        assert isinstance(_HEADROOM_AVAILABLE, bool)

    def test_init_default_mode(self):
        from adam.observability.headroom_integration import AdamHeadroom
        hr = AdamHeadroom()
        assert hr._mode_str == "audit"
        assert hr._total_calls == 0

    def test_init_custom_mode(self):
        from adam.observability.headroom_integration import AdamHeadroom
        hr = AdamHeadroom(mode="optimize")
        assert hr._mode_str == "optimize"

    def test_init_from_env(self, monkeypatch):
        monkeypatch.setenv("ADAM_HEADROOM_MODE", "simulate")
        from adam.observability.headroom_integration import AdamHeadroom
        hr = AdamHeadroom()
        assert hr._mode_str == "simulate"

    def test_compress_short_content_passthrough(self):
        from adam.observability.headroom_integration import AdamHeadroom
        hr = AdamHeadroom()
        # Short content (< 500 tokens) should pass through unchanged
        result = hr.compress("Hello world")
        assert result.was_compressed is False
        assert result.content == "Hello world"
        assert result.ratio == 1.0

    def test_compress_long_content_in_audit(self):
        from adam.observability.headroom_integration import AdamHeadroom
        hr = AdamHeadroom(mode="audit")
        long_content = "x" * 5000  # ~1400 tokens
        result = hr.compress(long_content)
        # In audit mode, content is unchanged but stats are tracked
        assert result.content == long_content
        assert result.original_tokens > 500
        # Audit mode: was_compressed should be False
        assert result.was_compressed is False

    def test_stats_structure(self):
        from adam.observability.headroom_integration import AdamHeadroom
        hr = AdamHeadroom()
        hr.compress("x" * 5000)
        stats = hr.stats()
        assert "mode" in stats
        assert "headroom_available" in stats
        assert "total_calls" in stats
        assert stats["total_calls"] == 1
        assert stats["original_tokens"] > 0

    def test_compression_result_dataclass(self):
        from adam.observability.headroom_integration import CompressionResult
        r = CompressionResult(
            content="x" * 100,
            original_tokens=1000,
            compressed_tokens=200,
            ratio=0.2,
            was_compressed=True,
        )
        assert r.tokens_saved == 800
        assert r.cost_saved_usd > 0
        # 800 tokens at $5/1M = 0.004 USD
        assert abs(r.cost_saved_usd - 0.004) < 0.0001

    def test_singleton_get_headroom(self):
        from adam.observability.headroom_integration import get_headroom, reset_headroom
        reset_headroom()
        h1 = get_headroom()
        h2 = get_headroom()
        assert h1 is h2  # same singleton
        reset_headroom()


# ── compression_decorator ─────────────────────────────────────────────
class TestCompressionDecorator:
    def test_decorator_passes_through_non_string(self):
        from adam.observability.compression_decorator import compress_tool

        @compress_tool()
        def get_count() -> int:
            return 42

        assert get_count() == 42

    def test_decorator_passes_through_short_string(self):
        from adam.observability.compression_decorator import compress_tool

        @compress_tool()
        def get_greeting() -> str:
            return "Hello"

        result = get_greeting()
        assert result == "Hello"

    def test_decorator_preserves_metadata(self):
        from adam.observability.compression_decorator import compress_tool

        @compress_tool(content_type="json", threshold_tokens=1000)
        def my_tool() -> str:
            """Tool docstring."""
            return "data"

        assert my_tool.__adam_compressed__ is True
        assert my_tool.__adam_compression_config__["content_type"] == "json"
        assert my_tool.__adam_compression_config__["threshold_tokens"] == 1000
        assert my_tool.__doc__ == "Tool docstring."

    def test_decorator_processes_long_string(self):
        from adam.observability.compression_decorator import compress_tool

        @compress_tool()
        def get_long_data() -> str:
            return "y" * 5000

        result = get_long_data()
        # Should either be unchanged (audit/no-op) or compressed
        # Just verify it returns a string
        assert isinstance(result, str)
        assert len(result) > 0

    def test_get_compression_stats(self):
        from adam.observability.compression_decorator import get_compression_stats
        stats = get_compression_stats()
        assert "total_calls" in stats
        assert "original_tokens" in stats


# ── /api/compression endpoints ───────────────────────────────────────
class TestCompressionEndpoints:
    @pytest.fixture
    def client(self):
        os.environ["ADAM_API_KEY"] = "test"
        os.environ["ADAM_PRODUCTION"] = "0"
        os.environ.setdefault("ADAM_HEADROOM_MODE", "audit")
        from adam.api.server_minimal import create_app
        app = create_app()
        from fastapi.testclient import TestClient
        return TestClient(app)

    def test_get_compression_stats(self, client):
        resp = client.get("/api/compression")
        assert resp.status_code == 200
        data = resp.json()
        assert "compression" in data
        assert "description" in data
        assert data["compression"]["mode"] == "audit"

    def test_post_compression_test_short(self, client):
        resp = client.post(
            "/api/compression/test",
            json={"content": "Hello world", "content_type": "text"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "original_tokens" in data
        assert "compressed_tokens" in data
        assert "was_compressed" in data
        # Short content should not be compressed
        assert data["was_compressed"] is False

    def test_post_compression_test_long(self, client):
        long_text = json.dumps({"data": list(range(500))}) * 3
        resp = client.post(
            "/api/compression/test",
            json={"content": long_text, "content_type": "json"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["original_tokens"] > 500
        # In audit mode, was_compressed is False but stats are tracked
        assert "tokens_saved" in data


# ── Token estimation ───────────────────────────────────────────────
class TestTokenEstimation:
    def test_estimate_empty(self):
        from adam.observability.headroom_integration import _estimate_tokens
        assert _estimate_tokens("") == 0

    def test_estimate_short(self):
        from adam.observability.headroom_integration import _estimate_tokens
        n = _estimate_tokens("Hello world")
        # 11 chars / 3.5 = ~3 tokens
        assert 2 <= n <= 5

    def test_estimate_long(self):
        from adam.observability.headroom_integration import _estimate_tokens
        n = _estimate_tokens("x" * 1000)
        # 1000 / 3.5 = ~285 tokens
        assert 250 <= n <= 320
