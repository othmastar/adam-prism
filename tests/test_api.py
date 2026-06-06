"""API server tests - requires server running on port 8000"""

import pytest
import httpx
import json

BASE = "http://localhost:8000"


class TestHealth:
    def test_status(self):
        r = httpx.get(f"{BASE}/api/status", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "session_id" in data
        assert "model" in data

    def test_health(self):
        r = httpx.get(f"{BASE}/api/engine/health", timeout=10)
        assert r.status_code == 200
        data = r.json()
        assert data["api"] == "running"
        assert "engine" in data
        assert "system" in data

    def test_ollama_connected(self):
        r = httpx.get(f"{BASE}/api/engine/health", timeout=10)
        data = r.json()
        assert data.get("ollama", {}).get("connected", False) == True


class TestChat:
    @pytest.mark.slow
    def test_simple_message(self):
        r = httpx.post(
            f"{BASE}/api/chat",
            json={"message": "What is 2+2?", "context": {}},
            timeout=60
        )
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        assert len(data["response"]) > 0
        assert data["cycle"] >= 1

    @pytest.mark.slow
    def test_url_message(self):
        r = httpx.post(
            f"{BASE}/api/chat",
            json={"message": "افتح https://example.com", "context": {}},
            timeout=120
        )
        assert r.status_code == 200
        data = r.json()
        assert "response" in data
        refusal_words = ["لا أملك", "لا أستطيع", "لا يمكن"]
        for word in refusal_words:
            assert word not in data["response"], f"Found refusal: {word}"


class TestSessions:
    def test_list_sessions(self):
        r = httpx.get(f"{BASE}/api/chat/sessions", timeout=5)
        assert r.status_code == 200
        data = r.json()
        assert "sessions" in data

    def test_create_session(self):
        r = httpx.post(
            f"{BASE}/api/chat/sessions",
            json={"title": "Test Session"},
            timeout=5
        )
        assert r.status_code == 200
        data = r.json()
        assert "id" in data
        assert data["title"] == "Test Session"
