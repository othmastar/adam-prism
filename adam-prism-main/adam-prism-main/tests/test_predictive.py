"""
[PHASE4] Tests for CruxSight.ai predictive monitoring integration.
"""
import pytest
from adam.predictive.bottleneck import (
    BottleneckPattern,
    BottleneckPrediction,
    BottleneckPredictor,
    ServiceNode,
)
from adam.predictive.tool import PredictiveMonitor


class TestBottleneckPattern:
    """Test the BottleneckPattern enum."""

    def test_all_patterns_defined(self):
        patterns = list(BottleneckPattern)
        assert len(patterns) >= 7  # A through G + UNKNOWN

    def test_from_str_valid(self):
        assert BottleneckPattern.from_str("A_entry_only") == BottleneckPattern.A_ENTRY_ONLY
        assert BottleneckPattern.from_str("D_entry_storage") == BottleneckPattern.D_ENTRY_STORAGE

    def test_from_str_invalid_returns_unknown(self):
        assert BottleneckPattern.from_str("invalid_pattern") == BottleneckPattern.UNKNOWN


class TestServiceNode:
    """Test ServiceNode dataclass."""

    def test_basic_node(self):
        node = ServiceNode(
            service_id="svc-1",
            service_name="api",
            avg_latency_ms=100,
            p99_latency_ms=500,
        )
        assert node.service_id == "svc-1"
        assert node.avg_latency_ms == 100
        assert not node.is_constrained  # default capacity 1.0

    def test_constrained_node(self):
        node = ServiceNode(
            service_id="svc-1",
            service_name="db",
            capacity_score=0.3,
        )
        assert node.is_constrained

    def test_to_dict(self):
        node = ServiceNode(service_id="s1", service_name="api")
        d = node.to_dict()
        assert "service_id" in d
        assert "is_constrained" in d


class TestBottleneckPrediction:
    """Test BottleneckPrediction dataclass."""

    def test_to_dict_default(self):
        pred = BottleneckPrediction()
        d = pred.to_dict()
        assert "bottleneck_probability" in d
        assert "pattern" in d
        assert "is_bottleneck" in d

    def test_to_dict_with_values(self):
        pred = BottleneckPrediction(
            bottleneck_probability=0.85,
            is_bottleneck=True,
            pattern=BottleneckPattern.D_ENTRY_STORAGE,
            pattern_confidence=0.9,
            minutes_to_breach=3.5,
            rcs_top_service="nginx-gateway",
            graph_nodes=10,
            graph_edges=15,
        )
        d = pred.to_dict()
        assert d["bottleneck_probability"] == 0.85
        assert d["pattern"] == "D_entry_storage"
        assert d["minutes_to_breach"] == 3.5


