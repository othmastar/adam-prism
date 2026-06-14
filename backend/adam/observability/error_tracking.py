"""
[PHASE5] Error tracking integration (Sentry-compatible).
Catches unhandled exceptions in FastAPI and reports them.
"""
from __future__ import annotations

import logging
import os
import traceback
from contextvars import ContextVar
from typing import Any
from datetime import UTC

logger = logging.getLogger("adam_prism.error_tracking")

_request_id: ContextVar[str] = ContextVar("request_id", default="-")


def set_request_id(rid: str) -> None:
    _request_id.set(rid)


def get_request_id() -> str:
    return _request_id.get()


class ErrorTracker:
    """[PHASE5] Sentry-compatible error tracker.

    Captures exceptions, includes context (request ID, user, etc.),
    and sends to configured endpoint (Sentry, custom, or logs only).
    """

    def __init__(self):
        self.endpoint = os.environ.get("ADAM_SENTRY_DSN") or os.environ.get("SENTRY_DSN")
        self.environment = os.environ.get("ADAM_ENV", "production")
        self.release = os.environ.get("ADAM_VERSION", "2.0.0")
        self.sample_rate = float(os.environ.get("ADAM_SENTRY_SAMPLE_RATE", "1.0"))
        self.enabled = bool(self.endpoint) and self.sample_rate > 0

    def capture_exception(
        self,
        exc: Exception,
        context: dict[str, Any] | None = None,
        level: str = "error",
    ) -> None:
        """[PHASE5] Capture an exception with full context."""
        if not self.enabled:
            # [PHASE5] Local-only mode: just log with full context
            logger.error(
                "[exception] %s: %s",
                type(exc).__name__,
                str(exc),
                extra={
                    "exc_type": type(exc).__name__,
                    "exc_message": str(exc),
                    "traceback": traceback.format_exception(type(exc), exc, exc.__traceback__),
                    "ctx": context or {},
                    "request_id": get_request_id(),
                    "level": level,
                },
            )
            return

        # [PHASE5] Sentry-compatible payload
        try:
            import httpx

            payload = {
                "event_id": _generate_event_id(),
                "timestamp": _now_iso(),
                "platform": "python",
                "level": level,
                "logger": "adam_prism",
                "transaction": f"{context.get('method', '?')} {context.get('path', '?')}" if context else "unknown",
                "server_name": os.uname().nodename if hasattr(os, "uname") else "unknown",
                "release": self.release,
                "environment": self.environment,
                "tags": {
                    "request_id": get_request_id(),
                },
                "extra": context or {},
                "exception": {
                    "values": [
                        {
                            "type": type(exc).__name__,
                            "value": str(exc),
                            "stacktrace": {
                                "frames": _format_frames(exc.__traceback__),
                            },
                        }
                    ]
                },
            }

            httpx.post(
                f"{self.endpoint}/api/{self._get_project_id()}/store/",
                json=payload,
                timeout=2.0,
            )
        except Exception as e:
            logger.error(f"Failed to send to error tracker: {e}")

    def capture_message(
        self,
        message: str,
        level: str = "info",
        context: dict[str, Any] | None = None,
    ) -> None:
        """[PHASE5] Capture a message (non-exception)."""
        if not self.enabled:
            logger.log(
                logging.INFO if level == "info" else logging.WARNING,
                message,
                extra={"context": context or {}, "request_id": get_request_id()},
            )
            return

    def _get_project_id(self) -> str:
        """[PHASE5] Extract project ID from Sentry DSN."""
        if not self.endpoint:
            return "0"
        # DSN format: https://key@host/project_id
        try:
            return self.endpoint.rstrip("/").split("/")[-1]
        except Exception:
            return "0"


def _generate_event_id() -> str:
    import secrets

    return secrets.token_hex(16)


def _now_iso() -> str:
    from datetime import datetime

    return datetime.now(UTC).isoformat()


def _format_frames(tb) -> list[dict[str, Any]]:
    """[PHASE5] Format traceback frames for Sentry."""
    frames = []
    if tb is None:
        return frames
    while tb:
        frame = tb.tb_frame
        frames.append({
            "filename": frame.f_code.co_filename,
            "function": frame.f_code.co_name,
            "lineno": tb.tb_lineno,
        })
        tb = tb.tb_next
    return frames


# [PHASE5] Singleton
_error_tracker: ErrorTracker | None = None


def get_error_tracker() -> ErrorTracker:
    """[PHASE5] Get the singleton error tracker."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker
