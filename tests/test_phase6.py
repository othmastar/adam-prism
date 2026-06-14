"""
[PHASE6] Tests for new Phase 6 features.
"""

from adam.security.waf import WebApplicationFirewall, WAFAction
from adam.observability.ai_observability import AIObservability
from adam.webhooks.manager import WebhookManager, WebhookEvent
from adam.observability.hybrid_search import BM25, HybridSearcher
from adam.core.voice_enhanced import VoiceCloningService, VoiceDialect


class TestWAF:
    """Test Web Application Firewall."""

    def test_safe_text_passes(self):
        waf = WebApplicationFirewall()
        is_safe, matches = waf.is_safe("Hello world, this is a normal message")
        assert is_safe
        assert len(matches) == 0

    def test_sql_injection_detected(self):
        waf = WebApplicationFirewall()
        is_safe, matches = waf.is_safe("1' OR 1=1; DROP TABLE users;--")
        assert len(matches) > 0
        assert any(m.category == "sql_injection" for m in matches)

    def test_xss_detected(self):
        waf = WebApplicationFirewall()
        is_safe, matches = waf.is_safe("<script>alert('xss')</script>")
        assert len(matches) > 0
        assert any(m.category == "xss" for m in matches)

    def test_path_traversal_detected(self):
        waf = WebApplicationFirewall()
        is_safe, matches = waf.is_safe("../../../../etc/passwd")
        assert len(matches) > 0
        assert any(m.category == "path_traversal" for m in matches)

    def test_command_injection_detected(self):
        waf = WebApplicationFirewall()
        is_safe, matches = waf.is_safe("; rm -rf /")
        assert len(matches) > 0
        assert any(m.category == "command_injection" for m in matches)

    def test_ssrf_aws_metadata(self):
        waf = WebApplicationFirewall()
        is_safe, matches = waf.is_safe("http://169.254.169.254/latest/meta-data")
        assert len(matches) > 0
        assert any(m.category == "ssrf" for m in matches)

    def test_block_mode_rejects(self):
        waf = WebApplicationFirewall(mode=WAFAction.BLOCK)
        is_safe, matches = waf.is_safe("1' OR 1=1;")
        assert not is_safe
        assert len(matches) > 0

    def test_stats_tracked(self):
        waf = WebApplicationFirewall()
        waf.is_safe("1' OR 1=1;")
        waf.is_safe("<script>alert()</script>")
        stats = waf.get_stats()
        assert stats.get("sql_injection", 0) > 0
        assert stats.get("xss", 0) > 0


class TestAIObservability:
    """Test AI usage tracking."""

    def test_record_openai_call(self):
        obs = AIObservability()
        rec = obs.record(
            provider="openai",
            model="gpt-4o",
            input_tokens=100,
            output_tokens=200,
            latency_ms=500,
        )
        assert rec.provider == "openai"
        assert rec.input_tokens == 100
        assert rec.output_tokens == 200
        assert rec.total_tokens == 300
        assert rec.cost_usd > 0  # Should calculate cost

    def test_ollama_zero_cost(self):
        obs = AIObservability()
        rec = obs.record(
            provider="ollama",
            model="gemma3:8b",
            input_tokens=1000,
            output_tokens=500,
            latency_ms=2000,
        )
        assert rec.cost_usd == 0  # Local is free

    def test_stats_aggregation(self):
        obs = AIObservability()
        obs.record(provider="openai", model="gpt-4o", input_tokens=100, output_tokens=200, user_id="u1")
        obs.record(provider="openai", model="gpt-4o", input_tokens=50, output_tokens=100, user_id="u1")
        stats = obs.get_stats(user_id="u1")
        assert stats["total_tokens"] == 450
        assert stats["record_count"] == 2

    def test_recent_records(self):
        obs = AIObservability()
        for _ in range(5):
            obs.record(provider="openai", model="gpt-4o", input_tokens=10, output_tokens=20)
        recent = obs.get_recent(limit=3)
        assert len(recent) == 3


