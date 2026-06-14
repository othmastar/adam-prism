"""
[PHASE6] Locust load test for Adam Prism API.
Simulates realistic user traffic to benchmark performance.

Usage:
    pip install locust
    locust -f tests/load/locustfile.py --host=http://localhost:8000
"""
import random

from locust import HttpUser, task, between


class ChatUser(HttpUser):
    """[PHASE6] Simulated user running chat workloads."""

    wait_time = between(1, 5)  # Wait 1-5s between tasks (realistic)

    def on_start(self):
        """[PHASE6] Login before running tasks."""
        # For load tests, use the API key directly (or login)
        self.api_key = "test-load-key"
        self.client.headers.update({
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        })

    @task(5)  # Weight: most common
    def chat_simple(self):
        """[PHASE6] Send a simple chat message."""
        messages = [
            "مرحبا، كيف حالك؟",
            "ما هو آدم بريزم؟",
            "Explain quantum computing",
            "What is the meaning of life?",
            "اكتب كود Python بسيط",
        ]
        msg = random.choice(messages)
        self.client.post(
            "/api/chat",
            json={"message": msg, "voice": False},
            name="/api/chat",
        )

    @task(2)
    def list_sessions(self):
        """[PHASE6] List chat sessions."""
        self.client.get(
            "/api/chat/sessions?limit=20",
            name="/api/chat/sessions",
        )

    @task(1)
    def get_status(self):
        """[PHASE6] Health/status check."""
        self.client.get(
            "/api/status",
            name="/api/status",
        )

    @task(1)
    def search_knowledge(self):
        """[PHASE6] Search knowledge base."""
        queries = [
            "ما هو التوأم الرقمي",
            "cybersecurity best practices",
            "AI ethics",
            "Docker deployment",
        ]
        self.client.post(
            "/api/knowledge/search",
            json={"query": random.choice(queries), "top_k": 3},
            name="/api/knowledge/search",
        )

    @task(1)
    def create_session(self):
        """[PHASE6] Create a new chat session."""
        self.client.post(
            "/api/chat/sessions",
            json={"title": f"Load test session {random.randint(1, 1000)}"},
            name="/api/chat/sessions [POST]",
        )


class AdminUser(HttpUser):
    """[PHASE6] Simulated admin user running observability queries."""

    wait_time = between(5, 15)

    def on_start(self):
        self.api_key = "test-admin-key"
        self.client.headers.update({
            "Authorization": f"Bearer {self.api_key}",
        })

    @task(2)
    def get_health(self):
        self.client.get("/healthz/ready", name="/healthz/ready")

    @task(2)
    def get_metrics(self):
        self.client.get("/metrics", name="/metrics")

    @task(1)
    def get_audit(self):
        self.client.get("/api/audit?limit=50", name="/api/audit")

    @task(1)
    def get_ai_stats(self):
        self.client.get("/api/ai-observability/stats?hours=24", name="/api/ai-observability/stats")
