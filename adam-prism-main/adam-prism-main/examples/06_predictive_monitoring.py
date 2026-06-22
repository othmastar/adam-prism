#!/usr/bin/env python3
"""
Example 06: Predictive Monitoring with CruxSight.ai
=====================================================
يوضح كيفية استخدام Adam Prism's predictive monitoring integration
مع CruxSight.ai لاكتشاف bottlenecks قبل حدوثها.
"""

import asyncio
from adam.predictive import (
    BottleneckPredictor,
    PredictiveMonitor,
    ServiceNode,
    BottleneckPattern,
)


async def demo_heuristic():
    """[PHASE4] Demo: heuristic prediction (no ML model required)"""
    print("=" * 60)
    print("Demo 1: Heuristic Prediction (no ML model)")
    print("=" * 60)

    # Create predictor in heuristic mode (no model needed)
    predictor = BottleneckPredictor(use_ml=False)

    # Simulate a microservices system under stress
    services = [
        ServiceNode(
            service_id="nginx",
            service_name="nginx-gateway",
            avg_latency_ms=2500,  # Very high!
            p99_latency_ms=5000,
            error_rate=0.15,  # 15% errors!
            capacity_score=0.3,  # Low capacity
            in_degree=0,
            out_degree=5,
        ),
        ServiceNode(
            service_id="api",
            service_name="api-server",
            avg_latency_ms=800,
            p99_latency_ms=1500,
            error_rate=0.05,
            capacity_score=0.6,
            in_degree=1,
            out_degree=2,
        ),
        ServiceNode(
            service_id="auth",
            service_name="auth-service",
            avg_latency_ms=400,
            p99_latency_ms=900,
            error_rate=0.02,
            capacity_score=0.7,
            in_degree=1,
            out_degree=1,
        ),
        ServiceNode(
            service_id="mongo",
            service_name="mongodb",
            avg_latency_ms=2200,  # High
            p99_latency_ms=4500,
            error_rate=0.08,
            capacity_score=0.4,  # Low capacity
            in_degree=4,
            out_degree=0,
        ),
        ServiceNode(
            service_id="redis",
            service_name="redis-cache",
            avg_latency_ms=100,
            p99_latency_ms=200,
            error_rate=0.0,
            capacity_score=0.9,
            in_degree=3,
            out_degree=0,
        ),
    ]

    # Call graph
    edges = [
        ("nginx", "api"),
        ("nginx", "auth"),
        ("api", "mongo"),
        ("api", "redis"),
        ("auth", "mongo"),
        ("auth", "redis"),
    ]

    # Run prediction
    prediction = await predictor.predict(services, edges)

    print(f"\n🔍 Bottleneck Probability: {prediction.bottleneck_probability:.1%}")
    print(f"⚠️  Is Bottleneck: {prediction.is_bottleneck}")
    print(f"📊 Pattern: {prediction.pattern.value}")
    print(f"📈 Pattern Confidence: {prediction.pattern_confidence:.1%}")
    print(f"⏱️  Time to Breach: {prediction.minutes_to_breach} min")
    print(f"\nRoot Cause Ranking:")
    for s in prediction.root_cause_ranking[:3]:
        print(f"   {s['rank']}. {s['service_name']} (RCS: {s['rcs_score']:.3f})")
    print(f"\n🤖 Agent message:")
    print(predictor.format_for_agent(prediction))


async def demo_monitor():
    """[PHASE4] Demo: PredictiveMonitor with stateful updates"""
    print("\n" + "=" * 60)
    print("Demo 2: PredictiveMonitor (stateful)")
    print("=" * 60)

    monitor = PredictiveMonitor()

    # Update services as metrics come in
    monitor.update_service_metrics(
        service_id="api",
        service_name="api-server",
        avg_latency_ms=1500,
        p99_latency_ms=3000,
        error_rate=0.05,
    )
    monitor.update_service_metrics(
        service_id="db",
        service_name="postgres",
        avg_latency_ms=200,
        p99_latency_ms=500,
        error_rate=0.0,
    )

    # Predict
    prediction = await monitor.predict()

    print(f"\n📊 Status: {monitor.predictor.model_version}")
    print(f"🔍 Prediction: {prediction.bottleneck_probability:.1%} bottleneck probability")
    print(f"🎯 Top suspect: {prediction.rcs_top_service}")
    print(f"📈 Inference: {prediction.inference_time_ms:.2f}ms")


async def demo_with_ml_model():
    """[PHASE4] Demo: with actual CST-GNN model (requires torch + safetensors)"""
    print("\n" + "=" * 60)
    print("Demo 3: With CST-GNN Model (requires torch)")
    print("=" * 60)

    import os
    model_path = os.environ.get("CRUXSIGHT_MODEL_PATH")
    if not model_path or not os.path.exists(model_path):
        print(f"⚠️  Model not found at {model_path}")
        print("   Set CRUXSIGHT_MODEL_PATH to enable ML inference")
        print("   Download from: https://github.com/Maral-Alshanaa/CruxSight.ai/releases")
        return

    predictor = BottleneckPredictor(model_path=model_path, use_ml=True)

    if not predictor.model_loaded:
        print(f"⚠️  Model failed to load - using heuristic fallback")
        return

    print(f"✅ Model loaded: {model_path}")
    # Same as demo 1 with real model inference...


async def main():
    await demo_heuristic()
    await demo_monitor()
    await demo_with_ml_model()

    print("\n" + "=" * 60)
    print("✅ All demos complete")
    print("=" * 60)
    print()
    print("Next steps:")
    print("1. Get the model: https://github.com/Maral-Alshanaa/CruxSight.ai")
    print("2. Set CRUXSIGHT_MODEL_PATH in your .env")
    print("3. Start the API: python main.py --port 8000")
    print("4. Visit http://localhost:8000/docs for OpenAPI docs")


if __name__ == "__main__":
    asyncio.run(main())
