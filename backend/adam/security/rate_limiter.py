"""
Adam Prism — Token Bucket Rate Limiter
========================================
محدد معدل الطلبات بخوارزمية دلو الرموز.

A token bucket rate limiter that enforces per-endpoint, per-user
rate limits with configurable buckets and FastAPI middleware integration.

خوارزمية دلو الرموز / Token Bucket Algorithm:
  - كل نقطة نهاية لها سعة محددة من الرموز في الدقيقة
  - كل طلب يستهلك رمزاً واحداً
  - الرموز تُعاد تعبئتها بمعدل ثابت
  - إذا لم تكف الرموز، يُرفض الطلب

المميزات / Features:
  - حدود لكل نقطة نهاية — Per-endpoint limits
  - تتبع لكل مستخدم — Per-user tracking
  - تكامل مع FastAPI كوسيط — FastAPI middleware integration
  - إحصائيات — Usage statistics
"""

from __future__ import annotations

import asyncio
import logging
import time
from dataclasses import dataclass, field
from typing import Any, Dict, Optional, Tuple

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

logger = logging.getLogger("adam_prism.security.rate_limiter")


# ═══════════════════════════════════════════════════════════════
# حدود النقاط / Endpoint Limits
# ═══════════════════════════════════════════════════════════════

# الحدود الافتراضية لكل نقطة نهاية (طلبات/دقيقة)
# Default rate limits per endpoint category (requests/minute)
DEFAULT_ENDPOINT_LIMITS: Dict[str, int] = {
    "chat": 30,
    "voice": 15,
    "admin": 5,
    "tool": 20,
    "research": 20,
    "workflow": 10,
    "default": 60,
}


@dataclass
class TokenBucket:
    """
    دلو رموز — A token bucket for rate limiting.

    Attributes / الخصائص:
        capacity: السعة القصوى — Maximum capacity (max tokens)
        tokens: الرموز المتاحة — Available tokens
        refill_rate: معدل إعادة التعبئة (رموز/ثانية) — Refill rate (tokens/second)
        last_refill: وقت آخر تعبئة — Last refill timestamp
    """
    capacity: int
    tokens: float
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.time)

    def refill(self) -> None:
        """
        إعادة تعبئة الرموز — Refill tokens based on elapsed time.
        """
        now = time.time()
        elapsed = now - self.last_refill
        new_tokens = elapsed * self.refill_rate
        self.tokens = min(self.capacity, self.tokens + new_tokens)
        self.last_refill = now

    def consume(self, tokens: int = 1) -> bool:
        """
        استهلاك رموز — Try to consume tokens.

        Args / المعاملات:
            tokens: عدد الرموز المطلوبة — Number of tokens to consume

        Returns / المخرجات:
            True إذا تم الاستهلاك، False إذا لم تتوفر الرموز
            — True if consumed, False if insufficient tokens
        """
        self.refill()
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False

    @property
    def remaining(self) -> int:
        """
        الرموز المتبقية — Remaining tokens (rounded down).
        """
        self.refill()
        return int(self.tokens)

    @property
    def reset_at(self) -> float:
        """
        وقت إعادة التعبئة الكاملة — Time when bucket will be fully refilled.
        """
        self.refill()
        deficit = self.capacity - self.tokens
        return time.time() + (deficit / self.refill_rate if self.refill_rate > 0 else 0)


# ═══════════════════════════════════════════════════════════════
# Rate Limiter
# ═══════════════════════════════════════════════════════════════

