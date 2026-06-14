"""
[PHASE3] Health check endpoints for Kubernetes/Docker.
Implements standard probes:
- /healthz/live  — liveness: am I alive?
- /healthz/ready — readiness: can I serve traffic?
- /healthz/startup — startup: have I finished initial bootstrap?
"""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Any, Callable, Awaitable

from fastapi import APIRouter, FastAPI, Response, status
from fastapi.responses import JSONResponse

logger = logging.getLogger("adam_prism.health")

# Subsystem check functions
# Each returns (healthy: bool, details: dict)
CheckFunc = Callable[[], Awaitable[tuple[bool, dict[str, Any]]]]


class HealthRegistry:
    """[PHASE3] Registry of health checks for subsystems."""

    def __init__(self) -> None:
        self._checks: dict[str, CheckFunc] = {}
        self._startup_complete = False
        self._startup_time: float | None = None

    def register(self, name: str, check: CheckFunc) -> None:
        self._checks[name] = check

    def mark_startup_complete(self) -> None:
        self._startup_complete = True
        self._startup_time = time.time()

    def is_ready(self) -> bool:
        return self._startup_complete

    async def check_all(self) -> tuple[bool, dict[str, Any]]:
        """Run all registered checks in parallel."""
        if not self._checks:
            return True, {}

        results: dict[str, Any] = {}
        all_healthy = True

        # Run checks in parallel
        check_tasks = {
            name: asyncio.create_task(check())
            for name, check in self._checks.items()
        }
        for name, task in check_tasks.items():
            try:
                healthy, details = await asyncio.wait_for(task, timeout=5.0)
            except asyncio.TimeoutError:
                healthy, details = False, {"error": "timeout"}
            except Exception as e:
                healthy, details = False, {"error": str(e)}
            results[name] = {
                "healthy": healthy,
                **details,
            }
            if not healthy:
                all_healthy = False

        return all_healthy, results


# Default subsystem health checks
async def check_qdrant(engine) -> tuple[bool, dict[str, Any]]:
    """Check Qdrant connectivity"""
    try:
        from qdrant_client import QdrantClient
        from urllib.parse import urlparse
        cfg = engine.config if engine else {}
        url = cfg.get("qdrant_url", "http://localhost:6333")
        pu = urlparse(url)
        client = QdrantClient(
            host=pu.hostname or "localhost",
            port=pu.port or 6333,
            timeout=3.0,
        )
        client.get_collections()
        return True, {"url": url}
    except Exception as e:
        return False, {"error": str(e)[:200]}


async def check_ollama(engine) -> tuple[bool, dict[str, Any]]:
    """Check Ollama connectivity"""
    try:
        import httpx
        cfg = engine.config if engine else {}
        url = cfg.get("ollama_base", "http://localhost:11434")
        async with httpx.AsyncClient(timeout=3.0) as client:
            resp = await client.get(f"{url}/api/tags")
        if resp.status_code == 200:
            data = resp.json()
            models = [m.get("name") for m in data.get("models", [])]
            return True, {"url": url, "model_count": len(models)}
        return False, {"url": url, "status": resp.status_code}
    except Exception as e:
        return False, {"error": str(e)[:200]}


async def check_disk_space(engine) -> tuple[bool, dict[str, Any]]:
    """Check disk space available"""
    try:
        import shutil
        cfg = engine.config if engine else {}
        data_dir = cfg.get("data_dir", "/tmp")
        usage = shutil.disk_usage(data_dir)
        free_gb = usage.free / (1024 ** 3)
        healthy = free_gb > 0.5  # At least 500MB free
        return healthy, {
            "free_gb": round(free_gb, 2),
            "total_gb": round(usage.total / (1024 ** 3), 2),
            "percent_used": round(usage.percent, 1),
        }
    except Exception as e:
        return False, {"error": str(e)[:200]}


async def check_memory(engine) -> tuple[bool, dict[str, Any]]:
    """Check available memory"""
    try:
        import psutil
        mem = psutil.virtual_memory()
        healthy = mem.percent < 95  # Less than 95% used
        return healthy, {
            "used_percent": mem.percent,
            "available_gb": round(mem.available / (1024 ** 3), 2),
        }
    except ImportError:
        return True, {"psutil": "not installed"}
    except Exception as e:
        return False, {"error": str(e)[:200]}


def setup_health_endpoints(app: FastAPI, engine, registry: HealthRegistry) -> None:
    """[PHASE3] Register health check endpoints on the FastAPI app."""

    # Register default checks
    if engine:
        registry.register("qdrant", lambda: check_qdrant(engine))
        registry.register("ollama", lambda: check_ollama(engine))
        registry.register("disk_space", lambda: check_disk_space(engine))
        registry.register("memory", lambda: check_memory(engine))

    @app.get("/healthz/live", include_in_schema=False)
    async def liveness():
        """[PHASE3] Liveness probe - is the process alive?
        Always returns 200 if the event loop is responsive.
        """
        return JSONResponse(
            status_code=200,
            content={"status": "alive", "timestamp": time.time()},
        )

    @app.get("/healthz/ready", include_in_schema=False)
    async def readiness(response: Response):
        """[PHASE3] Readiness probe - can I serve traffic?
        Returns 200 only when:
        - Startup is complete
        - All critical subsystems are healthy
        """
        if not registry.is_ready():
            return JSONResponse(
                status_code=503,
                content={"status": "starting", "ready": False},
            )
        all_healthy, results = await registry.check_all()
        status_code = 200 if all_healthy else 503
        return JSONResponse(
            status_code=status_code,
            content={
                "status": "ready" if all_healthy else "degraded",
                "ready": all_healthy,
                "checks": results,
            },
        )

    @app.get("/healthz/startup", include_in_schema=False)
    async def startup():
        """[PHASE3] Startup probe - has initial bootstrap finished?"""
        if registry.is_ready():
            return JSONResponse(
                status_code=200,
                content={
                    "status": "started",
                    "startup_time": registry._startup_time,
                },
            )
        return JSONResponse(
            status_code=503,
            content={"status": "starting", "ready": False},
        )

    @app.get("/health", include_in_schema=False)
    async def health(response: Response):
        """[PHASE3] Human-readable health overview"""
        if not registry.is_ready():
            return JSONResponse(
                status_code=503,
                content={"status": "starting", "ready": False},
            )
        all_healthy, results = await registry.check_all()
        return JSONResponse(
            status_code=200 if all_healthy else 503,
            content={
                "status": "healthy" if all_healthy else "degraded",
                "engine_attached": engine is not None,
                "subsystems": results,
            },
        )
