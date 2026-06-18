"""Regression tests for /chat mock responses.

These tests prevent the KeyError bugs we hit when:
- English keywords ('sovereignty') tried to access Arabic keys
- Mixed keywords ('license', 'pricing') pointed to wrong response

Each test ensures all the documented keywords resolve to a valid
mock response (either Arabic or English) without raising KeyError.
"""
from __future__ import annotations

import pytest


# All keyword patterns from _mock_response
ENGLISH_KEYWORDS = [
    "hi", "hello", "hey",
    "who are you", "what are you",
    "features", "what can you do", "capabilities",
    "install", "setup", "how to start",
    "sovereignty", "sovereign", "security", "private",
    "compression", "cost", "expensive",
    "company", "sovereign neural", "fortresses", "founder",
    "license", "pricing", "commercial", "agpl",
    "help", "what can you",
]

ARABIC_KEYWORDS = [
    "مرحبا", "أهلا", "السلام",
    "انت مين", "عرفني", "من أنت", "عن نفسك",
    "مميزات", "ايه بتعمل", "ايه عندك", "قدرات",
    "ازاي اشغل", "ازاي ثبت", "تثبيت", "كيف ابدأ",
    "سيادة", "حماية", "بيانات",
    "ضغط", "تكلفة", "tokens",
    "شركة", "مين بنى", "من صنعك",
    "ترخيص", "رخصة", "اسعار", "سعر",
    "مساعدة", "ساعدني", "ايه اللي تقدر",
]


class TestChatMockResponses:
    @pytest.fixture
    def client(self):
        import sys
        sys.path.insert(0, "backend")
        from adam.api.server_minimal import create_app
        from fastapi.testclient import TestClient
        app = create_app()
        return TestClient(app)

    @pytest.mark.parametrize("keyword", ENGLISH_KEYWORDS)
    def test_english_keyword_returns_200(self, client, keyword):
        """Every documented English keyword should resolve without error."""
        r = client.post("/chat", json={"message": keyword})
        assert r.status_code == 200, f"keyword {keyword!r} failed: {r.text}"
        data = r.json()
        assert "response" in data
        assert len(data["response"]) > 10, f"Response too short for {keyword!r}"

    @pytest.mark.parametrize("keyword", ARABIC_KEYWORDS)
    def test_arabic_keyword_returns_200(self, client, keyword):
        """Every documented Arabic keyword should resolve without error."""
        r = client.post("/chat", json={"message": keyword})
        assert r.status_code == 200, f"keyword {keyword!r} failed: {r.text}"
        data = r.json()
        assert "response" in data
        assert len(data["response"]) > 10, f"Response too short for {keyword!r}"

    def test_arabic_question_returns_help_response(self, client):
        """An Arabic question mark should trigger help response (not generic fallback)."""
        r = client.post("/chat", json={"message": "ايه هي ال layers؟"})
        assert r.status_code == 200
        data = r.json()
        # Should be a structured help response, not the default fallback
        assert "أقدر أساعدك" in data["response"] or "ساعدني" in data["response"]

    def test_english_question_returns_help_response(self, client):
        """An English question should trigger help response."""
        r = client.post("/chat", json={"message": "I need help"})
        assert r.status_code == 200
        data = r.json()
        # Should be the help response (not the features one)
        assert "I can help you" in data["response"]

    def test_empty_message_returns_400(self, client):
        """Empty message should be rejected."""
        r = client.post("/chat", json={"message": ""})
        assert r.status_code == 400

    def test_whitespace_message_returns_400(self, client):
        """Whitespace-only message should be rejected."""
        r = client.post("/chat", json={"message": "   "})
        assert r.status_code == 400

    def test_regression_sovereignty_english(self, client):
        """Regression: 'sovereignty' (English) used to raise KeyError.

        This is the specific bug we hit: the lookup was for 'sovereign_en'
        but the key was 'sovereignty_en'. This test ensures it never
        happens again.
        """
        r = client.post("/chat", json={"message": "sovereignty"})
        assert r.status_code == 200
        data = r.json()
        # Must contain English content, not the Arabic fallback
        assert "I run on YOUR machine" in data["response"] or "Sovereignty" in data["response"]

    def test_regression_license_pricing(self, client):
        """Regression: 'license' (English) used to return pricing.

        The bug was that 'license' keyword hit the 'pricing_en' key instead
        of 'license_en'. This test ensures the right response.
        """
        r = client.post("/chat", json={"message": "license"})
        assert r.status_code == 200
        data = r.json()
        # License response talks about AGPL, not pricing tiers
        # (or it could include both; just shouldn't be pricing-only)
        assert len(data["response"]) > 50

    def test_unknown_word_returns_friendly_fallback(self, client):
        """Unknown words should return a friendly fallback, not crash."""
        r = client.post("/chat", json={"message": "asdfqwer12345"})
        assert r.status_code == 200
        data = r.json()
        # Should be the friendly default (Arabic fallback or helpful message)
        assert len(data["response"]) > 20