class RateLimiter:
    """
    محدد معدل الطلبات — Token bucket rate limiter.

    يدعم حدود مختلفة لكل نوع نقطة نهاية ولكل مستخدم.
    Supports different limits per endpoint category and per user.

    الاستخدام / Usage:
        limiter = RateLimiter()
        allowed, remaining, reset_at = limiter.check("user_1", "chat")
        if not allowed:
            raise HTTPException(429, "Rate limit exceeded")
    """

    def __init__(
        self,
        endpoint_limits: Optional[Dict[str, int]] = None,
    ) -> None:
        """
        تهيئة محدد المعدل — Initialize the rate limiter.

        Args / المعاملات:
            endpoint_limits: حدود لكل نقطة نهاية (طلبات/دقيقة)
                             — Per-endpoint limits (requests/minute)
        """
        self._limits = endpoint_limits or DEFAULT_ENDPOINT_LIMITS.copy()

        # دواليب الرموز: (user_id, endpoint) → TokenBucket
        self._buckets: Dict[Tuple[str, str], TokenBucket] = {}

        # قفل للسلامة — Lock for thread safety
        self._lock = asyncio.Lock()

        # عدادات — Counters
        self._total_allowed: int = 0
        self._total_rejected: int = 0

    def _get_endpoint_category(self, endpoint: str) -> str:
        """
        تحديد فئة نقطة النهاية — Determine the endpoint category.

        Args / المعاملات:
            endpoint: مسار نقطة النهاية — Endpoint path

        Returns / المخرجات:
            فئة نقطة النهاية — Endpoint category
        """
        path_lower = endpoint.lower()

        # مطابقة الأنماط — Pattern matching
        if "/chat" in path_lower or "/message" in path_lower:
            return "chat"
        if "/voice" in path_lower or "/tts" in path_lower or "/stt" in path_lower:
            return "voice"
        if "/admin" in path_lower or "/config" in path_lower or "/mcp" in path_lower:
            return "admin"
        if "/tool" in path_lower or "/browser" in path_lower or "/shell" in path_lower:
            return "tool"
        if "/research" in path_lower or "/search" in path_lower or "/knowledge" in path_lower:
            return "research"
        if "/workflow" in path_lower or "/orchestrator" in path_lower:
            return "workflow"
        return "default"

    def _get_or_create_bucket(self, user_id: str, category: str) -> TokenBucket:
        """
        الحصول على أو إنشاء دلو رموز — Get or create a token bucket.
        """
        key = (user_id, category)
        if key not in self._buckets:
            limit = self._limits.get(category, self._limits["default"])
            self._buckets[key] = TokenBucket(
                capacity=limit,
                tokens=float(limit),
                refill_rate=limit / 60.0,  # توزيع على 60 ثانية — Spread over 60s
            )
        return self._buckets[key]

    async def check(
        self,
        user_id: str,
        endpoint: str,
    ) -> Tuple[bool, int, float]:
        """
        فحص معدل الطلبات — Check if a request is allowed.

        Args / المعاملات:
            user_id: معرف المستخدم — User identifier
            endpoint: مسار نقطة النهاية — Endpoint path

        Returns / المخرجات:
            (allowed, remaining, reset_at):
              - allowed: هل سُمح بالطلب؟ — Is the request allowed?
              - remaining: الرموز المتبقية — Remaining tokens
              - reset_at: وقت إعادة التعبئة — Reset timestamp
        """
        category = self._get_endpoint_category(endpoint)

        async with self._lock:
            bucket = self._get_or_create_bucket(user_id, category)
            allowed = bucket.consume()
            remaining = bucket.remaining
            reset_at = bucket.reset_at

        if allowed:
            self._total_allowed += 1
        else:
            self._total_rejected += 1
            logger.warning(
                "Rate limit: user=%s endpoint=%s category=%s remaining=%d",
                user_id, endpoint, category, remaining,
            )

        return allowed, remaining, reset_at

    async def reset(self, user_id: Optional[str] = None) -> int:
        """
        إعادة تعيين الحدود — Reset rate limits.

        Args / المعاملات:
            user_id: معرف المستخدم (None = إعادة تعيين الكل)
                     — User ID (None = reset all)

        Returns / المخرجات:
            عدد الدلوب المعاد تعيينها — Number of buckets reset
        """
        async with self._lock:
            if user_id is None:
                count = len(self._buckets)
                self._buckets.clear()
            else:
                keys_to_remove = [
                    k for k in self._buckets if k[0] == user_id
                ]
                for k in keys_to_remove:
                    del self._buckets[k]
                count = len(keys_to_remove)

        logger.info("Rate limit reset: %d buckets cleared", count)
        return count

    async def get_stats(self) -> Dict[str, Any]:
        """
        الحصول على إحصائيات المحدد — Get rate limiter statistics.

        Returns / المخرجات:
            إحصائيات — Stats dict
        """
        async with self._lock:
            active_users = set(k[0] for k in self._buckets)
            category_counts: Dict[str, int] = {}
            for k in self._buckets:
                cat = k[1]
                category_counts[cat] = category_counts.get(cat, 0) + 1

        return {
            "total_allowed": self._total_allowed,
            "total_rejected": self._total_rejected,
            "active_users": len(active_users),
            "active_buckets": len(self._buckets),
            "category_buckets": category_counts,
            "endpoint_limits": self._limits,
        }


