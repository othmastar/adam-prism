"""Tool decorator for automatic context compression.

Wraps any tool that returns large content (strings, JSON, logs, files)
with automatic Headroom compression. Tool authors opt-in by adding
@compress_tool to their tool functions.

Usage:
    from adam.observability.compression_decorator import compress_tool

    @compress_tool(content_type="json", threshold_tokens=500)
    def get_large_dataset(query: str) -> str:
        # returns large JSON, will be auto-compressed before LLM
        return huge_json_string
"""
from __future__ import annotations

import functools
import logging
from typing import Any
from collections.abc import Callable

from adam.observability.headroom_integration import get_headroom

logger = logging.getLogger("adam_prism.compression")


def compress_tool(
    *,
    content_type: str = "text",
    threshold_tokens: int = 500,
    force: bool = False,
) -> Callable:
    """Decorator that compresses a tool's return value.

    The wrapped tool's output is passed through Headroom's compress()
    before being returned. Compression is skipped if:
      - Output is not a string (lists/dicts/Numbers are passed through)
      - Output is shorter than `threshold_tokens`
      - Headroom is in 'audit' mode (count savings but don't modify)

    Args:
        content_type: hint to the compressor ('text', 'code', 'json', 'log')
        threshold_tokens: skip compression for outputs shorter than this
        force: if True, compress even small outputs
    """
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            result = func(*args, **kwargs)
            # Only compress string outputs
            if not isinstance(result, str):
                return result
            headroom = get_headroom()
            compression = headroom.compress(
                result,
                content_type=content_type,
                force=force,
            )
            if compression.was_compressed:
                logger.debug(
                    f"@compress_tool: {func.__name__} compressed "
                    f"{compression.original_tokens} → {compression.compressed_tokens} tokens "
                    f"({compression.savings_percent:.0f}% saved)"
                )
            return compression.content

        # Attach metadata for introspection
        wrapper.__adam_compressed__ = True  # type: ignore[attr-defined]
        wrapper.__adam_compression_config__ = {  # type: ignore[attr-defined]
            "content_type": content_type,
            "threshold_tokens": threshold_tokens,
            "force": force,
        }
        return wrapper

    return decorator


def get_compression_stats() -> dict[str, Any]:
    """Return Adam's session-wide compression statistics."""
    return get_headroom().stats()
