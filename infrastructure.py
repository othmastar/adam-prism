"""
Adam Prism - Production Infrastructure
=========================================
اتصال مهيأ (Connection Pooling) + Caching + Retry + Metrics
خفيف، غير معطل، جاهز للإنتاج.
"""

import asyncio
import hashlib
import logging
import time
from contextlib import asynccontextmanager
from dataclasses import dataclass, field
from functools import wraps
from typing import Dict, Any, Callable, Optional, Tuple, List

import httpx

logger = logging.getLogger("adam_prism.infrastructure")


# ═══════════════════════════════════════
# 1. Connection Pooling — اتصال مهيأ واحد لكل خدمة
# ═══════════════════════════════════════

class SharedClients:
    """مشاركة اتصال HTTP واحد لكل خدمة — بدلاً من create جديد كل مرة"""

    def __init__(self):
        self._clients: Dict[str, httpx.AsyncClient] = {}
        self._client_timeouts: Dict[str, float] = {}
        self._lock = asyncio.Lock()

    def _make_client(self, base_url: str, timeout: float = 30.0) -> httpx.AsyncClient:
        """إنشاء عميل مع connection pooling حقيقي"""
        limits = httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20,
            keepalive_expiry=60.0,
        )
        return httpx.AsyncClient(
            base_url=base_url,
            timeout=httpx.Timeout(timeout),
            limits=limits,
            follow_redirects=True,
        )

    async def get(self, name: str, base_url: str = "", timeout: float = 30.0) -> httpx.AsyncClient:
        """الحصول على عميل — ينشئه لو مش موجود أو إذا تغير timeout"""
        async with self._lock:
            needs_new = (
                name not in self._clients
                or self._clients[name].is_closed
                or self._client_timeouts.get(name) != timeout
            )
            if needs_new:
                client = self._make_client(base_url, timeout)
                self._clients[name] = client
                self._client_timeouts[name] = timeout
            return self._clients[name]

    async def close_all(self):
        """إغلاق كل الاتصالات — للخروج النظيف"""
        async with self._lock:
            for name, client in self._clients.items():
                if not client.is_closed:
                    await client.aclose()
            self._clients.clear()

    async def health(self) -> Dict[str, bool]:
        """حالة كل الاتصالات"""
        return {name: not c.is_closed for name, c in self._clients.items()}


# ═══════════════════════════════════════
# 2. TTL Cache — كاش بزمن انتهاء
# ═══════════════════════════════════════

@dataclass
class CacheEntry:
    value: Any
    expiry: float

