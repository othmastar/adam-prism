"""
[PHASE6] AI Observability — token usage, costs, latency tracking.
Like LangSmith but for Adam Prism.
"""
from __future__ import annotations

import logging
import time
from collections import defaultdict
from dataclasses import asdict, dataclass, field
from typing import Any

logger = logging.getLogger("adam_prism.ai_observability")

PRICING_USD_PER_1K_TOKENS = {
    "ollama": 0.0,  # Local - free
    "openai": {
        "gpt-4": {"input": 0.03, "output": 0.06},
        "gpt-4-turbo": {"input": 0.01, "output": 0.03},
        "gpt-3.5-turbo": {"input": 0.0005, "output": 0.0015},
        "gpt-4o": {"input": 0.005, "output": 0.015},
        "gpt-4o-mini": {"input": 0.00015, "output": 0.0006},
    },
    "anthropic": {
        "claude-3-opus": {"input": 0.015, "output": 0.075},
        "claude-3-sonnet": {"input": 0.003, "output": 0.015},
        "claude-3-haiku": {"input": 0.00025, "output": 0.00125},
    },
}


@dataclass
class UsageRecord:
    """[PHASE6] Single LLM call usage record."""

    timestamp: float = field(default_factory=time.time)
    user_id: str | None = None
    tenant_id: str | None = None
    session_id: str | None = None
    provider: str = "unknown"
    model: str = "unknown"
    operation: str = "chat"  # chat, embed, completion
    input_tokens: int = 0
    output_tokens: int = 0
    total_tokens: int = 0
    latency_ms: float = 0.0
    cost_usd: float = 0.0
    success: bool = True
    error: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)


class AIObservability:
    """[PHASE6] Tracks LLM usage, costs, and latencies."""

    def __init__(self, max_records: int = 10000):
        self._records: list[UsageRecord] = []
        self._max_records = max_records
        # Aggregated stats
        self._by_user: dict[str, list[UsageRecord]] = defaultdict(list)
        self._by_tenant: dict[str, list[UsageRecord]] = defaultdict(list)
        self._by_model: dict[str, list[UsageRecord]] = defaultdict(list)

    def record(
        self,
        provider: str,
        model: str,
        input_tokens: int = 0,
        output_tokens: int = 0,
        latency_ms: float = 0.0,
        user_id: str | None = None,
        tenant_id: str | None = None,
        session_id: str | None = None,
        success: bool = True,
        error: str | None = None,
        operation: str = "chat",
        metadata: dict[str, Any] | None = None,
    ) -> UsageRecord:
        """[PHASE6] Record an LLM call."""
        total = input_tokens + output_tokens
        cost = self._calculate_cost(provider, model, input_tokens, output_tokens)

        rec = UsageRecord(
            provider=provider,
            model=model,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            total_tokens=total,
            latency_ms=latency_ms,
            cost_usd=cost,
            user_id=user_id,
            tenant_id=tenant_id,
            session_id=session_id,
            success=success,
            error=error,
            operation=operation,
            metadata=metadata or {},
        )

        self._records.append(rec)
        if user_id:
            self._by_user[user_id].append(rec)
        if tenant_id:
            self._by_tenant[tenant_id].append(rec)
        self._by_model[model].append(rec)

        # [PHASE6] Trim old records
        if len(self._records) > self._max_records:
            self._records = self._records[-self._max_records:]

        return rec

    def _calculate_cost(self, provider: str, model: str, input_tok: int, output_tok: int) -> float:
        """[PHASE6] Calculate cost in USD based on pricing."""
        if provider == "ollama":
            return 0.0  # Local models

        provider_pricing = PRICING_USD_PER_1K_TOKENS.get(provider, {})
        if not isinstance(provider_pricing, dict):
            return 0.0

        model_pricing = provider_pricing.get(model, {})
        if not isinstance(model_pricing, dict):
            return 0.0

        input_cost = (input_tok / 1000.0) * model_pricing.get("input", 0)
        output_cost = (output_tok / 1000.0) * model_pricing.get("output", 0)
        return round(input_cost + output_cost, 6)

    def get_stats(
        self,
        user_id: str | None = None,
        tenant_id: str | None = None,
        since: float | None = None,
    ) -> dict[str, Any]:
        """[PHASE6] Get aggregated usage stats."""
        records = self._records
        if user_id:
            records = self._by_user.get(user_id, [])
        elif tenant_id:
            records = self._by_tenant.get(tenant_id, [])
        if since:
            records = [r for r in records if r.timestamp >= since]

        total_cost = sum(r.cost_usd for r in records)
        total_tokens = sum(r.total_tokens for r in records)
        total_input = sum(r.input_tokens for r in records)
        total_output = sum(r.output_tokens for r in records)
        avg_latency = (
            sum(r.latency_ms for r in records) / len(records) if records else 0
        )
        success_count = sum(1 for r in records if r.success)
        success_rate = success_count / len(records) if records else 0

        return {
            "record_count": len(records),
            "total_cost_usd": round(total_cost, 4),
            "total_tokens": total_tokens,
            "input_tokens": total_input,
            "output_tokens": total_output,
            "avg_latency_ms": round(avg_latency, 2),
            "success_rate": round(success_rate, 4),
            "by_model": {
                m: {
                    "calls": len(rs),
                    "tokens": sum(r.total_tokens for r in rs),
                    "cost_usd": round(sum(r.cost_usd for r in rs), 4),
                }
                for m, rs in self._by_model.items()
            },
        }

    def get_recent(self, limit: int = 100) -> list[UsageRecord]:
        """[PHASE6] Get recent records."""
        return self._records[-limit:]


# [PHASE6] Singleton
_ai_obs: AIObservability | None = None


def get_ai_observability() -> AIObservability:
    """[PHASE6] Get the singleton AI observability instance."""
    global _ai_obs
    if _ai_obs is None:
        _ai_obs = AIObservability()
    return _ai_obs
