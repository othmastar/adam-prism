"""
[PHASE3] Integration tests for Adam Prism API.
Requires a running API server (set ADAM_TEST_URL).
Run: ADAM_TEST_URL=http://localhost:8000 pytest tests/test_integration.py -v
"""
import os
import uuid

import pytest
import httpx

TEST_URL = os.environ.get("ADAM_TEST_URL", "http://localhost:8000")
TEST_API_KEY = os.environ.get("ADAM_API_KEY", "test-key")

def _auth_headers():
    return {"Authorization": f"Bearer {TEST_API_KEY}"}

@pytest.fixture
def client():
    return httpx.Client(base_url=TEST_URL, timeout=10.0)

@pytest.mark.integration
class TestHealthEndpoints:
    """Test Kubernetes-style health endpoints"""

    def test_liveness(self, client):
        r = client.get("/healthz/live")
        assert r.status_code == 200
        assert r.json()["status"] == "alive"

    def test_readiness(self, client):
        r = client.get("/healthz/ready")
        # 200 = ready, 503 = still starting
        assert r.status_code in (200, 503)
        data = r.json()
        assert "status" in data
        assert "ready" in data

    def test_startup(self, client):
        r = client.get("/healthz/startup")
        assert r.status_code in (200, 503)
        data = r.json() if r.status_code == 200 else {}
        assert "status" in data or r.status_code == 503

    def test_health_overview(self, client):
        r = client.get("/health")
        assert r.status_code in (200, 503)
        data = r.json()
        assert "subsystems" in data

    def test_metrics_endpoint(self, client):
        r = client.get("/metrics")
        assert r.status_code == 200
        assert "adam_up" in r.text
        assert "# HELP" in r.text
        assert "# TYPE" in r.text

@pytest.mark.integration
class TestAuthFlow:
    """Test user registration, login, and JWT"""

    def test_register_new_user(self, client):
        username = f"test_{uuid.uuid4().hex[:8]}"
        email = f"{username}@example.com"
        r = client.post(
            "/api/auth/register",
            json={"email": email, "username": username, "password": "testpass1234"},
        )
        if r.status_code == 409:  # Already exists
            return
        assert r.status_code == 200, f"Register failed: {r.text}"
        data = r.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_register_weak_password(self, client):
        r = client.post(
            "/api/auth/register",
            json={"email": "weak@example.com", "username": "weakuser", "password": "123"},
        )
        assert r.status_code == 400

    def test_login_flow(self, client):
        # Register first
        username = f"login_{uuid.uuid4().hex[:8]}"
        email = f"{username}@example.com"
        password = "testpass1234"
        reg = client.post(
            "/api/auth/register",
            json={"email": email, "username": username, "password": password},
        )
        if reg.status_code != 200:
            pytest.skip("Could not register user")
        # Login
        r = client.post(
            "/api/auth/login",
            json={"username_or_email": username, "password": password},
        )
        assert r.status_code == 200
        data = r.json()
        assert "access_token" in data

    def test_login_invalid(self, client):
        r = client.post(
            "/api/auth/login",
            json={"username_or_email": "nobody", "password": "wrong"},
        )
        assert r.status_code == 401

    def test_me_with_jwt(self, client):
        # Register and login
        username = f"me_{uuid.uuid4().hex[:8]}"
        email = f"{username}@example.com"
        client.post(
            "/api/auth/register",
            json={"email": email, "username": username, "password": "testpass1234"},
        )
        login = client.post(
            "/api/auth/login",
            json={"username_or_email": username, "password": "testpass1234"},
        )
        if login.status_code != 200:
            pytest.skip("Login failed")
        token = login.json()["access_token"]
        r = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
        assert r.status_code == 200
        assert "user_id" in r.json()

    def test_me_with_api_key(self, client):
        r = client.get("/api/auth/me", headers=_auth_headers())
        if TEST_API_KEY == "test-key":
            pytest.skip("Test key may not be the actual API key")
        assert r.status_code == 200

@pytest.mark.integration
class TestChatFlow:
    """Test chat end-to-end with engine"""

    def test_chat_simple(self, client):
        r = client.post(
            "/api/chat",
            json={"message": "Hello", "voice": False},
            headers=_auth_headers(),
        )
        if r.status_code == 503:
            pytest.skip("Engine not attached")
        assert r.status_code == 200
        data = r.json()
        assert "response" in data

    def test_chat_long_message_rejected(self, client):
        r = client.post(
            "/api/chat",
            json={"message": "x" * 11000, "voice": False},
            headers=_auth_headers(),
        )
        assert r.status_code == 400

@pytest.mark.integration
class TestKnowledgeFlow:
    """Test knowledge base operations"""

    def test_list_collections(self, client):
        r = client.get("/api/knowledge/collections", headers=_auth_headers())
        if r.status_code == 503:
            pytest.skip("Qdrant not available")
        assert r.status_code == 200
        assert "collections" in r.json()

    def test_search_knowledge(self, client):
        r = client.post(
            "/api/knowledge/search",
            json={"query": "test", "top_k": 3},
            headers=_auth_headers(),
        )
        if r.status_code == 503:
            pytest.skip("Qdrant not available")
        assert r.status_code == 200
        assert "results" in r.json() or "count" in r.json()

    def test_add_knowledge(self, client):
        r = client.post(
            "/api/knowledge/add",
            json={"texts": ["Integration test knowledge"], "collection": "test"},
            headers=_auth_headers(),
        )
        if r.status_code == 503:
            pytest.skip("Qdrant not available")
        assert r.status_code == 200