class TestBottleneckPredictorHeuristic:
    """Test heuristic inference (no ML model needed)."""

    @pytest.fixture
    def predictor(self):
        return BottleneckPredictor(use_ml=False)

    @pytest.mark.asyncio
    async def test_empty_services(self, predictor):
        pred = await predictor.predict([])
        assert pred.bottleneck_probability == 0.0
        assert pred.graph_nodes == 0

    @pytest.mark.asyncio
    async def test_healthy_services(self, predictor):
        services = [
            ServiceNode(service_id=f"svc-{i}", service_name=f"service-{i}", avg_latency_ms=10, p99_latency_ms=50)
            for i in range(3)
        ]
        pred = await predictor.predict(services)
        assert pred.bottleneck_probability < 0.5
        assert not pred.is_bottleneck
        assert pred.inference_time_ms > 0

    @pytest.mark.asyncio
    async def test_degraded_services(self, predictor):
        services = [
            ServiceNode(service_id="nginx", service_name="nginx-gateway",
                        avg_latency_ms=2000, p99_latency_ms=5000, error_rate=0.1,
                        in_degree=0, out_degree=5, capacity_score=0.3),
            ServiceNode(service_id="db", service_name="postgres-db",
                        avg_latency_ms=1500, p99_latency_ms=4000, error_rate=0.05,
                        in_degree=5, out_degree=0, capacity_score=0.4),
        ]
        edges = [("nginx", "db")]
        pred = await predictor.predict(services, edges)
        # High latency + entry + storage → Pattern D most likely
        assert pred.bottleneck_probability > 0.3
        assert len(pred.root_cause_ranking) > 0
        assert pred.rcs_top_service is not None
        assert pred.minutes_to_breach is not None or pred.bottleneck_probability < 0.5

    @pytest.mark.asyncio
    async def test_pattern_d_entry_plus_storage(self, predictor):
        services = [
            ServiceNode(service_id="nginx", service_name="nginx", avg_latency_ms=1000, error_rate=0.1, capacity_score=0.2, in_degree=0),
            ServiceNode(service_id="mongo", service_name="mongodb", avg_latency_ms=900, error_rate=0.05, capacity_score=0.3, out_degree=0),
        ]
        edges = [("nginx", "mongo")]
        pred = await predictor.predict(services, edges)
        # Should detect Pattern D
        assert pred.pattern == BottleneckPattern.D_ENTRY_STORAGE
        assert pred.pattern_confidence > 0.5

    def test_should_alert(self, predictor):
        # Low risk - no alert
        pred = BottleneckPrediction(bottleneck_probability=0.3, is_bottleneck=False, minutes_to_breach=10)
        assert not predictor.should_alert(pred)

        # High probability - alert
        pred = BottleneckPrediction(bottleneck_probability=0.85, is_bottleneck=True, minutes_to_breach=3)
        assert predictor.should_alert(pred)

    def test_format_for_agent_healthy(self, predictor):
        pred = BottleneckPrediction(bottleneck_probability=0.2, is_bottleneck=False)
        msg = predictor.format_for_agent(pred)
        assert "سليم" in msg or "لا حاجة" in msg

    def test_format_for_agent_critical(self, predictor):
        pred = BottleneckPrediction(
            bottleneck_probability=0.85,
            is_bottleneck=True,
            pattern=BottleneckPattern.D_ENTRY_STORAGE,
            pattern_confidence=0.9,
            minutes_to_breach=3.0,
            root_cause_ranking=[{
                "service_id": "nginx",
                "service_name": "nginx-gateway",
                "rcs_score": 0.8,
                "rank": 1,
            }],
            rcs_top_service="nginx",
        )
        msg = predictor.format_for_agent(pred)
        assert "⚠️" in msg or "تحذير" in msg
        assert "nginx-gateway" in msg
        assert "D_entry_storage" in msg


class TestPredictiveMonitor:
    """Test the PredictiveMonitor wrapper."""

    @pytest.fixture
    def monitor(self):
        return PredictiveMonitor()

    def test_initial_state(self, monitor):
        assert monitor.last_prediction is None
        assert monitor.last_run == 0
        assert len(monitor._services_state) == 0

    def test_update_service(self, monitor):
        node = ServiceNode(service_id="svc-1", service_name="api")
        monitor.update_service(node)
        assert "svc-1" in monitor._services_state

    def test_update_service_metrics(self, monitor):
        monitor.update_service_metrics(
            service_id="svc-1",
            service_name="api",
            avg_latency_ms=100,
            p99_latency_ms=500,
            error_rate=0.01,
        )
        assert "svc-1" in monitor._services_state
        assert monitor._services_state["svc-1"].avg_latency_ms == 100

    @pytest.mark.asyncio
    async def test_predict_empty(self, monitor):
        pred = await monitor.predict()
        assert pred.bottleneck_probability == 0.0

    @pytest.mark.asyncio
    async def test_predict_with_services(self, monitor):
        monitor.update_service_metrics(
            service_id="api",
            service_name="api-server",
            avg_latency_ms=1500,
            p99_latency_ms=3000,
            error_rate=0.05,
        )
        pred = await monitor.predict()
        assert pred.bottleneck_probability > 0

    @pytest.mark.asyncio
    async def test_predict_from_metrics(self, monitor):
        metrics = [
            {
                "service_id": "api",
                "service_name": "api-server",
                "avg_latency_ms": 1500,
                "p99_latency_ms": 3000,
                "error_rate": 0.05,
            },
            {
                "service_id": "db",
                "service_name": "postgres",
                "avg_latency_ms": 200,
                "p99_latency_ms": 500,
                "error_rate": 0.0,
            },
        ]
        pred = await monitor.predict_from_metrics(metrics)
        assert pred.bottleneck_probability > 0
        assert pred.rcs_top_service is not None

    @pytest.mark.asyncio
    async def test_run_health_check(self, monitor):
        metrics = [
            {
                "service_id": "api",
                "service_name": "api-server",
                "avg_latency_ms": 100,
                "p99_latency_ms": 200,
                "error_rate": 0.0,
            },
        ]
        result = await monitor.run_health_check(metrics)
        assert result["success"] is True
        assert "prediction" in result["data"]
        assert "agent_message" in result["data"]
        assert "alert" in result["data"]
