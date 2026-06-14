"""
[PHASE5] OpenTelemetry tracing for Adam Prism.
Provides distributed tracing across the engine, API, and external calls.
"""
from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any
from collections.abc import Iterator

logger = logging.getLogger("adam_prism.observability.tracing")

# [PHASE5] OpenTelemetry is optional - gracefully degrade
try:
    from opentelemetry import trace
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import (
        BatchSpanProcessor,
        ConsoleSpanExporter,
        SimpleSpanProcessor,
    )

    OTEL_AVAILABLE = True
except ImportError:
    OTEL_AVAILABLE = False
    logger.warning("OpenTelemetry not available - tracing disabled")


_initialized = False
_tracer = None


def setup_tracing(
    service_name: str = "adam-prism",
    service_version: str = "2.0.0",
    exporter_type: str | None = None,
    otlp_endpoint: str | None = None,
) -> bool:
    """
    [PHASE5] Initialize OpenTelemetry tracing.

    Args:
        service_name: Name of this service
        service_version: Version string
        exporter_type: "console", "otlp", or None (no exporter, just spans)
        otlp_endpoint: OTLP collector endpoint (e.g., http://localhost:4317)

    Returns:
        True if tracing was initialized, False otherwise
    """
    global _initialized, _tracer

    if not OTEL_AVAILABLE:
        logger.warning("OpenTelemetry not installed - tracing disabled")
        return False

    if _initialized:
        return True

    if os.environ.get("ADAM_TRACING_ENABLED", "1") != "1":
        logger.info("Tracing disabled by ADAM_TRACING_ENABLED=0")
        return False

    try:
        resource = Resource.create({
            "service.name": service_name,
            "service.version": service_version,
        })
        provider = TracerProvider(resource=resource)

        exporter_type = exporter_type or os.environ.get("ADAM_TRACING_EXPORTER", "console")

        if exporter_type == "otlp" and otlp_endpoint:
            try:
                from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
                exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
                provider.add_span_processor(BatchSpanProcessor(exporter))
                logger.info(f"Tracing: OTLP exporter to {otlp_endpoint}")
            except ImportError:
                logger.warning("OTLP exporter not available, using console")
                provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        elif exporter_type == "console":
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
            logger.info("Tracing: Console exporter")
        else:
            logger.info("Tracing: no exporter (spans only)")
        # else: no exporter

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer(service_name, service_version)
        _initialized = True
        logger.info("OpenTelemetry tracing initialized")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize tracing: {e}")
        return False


def get_tracer():
    """[PHASE5] Get the configured tracer, or a no-op if not initialized."""
    global _tracer
    if _tracer is None and OTEL_AVAILABLE:
        _tracer = trace.get_tracer("adam-prism")
    return _tracer


@contextmanager
def trace_span(
    name: str,
    attributes: dict[str, Any] | None = None,
) -> Iterator[Any]:
    """
    [PHASE5] Context manager for tracing a span.
    Works whether OpenTelemetry is available or not.
    """
    if not OTEL_AVAILABLE or get_tracer() is None:
        # No-op span
        yield None
        return

    tracer = get_tracer()
    with tracer.start_as_current_span(name, attributes=attributes or {}) as span:
        try:
            yield span
        except Exception as e:
            span.record_exception(e)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(e)))
            raise


def trace_function(name: str | None = None):
    """
    [PHASE5] Decorator for tracing function calls.
    Usage:
        @trace_function("my_operation")
        async def my_operation():
            ...
    """
    def decorator(func):
        func_name = name or func.__qualname__

        if asyncio.iscoroutinefunction(func):
            @functools.wraps(func)
            async def async_wrapper(*args, **kwargs):
                with trace_span(func_name) as span:
                    if span:
                        span.set_attribute("function.name", func_name)
                    return await func(*args, **kwargs)
            return async_wrapper
        else:
            @functools.wraps(func)
            def sync_wrapper(*args, **kwargs):
                with trace_span(func_name) as span:
                    if span:
                        span.set_attribute("function.name", func_name)
                    return func(*args, **kwargs)
            return sync_wrapper

    return decorator


# Imports needed for trace_function
import asyncio
import functools