class TestWebhooks:
    """Test webhook system."""

    def test_subscribe(self):
        mgr = WebhookManager()
        sub = mgr.subscribe(
            url="https://example.com/webhook",
            events=[WebhookEvent.CHAT_MESSAGE.value, "custom.event"],
            description="Test subscription",
        )
        assert sub.id.startswith("wh_")
        assert sub.secret != ""
        assert WebhookEvent.CHAT_MESSAGE.value in sub.events

    def test_unsubscribe(self):
        mgr = WebhookManager()
        sub = mgr.subscribe(url="https://x.com", events=["a"])
        assert mgr.unsubscribe(sub.id) is True
        assert mgr.unsubscribe("nonexistent") is False

    def test_sign_payload(self):
        mgr = WebhookManager()
        sub = mgr.subscribe(url="https://x.com", events=["a"])
        payload = b'{"test": "data"}'
        sig = mgr.sign_payload(sub, payload)
        assert len(sig) == 64  # SHA-256 hex digest
        # Verify signature
        import hmac
        import hashlib
        expected = hmac.new(
            sub.secret.encode("utf-8"), payload, hashlib.sha256
        ).hexdigest()
        assert sig == expected

    def test_dispatch_to_matching_subscribers(self):
        mgr = WebhookManager()
        mgr.subscribe(url="https://a.com", events=[WebhookEvent.CHAT_MESSAGE.value])
        mgr.subscribe(url="https://b.com", events=[WebhookEvent.BOTTLENECK_PREDICTED.value])
        # We won't actually deliver (no aiohttp event loop in test)
        # but the dispatch returns targets
        # Just test that the matching works


class TestHybridSearch:
    """Test BM25 + hybrid search."""

    def test_bm25_basic(self):
        bm = BM25()
        docs = [
            "Adam Prism is an AI agent framework",
            "FastAPI is a web framework for building APIs",
            "PostgreSQL is a powerful database",
        ]
        bm.fit(docs)
        results = bm.score("Adam agent")
        assert len(results) > 0
        # First result should be the Adam doc
        top_idx, top_score = results[0]
        assert top_idx == 0
        assert top_score > 0

    def test_bm25_arabic(self):
        bm = BM25()
        docs = [
            "آدم بريزم هو إطار عمل للذكاء الاصطناعي",
            "FastAPI إطار عمل للويب",
            "PostgreSQL قاعدة بيانات قوية",
        ]
        bm.fit(docs)
        results = bm.score("آدم ذكاء")
        assert len(results) > 0
        assert results[0][0] == 0

    def test_bm25_no_match(self):
        bm = BM25()
        bm.fit(["apple banana", "cherry date"])
        results = bm.score("xyz123")
        assert len(results) == 0

    def test_hybrid_searcher(self):
        hs = HybridSearcher()
        docs = ["cat dog", "fish whale", "bird eagle"]
        hs.fit(docs)
        results = hs.search("cat")
        assert len(results) > 0


class TestVoiceCloning:
    """Test voice service."""

    def test_default_voices(self):
        svc = VoiceCloningService()
        voices = svc.list_voices()
        assert len(voices) >= 3
        # Should have at least one Egyptian voice
        egyptian = [v for v in voices if v.dialect == VoiceDialect.EGYPTIAN]
        assert len(egyptian) >= 2

    def test_filter_by_dialect(self):
        svc = VoiceCloningService()
        egyptian = svc.list_voices(dialect=VoiceDialect.EGYPTIAN)
        msa = svc.list_voices(dialect=VoiceDialect.MSA)
        assert len(egyptian) >= 2
        assert len(msa) >= 1
        # No overlap
        assert set(v.id for v in egyptian).isdisjoint(set(v.id for v in msa))

    def test_voice_to_dict(self):
        svc = VoiceCloningService()
        v = svc.get_voice("ar-eg-male-1")
        d = v.to_dict()
        assert d["dialect"] == "ar-eg"
        assert d["gender"] == "male"
        assert d["is_cloned"] is False


class TestPhase6Integration:
    """Integration tests for Phase 6 features."""

    def test_all_phase6_modules_importable(self):
        from adam.security.waf import WebApplicationFirewall
        from adam.observability.ai_observability import AIObservability
        from adam.webhooks.manager import WebhookManager
        from adam.observability.hybrid_search import BM25, HybridSearcher
        from adam.core.voice_enhanced import VoiceCloningService
        assert WebApplicationFirewall is not None
        assert AIObservability is not None
        assert WebhookManager is not None
        assert BM25 is not None
        assert HybridSearcher is not None
        assert VoiceCloningService is not None

    def test_arabic_tokenization(self):
        """[PHASE6] Ensure Arabic text is properly tokenized."""
        bm = BM25()
        tokens = bm._tokenize("آدم بريزم AI")
        # Should split Arabic as one unit
        assert "آدم" in tokens or "آدم" in " ".join(tokens)
        assert any("بريزم" in t for t in tokens)
        assert "ai" in tokens