# ═══════════════════════════════════════════════════════════════
# FastAPI Middleware
# ═══════════════════════════════════════════════════════════════

class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    وسيط تحديد المعدل لـ FastAPI — Rate limiting middleware for FastAPI.

    يفحص كل طلب ويتحقق من معدل الطلبات للمستخدم ونقطة النهاية.
    Checks every request against the rate limiter before passing it through.

    الاستخدام / Usage:
        limiter = RateLimiter()
        app.add_middleware(RateLimitMiddleware, rate_limiter=limiter)
    """

    def __init__(
        self,
        app: Any,
        rate_limiter: Optional[RateLimiter] = None,
        exclude_paths: Optional[list] = None,
    ) -> None:
        """
        تهيئة الوسيط — Initialize the middleware.

        Args / المعاملات:
            app: تطبيق FastAPI — FastAPI app
            rate_limiter: محدد المعدل — Rate limiter instance
            exclude_paths: مسارات مستثناة — Paths to exclude from rate limiting
        """
        super().__init__(app)
        self.rate_limiter = rate_limiter or RateLimiter()
        self._exclude_paths = set(exclude_paths or [])
        # المسارات الأساسية المستثناة — Default excluded paths
        self._exclude_paths.update({"/health/live", "/health/ready", "/health/startup", "/docs", "/openapi.json"})

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        """
        معالجة الطلب — Process the request through rate limiting.
        """
        # تجاوز المسارات المستثناة — Skip excluded paths
        path = request.url.path
        if path in self._exclude_paths:
            return await call_next(request)

        # تحديد المستخدم — Identify user
        user_id = self._get_user_id(request)

        # فحص المعدل — Check rate
        allowed, remaining, reset_at = await self.rate_limiter.check(user_id, path)

        if not allowed:
            logger.warning("Rate limited: user=%s path=%s", user_id, path)
            return JSONResponse(
                status_code=429,
                content={
                    "error": "Rate limit exceeded",
                    "detail": "Too many requests. Please try again later.",
                    "retry_after": max(1, int(reset_at - time.time())),
                },
                headers={
                    "Retry-After": str(max(1, int(reset_at - time.time()))),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(int(reset_at)),
                },
            )

        # إضافة رؤوس المعدل — Add rate limit headers
        response = await call_next(request)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(int(reset_at))

        return response

    @staticmethod
    def _get_user_id(request: Request) -> str:
        """
        تحديد هوية المستخدم من الطلب — Identify user from request.
        """
        # محاولة من الرأس — Try authorization header
        auth = request.headers.get("Authorization", "")
        if auth:
            # تجزئة الرمز — Hash the token for privacy
            import hashlib
            return "user_" + hashlib.sha256(auth.encode()).hexdigest()[:12]

        # محاولة من عنوان IP — Try IP address
        client = request.client
        if client:
            return f"ip_{client.host}"

        return "anonymous"
