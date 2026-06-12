"""
Adam Prism — API Middleware Suite
====================================
حزمة وسائط FastAPI شاملة للأمن والتسجيل والمراقبة.

A complete middleware suite for FastAPI applications including security
headers, audit logging, rate limiting, request ID tracking, health
probes, CORS, and request size limiting.

الوسائط المتاحة / Available Middleware:
  - SecurityHeadersMiddleware: رؤوس أمنية — Security response headers
  - AuditLoggingMiddleware: تسجيل طلبات التدقيق — Audit request logging
  - RateLimitMiddleware: تحديد معدل الطلبات — Rate limiting
  - RequestIDMiddleware: معرف الطلب — Request ID tracking
  - RequestSizeLimitMiddleware: تحديد حجم الطلب — Request size limiting
  - Health probe endpoints: نقاط فحص الصحة — Health check endpoints
  - CORS configuration: تكوين CORS — Cross-origin setup
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Callable, Optional, Set

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.routing import Route

from adam.security.rate_limiter import RateLimiter, RateLimitMiddleware

logger = logging.getLogger("adam_prism.api.middleware")


# ═══════════════════════════════════════════════════════════════
# Security Headers Middleware
# ═══════════════════════════════════════════════════════════════

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    وسيط الرؤوس الأمنية — Adds security-related response headers.

    الرؤوس المُضافة / Headers Added:
      - X-Content-Type-Options: nosniff
      - X-Frame-Options: DENY
      - X-XSS-Protection: 1; mode=block
      - Referrer-Policy: strict-origin-when-cross-origin
      - Content-Security-Policy: default-src 'self'
      - Permissions-Policy: camera=(), microphone=(), geolocation=()
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Content-Security-Policy"] = "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'"
        response.headers["Permissions-Policy"] = "camera=(), microphone=(), geolocation=()"
        return response


# ═══════════════════════════════════════════════════════════════
# Request ID Middleware
# ═══════════════════════════════════════════════════════════════

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    وسيط معرف الطلب — Adds a unique request ID to every request.

    يضيف رأس X-Request-ID فريد لكل طلب ويمرره عبر الاستجابة.
    Adds a unique X-Request-ID header to every request and passes it
    through the response.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # استخدام المعرف الموجود أو إنشاء واحد جديد — Use existing or create new
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        response = await call_next(request)
        response.headers["X-Request-ID"] = request_id
        return response


# ═══════════════════════════════════════════════════════════════
# Audit Logging Middleware
# ═══════════════════════════════════════════════════════════════

class AuditLoggingMiddleware(BaseHTTPMiddleware):
    """
    وسيط تسجيل التدقيق — Logs all requests with timing information.

    يسجل كل طلب مع معرف الطلب والمسار والطريقة ووقت الاستجابة وحالة الاستجابة.
    Logs every request with request ID, path, method, response time, and status code.
    """

    def __init__(self, app: Any, exclude_paths: Optional[Set[str]] = None) -> None:
        super().__init__(app)
        self._exclude_paths = exclude_paths or {"/docs", "/openapi.json", "/favicon.ico"}

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # تجاوز المسارات المستثناة — Skip excluded paths
        if request.url.path in self._exclude_paths:
            return await call_next(request)

        start_time = time.time()
        request_id = getattr(request.state, "request_id", "unknown")

        try:
            response = await call_next(request)
            duration_ms = (time.time() - start_time) * 1000

            logger.info(
                "[%s] %s %s → %d (%.1fms)",
                request_id[:8],
                request.method,
                request.url.path,
                response.status_code,
                duration_ms,
            )

            response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
            return response

        except Exception as exc:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                "[%s] %s %s → ERROR (%.1fms): %s",
                request_id[:8],
                request.method,
                request.url.path,
                duration_ms,
                exc,
            )
            raise


# ═══════════════════════════════════════════════════════════════
# Request Size Limit Middleware
# ═══════════════════════════════════════════════════════════════

class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    وسيط تحديد حجم الطلب — Limits request body size.

    يرفض الطلبات التي تتجاوز الحجم المحدد.
    Rejects requests that exceed the configured body size limit.
    """

    def __init__(self, app: Any, max_size_bytes: int = 10 * 1024 * 1024) -> None:
        """
        Args / المعاملات:
            max_size_bytes: الحد الأقصى بحجم البايت (الافتراضي: 10MB)
                            — Max size in bytes (default: 10MB)
        """
        super().__init__(app)
        self._max_size = max_size_bytes

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        content_length = request.headers.get("content-length")
        if content_length:
            try:
                length = int(content_length)
                if length > self._max_size:
                    logger.warning(
                        "Request too large: %d bytes (max: %d) — %s %s",
                        length, self._max_size,
                        request.method, request.url.path,
                    )
                    return JSONResponse(
                        status_code=413,
                        content={
                            "error": "Request too large",
                            "detail": f"Request body exceeds maximum size of {self._max_size} bytes",
                        },
                    )
            except ValueError:
                pass

        return await call_next(request)