class TTLCache:
    """كاش خفيف في الذاكرة مع TTL — بدون Redis"""

    def __init__(self, default_ttl: float = 300.0, max_size: int = 500):
        self._data: Dict[str, CacheEntry] = {}
        self._default_ttl = default_ttl
        self._max_size = max_size
        self._hits = 0
        self._misses = 0

    def _key(self, *args, **kwargs) -> str:
        """توليد مفتاح فريد"""
        raw = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, key: str):
        """قراءة من الكاش"""
        entry = self._data.get(key)
        if entry and entry.expiry > time.time():
            self._hits += 1
            return entry.value
        if entry:
            self._misses += 1
            del self._data[key]
        return None

    def set(self, key: str, value: Any, ttl: Optional[float] = None):
        """كتابة في الكاش"""
        if len(self._data) >= self._max_size:
            self._evict()
        self._data[key] = CacheEntry(
            value=value,
            expiry=time.time() + (ttl or self._default_ttl),
        )

    def _evict(self):
        """إزالة أقدم 20% من المدخلات"""
        sorted_items = sorted(self._data.items(), key=lambda x: x[1].expiry)
        for k, _ in sorted_items[:len(self._data) // 5]:
            del self._data[k]

    def clear(self):
        self._data.clear()
        self._hits = 0
        self._misses = 0

    def stats(self) -> Dict:
        total = self._hits + self._misses
        return {
            "size": len(self._data),
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": round(self._hits / max(total, 1) * 100, 1),
        }


# ═══════════════════════════════════════
# 3. Retry Decorator — إعادة المحاولة عند الفشل
# ═══════════════════════════════════════

def retry(max_attempts: int = 3, base_delay: float = 0.5, max_delay: float = 10.0,
          retryable_exceptions: Tuple = (httpx.TimeoutException, httpx.ConnectError,
                                          httpx.RemoteProtocolError, ConnectionError, TimeoutError)):
    """ديكوريتور لإعادة المحاولة مع exponential backoff"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(1, max_attempts + 1):
                try:
                    return await func(*args, **kwargs)
                except retryable_exceptions as e:
                    last_exc = e
                    if attempt < max_attempts:
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        logger.warning(f"⚠️ {func.__name__} failed (attempt {attempt}/{max_attempts}): {e}. Retrying in {delay:.1f}s")
                        await asyncio.sleep(delay)
                    else:
                        logger.error(f"❌ {func.__name__} failed after {max_attempts} attempts: {e}")
            raise last_exc
        return wrapper
    return decorator


# ═══════════════════════════════════════
# 4. Simple Metrics — عدادات وإحصائيات خفيفة
# ═══════════════════════════════════════

class MetricsCollector:
    """عدادات أداء بسيطة — جاهزة للتصدير لـ Prometheus لاحقاً"""

    def __init__(self):
        self._counters: Dict[str, int] = {}
        self._timers: Dict[str, List[float]] = {}
        self._errors: Dict[str, int] = {}

    def inc(self, name: str, value: int = 1):
        self._counters[name] = self._counters.get(name, 0) + value

    def timing(self, name: str, duration_ms: float):
        if name not in self._timers:
            self._timers[name] = []
        self._timers[name].append(duration_ms)
        # حافظ على آخر 1000 قيمة فقط
        if len(self._timers[name]) > 1000:
            self._timers[name] = self._timers[name][-1000:]

    def error(self, name: str):
        self._errors[name] = self._errors.get(name, 0) + 1
        self.inc("errors_total")

    def dump(self) -> Dict:
        result = {}
        for name, count in sorted(self._counters.items()):
            result[f"counter_{name}"] = count
        for name, values in sorted(self._timers.items()):
            if values:
                result[f"timer_{name}_avg_ms"] = round(sum(values) / len(values), 1)
                result[f"timer_{name}_max_ms"] = round(max(values), 1)
                result[f"timer_{name}_total"] = len(values)
        for name, count in sorted(self._errors.items()):
            result[f"error_{name}"] = count
        return result

    def reset(self):
        self._counters.clear()
        self._timers.clear()
        self._errors.clear()


# ═══════════════════════════════════════
# 5. Input Sanitizer — حماية من المسارات الخبيثة
# ═══════════════════════════════════════

ALLOWED_FILE_PATHS = [
    "/mnt/Workspace/Adam_Prism_Complete_v2",
    "/tmp",
    "./notebook",
    "./data",
    "./config",
]

BLOCKED_FILE_SUBSTRINGS = [
    "/etc/", "/proc/", "/sys/", "/dev/", "/boot/",
    "/root/", "/home/", "/var/", "/usr/", "/bin/",
    ".ssh", ".config", ".env", "password",
    "credential", "secret", "token",
]

def sanitize_path(path: str) -> Optional[str]:
    """التحقق من أن المسار مصرح به — يمنع الوصول لملفات النظام"""
    resolved = str(Path(path).resolve())
    for blocked in BLOCKED_FILE_SUBSTRINGS:
        if blocked in resolved.lower():
            return None
    for allowed in ALLOWED_FILE_PATHS:
        if resolved.startswith(allowed):
            return resolved
    return None

from pathlib import Path  # noqa: E402


# ═══════════════════════════════════════
# 6. Circuit Breaker — حماية الخدمات المتعثرة
# ═══════════════════════════════════════

class CircuitBreaker:
    """قاطع الدائرة — يمنع استدعاء خدمة بعد عدد معين من الفشل"""

    CLOSED = "closed"    # الخدمة سليمة
    OPEN = "open"        # الخدمة متعثرة — ممنوع المرور
    HALF_OPEN = "half_open"  # اختبار واحد مسموح

    def __init__(self, name: str, failure_threshold: int = 5, recovery_timeout: float = 30.0):
        self.name = name
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.state = self.CLOSED
        self.failure_count = 0
        self.last_failure_time = 0.0
        self.total_failures = 0
        self.total_successes = 0

    async def call(self, func: Callable, *args, **kwargs):
        if self.state == self.OPEN:
            if time.time() - self.last_failure_time >= self.recovery_timeout:
                self.state = self.HALF_OPEN
                logger.info(f"🔓 CircuitBreaker '{self.name}' half-open — اختبار...")
            else:
                raise Exception(f"CircuitBreaker '{self.name}' is OPEN — الخدمة متعثرة")

        try:
            result = await func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise

    def _on_success(self):
        self.total_successes += 1
        if self.state == self.HALF_OPEN:
            self.state = self.CLOSED
            self.failure_count = 0
            logger.info(f"🔒 CircuitBreaker '{self.name}' closed — عادت الخدمة للعمل")
        self.failure_count = 0

    def _on_failure(self):
        self.total_failures += 1
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = self.OPEN
            logger.warning(f"🔴 CircuitBreaker '{self.name}' OPEN — تعطلت الخدمة ({self.failure_count} فشل)")

    def stats(self) -> Dict:
        return {
            "name": self.name,
            "state": self.state,
            "failure_count": self.failure_count,
            "total_failures": self.total_failures,
            "total_successes": self.total_successes,
        }


# ═══════════════════════════════════════
# 7. Model Swapper — إدارة VRAM: موديل واحد في اللحظة
# ═══════════════════════════════════════

class ModelSwapper:
    """مبادل الموديلات — يضمن أن موديلاً واحداً فقط في VRAM في اللحظة.
    الترتيب: Whisper (~1GB) → Gemma 4 (~9.6GB) → Silma TTS (~2.6GB) → Gemma 4
    """

    def __init__(self, max_vram_gb: float = 12.0):
        self._current_model: Optional[str] = None
        self._models: Dict[str, Dict[str, Any]] = {}
        self._max_vram_gb = max_vram_gb
        self._lock = asyncio.Lock()
        self._swap_count = 0
        self._total_swap_time_ms = 0.0

    def register(self, model_id: str, load_fn: Callable, unload_fn: Callable,
                 vram_gb: float = 1.0, metadata: Optional[Dict] = None):
        """تسجيل موديل مع دوال التحميل والتفريغ"""
        self._models[model_id] = {
            "load_fn": load_fn,
            "unload_fn": unload_fn,
            "vram_gb": vram_gb,
            "loaded": False,
            "metadata": metadata or {},
        }
        logger.info(f"ModelSwapper: {model_id} مسجل ({vram_gb}GB)")

    async def swap_in(self, model_id: str) -> bool:
        """تبديل إلى موديل — يفرغ الحالي ويحمل الجديد"""
        async with self._lock:
            if model_id == self._current_model:
                return True

            if model_id not in self._models:
                logger.error(f"ModelSwapper: {model_id} غير مسجل")
                return False

            start = time.time()

            # تفريغ الموديل الحالي
            if self._current_model is not None:
                current = self._models.get(self._current_model)
                if current and current["loaded"]:
                    try:
                        await current["unload_fn"]()
                        current["loaded"] = False
                        logger.info(f"ModelSwapper: {self._current_model} مُفرغ")
                    except Exception as e:
                        logger.error(f"فشل تفريغ {self._current_model}: {e}")

            # تحميل الموديل الجديد
            target = self._models[model_id]
            if not target["loaded"]:
                try:
                    await target["load_fn"]()
                    target["loaded"] = True
                    logger.info(f"ModelSwapper: {model_id} محمّل")
                except Exception as e:
                    logger.error(f"فشل تحميل {model_id}: {e}")
                    self._current_model = None
                    return False

            self._current_model = model_id
            elapsed = (time.time() - start) * 1000
            self._swap_count += 1
            self._total_swap_time_ms += elapsed
            logger.info(f"ModelSwapper: ↻ {model_id} في {elapsed:.0f}ms")
            return True

    async def swap_out(self):
        """تفريغ الموديل الحالي فقط"""
        async with self._lock:
            if self._current_model is None:
                return
            current = self._models.get(self._current_model)
            if current and current["loaded"]:
                try:
                    await current["unload_fn"]()
                    current["loaded"] = False
                except Exception as e:
                    logger.error(f"فشل تفريغ {self._current_model}: {e}")
            self._current_model = None
            logger.info("ModelSwapper: VRAM فارغ")

    @property
    def current_model(self) -> Optional[str]:
        return self._current_model

    def is_loaded(self, model_id: str) -> bool:
        m = self._models.get(model_id)
        return m is not None and m["loaded"]

    def stats(self) -> Dict:
        return {
            "current_model": self._current_model,
            "registered_models": list(self._models.keys()),
            "swap_count": self._swap_count,
            "total_swap_time_ms": round(self._total_swap_time_ms, 1),
            "avg_swap_time_ms": round(self._total_swap_time_ms / max(self._swap_count, 1), 1),
            "vram_usage_gb": sum(
                m["vram_gb"] for m in self._models.values() if m["loaded"]
            ),
            "max_vram_gb": self._max_vram_gb,
        }
