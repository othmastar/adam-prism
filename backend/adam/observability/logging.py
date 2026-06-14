"""
[PHASE2] Structured JSON logging for Adam Prism.

Provides:
- JSON formatter compatible with log aggregators (Loki, Elasticsearch, etc.)
- Request ID correlation
- Log level configuration via environment variables
- Async-safe logging
"""
import json
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any

_request_id_var: ContextVar[str] = ContextVar("request_id", default="-")


def set_request_id(request_id: str | None = None) -> str:
    """Set a request ID for the current async context. Returns the ID."""
    rid = request_id or str(uuid.uuid4())[:8]
    _request_id_var.set(rid)
    return rid


def get_request_id() -> str:
    """Get the current request ID."""
    return _request_id_var.get()


class JSONFormatter(logging.Formatter):
    """Format log records as JSON for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        log_data: dict[str, Any] = {
            "timestamp": time.strftime(
                "%Y-%m-%dT%H:%M:%S", time.gmtime(record.created)
            )
            + f".{int(record.msecs):03d}Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "request_id": get_request_id(),
            "module": record.module,
            "line": record.lineno,
        }

        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in (
                "args", "asctime", "created", "exc_info", "exc_text", "filename",
                "funcName", "levelname", "levelno", "lineno", "module", "msecs",
                "message", "msg", "name", "pathname", "process", "processName",
                "relativeCreated", "stack_info", "thread", "threadName",
            ):
                try:
                    json.dumps(value)
                    log_data[key] = value
                except (TypeError, ValueError):
                    log_data[key] = str(value)

        return json.dumps(log_data, ensure_ascii=False)


def setup_logging(
    level: str | None = None,
    json_format: bool | None = None,
) -> None:
    """
    Configure logging for the entire application.
    Honors environment variables:
    - ADAM_LOG_LEVEL: DEBUG, INFO, WARNING, ERROR (default: INFO)
    - ADAM_LOG_JSON: "1" or "true" to enable JSON format
    """
    level = level or os.environ.get("ADAM_LOG_LEVEL", "INFO").upper()
    json_format = json_format if json_format is not None else \
        os.environ.get("ADAM_LOG_JSON", "0").lower() in ("1", "true", "yes")

    # Convert string to logging level
    numeric_level = getattr(logging, level, logging.INFO)

    # Build formatter
    if json_format:
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )

    # Configure root logger
    root = logging.getLogger()
    root.setLevel(numeric_level)
    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    root.addHandler(handler)

    # Quiet down noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("multipart").setLevel(logging.WARNING)