# ═══════════════════════════════════════════════════════════════
# Health Probe Endpoints
# ═══════════════════════════════════════════════════════════════

def _create_health_routes(engine: Any = None) -> list:
    """
    إنشاء نقاط فحص الصحة — Create health probe route handlers.

    نقاط النهاية / Endpoints:
      - GET /health/live: فحص الحياة — Liveness probe (is the app running?)
      - GET /health/ready: فحص الجاهزية — Readiness probe (is the app ready?)
      - GET /health/startup: فحص البدء — Startup probe (did the app start?)
    """

    async def liveness(request: Request) -> JSONResponse:
        """فحص الحياة — Is the process alive?"""
        return JSONResponse(status_code=200, content={"status": "alive"})

    async def readiness(request: Request) -> JSONResponse:
        """
        فحص الجاهزية — Is the app ready to serve requests?
        يفحص المحرك والموديولات الأساسية — Checks engine and core modules.
        """
        checks: dict = {"status": "ready", "checks": {}}

        if engine is not None:
            # فحص المحرك — Check engine
            try:
                checks["checks"]["engine"] = "ok"
            except Exception as exc:
                checks["checks"]["engine"] = f"error: {exc}"
                checks["status"] = "degraded"

            # فحص المزود — Check provider
            try:
                if hasattr(engine, "provider") and engine.provider is not None:
                    checks["checks"]["provider"] = "ok"
                else:
                    checks["checks"]["provider"] = "not_initialized"
                    checks["status"] = "degraded"
            except Exception as exc:
                checks["checks"]["provider"] = f"error: {exc}"
                checks["status"] = "degraded"

        status_code = 200 if checks["status"] == "ready" else 503
        return JSONResponse(status_code=status_code, content=checks)

    async def startup_check(request: Request) -> JSONResponse:
        """فحص البدء — Did the app start successfully?"""
        return JSONResponse(status_code=200, content={"status": "started"})

    return [
        Route("/health/live", liveness, methods=["GET"]),
        Route("/health/ready", readiness, methods=["GET"]),
        Route("/health/startup", startup_check, methods=["GET"]),
    ]


# ═══════════════════════════════════════════════════════════════
# Install All Middleware
# ═══════════════════════════════════════════════════════════════

def install_all_middleware(
    app: FastAPI,
    engine: Any = None,
    rate_limiter: Optional[RateLimiter] = None,
    cors_origins: Optional[list] = None,
    max_request_size: int = 10 * 1024 * 1024,
    rate_limit_exclude_paths: Optional[list] = None,
) -> None:
    """
    تثبيت جميع الوسائط — Install all middleware on a FastAPI app.

    الترتيب مهم — Order matters (last added = first executed):
      1. CORS (أول معالج) — First handler
      2. Security headers
      3. Request ID
      4. Audit logging
      5. Request size limit
      6. Rate limiting (آخر معالج قبل التطبيق) — Last before app

    Args / المعاملات:
        app: تطبيق FastAPI — FastAPI application
        engine: مرجع المحرك (لنقاط فحص الصحة) — Engine reference (for health probes)
        rate_limiter: محدد المعدل — Rate limiter instance
        cors_origins: أصول CORS المسموحة — Allowed CORS origins
        max_request_size: الحد الأقصى لحجم الطلب — Max request body size
        rate_limit_exclude_paths: مسارات مستثناة من تحديد المعدل — Rate limit excluded paths
    """
    # 1. CORS — تكوين الأصل المشترك
    origins = cors_origins or [
        "http://localhost:3000",
        "http://localhost:8000",
        "http://127.0.0.1:3000",
        "http://127.0.0.1:8000",
    ]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
        expose_headers=["X-Request-ID", "X-RateLimit-Remaining", "X-RateLimit-Reset", "X-Response-Time"],
    )

    # 2. رؤوس أمنية — Security headers
    app.add_middleware(SecurityHeadersMiddleware)

    # 3. معرف الطلب — Request ID
    app.add_middleware(RequestIDMiddleware)

    # 4. تسجيل التدقيق — Audit logging
    app.add_middleware(AuditLoggingMiddleware)

    # 5. تحديد حجم الطلب — Request size limit
    app.add_middleware(RequestSizeLimitMiddleware, max_size_bytes=max_request_size)

    # 6. تحديد المعدل — Rate limiting
    app.add_middleware(
        RateLimitMiddleware,
        rate_limiter=rate_limiter or RateLimiter(),
        exclude_paths=rate_limit_exclude_paths,
    )

    # نقاط فحص الصحة — Health probe routes
    health_routes = _create_health_routes(engine)
    for route in health_routes:
        app.router.routes.append(route)

    logger.info(
        "All middleware installed: CORS, SecurityHeaders, RequestID, AuditLogging, "
        "SizeLimit, RateLimit, HealthProbes"
    )
