"""
[PHASE4] Predictive monitoring tool for Adam Prism.

Integrates CruxSight.ai bottleneck prediction as a tool the agent can invoke.
"""
from __future__ import annotations

import logging
import time
from typing import Any

from adam.predictive.bottleneck import (
    BottleneckPrediction,
    BottleneckPredictor,
    ServiceNode,
)

logger = logging.getLogger("adam_prism.predictive_tool")


class PredictiveMonitor:
    """[PHASE4] Wraps BottleneckPredictor as an Adam tool."""

    def __init__(self, model_path: str | None = None):
        self.predictor = BottleneckPredictor(model_path=model_path)
        self.last_prediction: BottleneckPrediction | None = None
        self.last_run: float = 0
        self._services_state: dict[str, ServiceNode] = {}

    def update_service(self, service: ServiceNode) -> None:
        """[PHASE4] Update the agent's view of a service (e.g., from metrics)."""
        self._services_state[service.service_id] = service

    def update_service_metrics(
        self,
        service_id: str,
        service_name: str,
        avg_latency_ms: float,
        p99_latency_ms: float,
        error_rate: float,
        capacity_score: float = 1.0,
        in_degree: int = 0,
        out_degree: int = 0,
    ) -> None:
        """[PHASE4] Convenience method to update a service."""
        self.update_service(
            ServiceNode(
                service_id=service_id,
                service_name=service_name,
                avg_latency_ms=avg_latency_ms,
                p99_latency_ms=p99_latency_ms,
                error_rate=error_rate,
                capacity_score=capacity_score,
                in_degree=in_degree,
                out_degree=out_degree,
            )
        )

    async def predict(
        self,
        edges: list[tuple[str, str]] | None = None,
    ) -> BottleneckPrediction:
        """[PHASE4] Run prediction on current state."""
        services = list(self._services_state.values())
        edges = edges or []
        prediction = await self.predictor.predict(services, edges)
        self.last_prediction = prediction
        self.last_run = time.time()
        return prediction

    async def predict_from_metrics(
        self,
        service_metrics: list[dict[str, Any]],
        edges: list[tuple[str, str]] | None = None,
    ) -> BottleneckPrediction:
        """[PHASE4] Predict directly from a list of metric dicts.

        Each dict must have: service_id, service_name, avg_latency_ms,
        p99_latency_ms, error_rate. Optional: capacity_score, in_degree, out_degree.
        """
        services = []
        for m in service_metrics:
            services.append(
                ServiceNode(
                    service_id=m["service_id"],
                    service_name=m["service_name"],
                    avg_latency_ms=m.get("avg_latency_ms", 0),
                    p99_latency_ms=m.get("p99_latency_ms", 0),
                    error_rate=m.get("error_rate", 0),
                    capacity_score=m.get("capacity_score", 1.0),
                    in_degree=m.get("in_degree", 0),
                    out_degree=m.get("out_degree", 0),
                )
            )
        edges = edges or []
        prediction = await self.predictor.predict(services, edges)
        self.last_prediction = prediction
        self.last_run = time.time()
        return prediction

    async def run_health_check(
        self, services: list[dict[str, Any]], edges: list[tuple[str, str]] | None = None
    ) -> dict:
        """[PHASE4] Run a predictive health check (the Adam tool entry point)."""
        prediction = await self.predict_from_metrics(services, edges)
        return {
            "success": True,
            "data": {
                "prediction": prediction.to_dict(),
                "alert": self.predictor.should_alert(prediction),
                "agent_message": self.predictor.format_for_agent(prediction),
            },
        }
