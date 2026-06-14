"""Shared pytest fixtures and sys.path setup for Adam Prism tests"""
import sys
from pathlib import Path

# [PHASE4] Add backend/ to sys.path so `adam.*` imports work
_backend = Path(__file__).parent / "backend"
if str(_backend) not in sys.path:
    sys.path.insert(0, str(_backend))

import pytest
import httpx


def _ollama_available():
    try:
        r = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
        return r.status_code == 200
    except Exception:
        return False


def _api_server_available():
    try:
        r = httpx.get("http://localhost:8002/health", timeout=2.0)
        return r.status_code == 200
    except Exception:
        try:
            r = httpx.get("http://localhost:8001/health", timeout=2.0)
            return r.status_code == 200
        except Exception:
            return False


ollama_available = _ollama_available()
api_available = _api_server_available()


def pytest_collection_modifyitems(items):
    """Skip tests that need Ollama or API server when not available"""
    for item in items:
        if "ollama" in item.nodeid or "engine" in item.nodeid:
            if "TestEngine" in item.nodeid and not ollama_available:
                item.add_marker(pytest.mark.skip(reason="Ollama not available"))
        if "api" in item.nodeid and not api_available:
            item.add_marker(pytest.mark.skip(reason="API server not running"))
