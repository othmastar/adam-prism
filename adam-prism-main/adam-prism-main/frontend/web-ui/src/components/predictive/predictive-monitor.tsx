"use client";

/**
 * [PHASE4] Predictive Monitoring Dashboard
 * Shows CruxSight.ai bottleneck predictions in real-time
 */
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";

interface BottleneckPrediction {
  bottleneck_probability: number;
  is_bottleneck: boolean;
  pattern: string;
  pattern_confidence: number;
  minutes_to_breach: number | null;
  root_cause_ranking: Array<{
    service_id: string;
    service_name: string;
    rcs_score: number;
    rank: number;
  }>;
  rcs_top_service: string | null;
  graph_nodes: number;
  graph_edges: number;
  model_version: string;
  inference_time_ms: number;
  timestamp: number;
}

const PATTERN_LABELS: Record<string, string> = {
  A_entry_only: "A — Entry layer",
  B_storage_core: "B — Storage core",
  C_middle_tier: "C — Middle tier",
  D_entry_storage: "D — Entry + Storage (Hybrid)",
  E_full_cascade: "E — Full cascade",
  F_partial_storage: "F — Partial storage",
  G_home_workflow: "G — Home workflow",
  unknown: "Unknown",
};

export function PredictiveMonitor() {
  const [prediction, setPrediction] = useState<BottleneckPrediction | null>(null);
  const [status, setStatus] = useState<{ has_prediction: boolean; model_version: string } | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || "";

  const fetchStatus = async () => {
    try {
      const r = await fetch(`${apiUrl}/api/predict/status`, {
        headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
      });
      if (r.ok) {
        const data = await r.json();
        setStatus(data);
      }
    } catch (e) {
      // Silently fail - status is optional
    }
  };

  const fetchPrediction = async () => {
    try {
      const r = await fetch(`${apiUrl}/api/predict/last`, {
        headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
      });
      if (r.ok) {
        const data = await r.json();
        if (data.prediction) {
          setPrediction(data.prediction);
        }
      }
    } catch (e) {
      // Silently fail - no prediction yet is OK
    }
  };

  const runDemoPrediction = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${apiUrl}/api/predict/bottleneck`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          ...(apiKey ? { Authorization: `Bearer ${apiKey}` } : {}),
        },
        body: JSON.stringify({
          services: [
            { service_id: "nginx", service_name: "nginx-gateway", avg_latency_ms: 2500, p99_latency_ms: 5000, error_rate: 0.15, capacity_score: 0.3, in_degree: 0, out_degree: 5 },
            { service_id: "api", service_name: "api-server", avg_latency_ms: 800, p99_latency_ms: 1500, error_rate: 0.05, capacity_score: 0.6, in_degree: 1, out_degree: 2 },
            { service_id: "auth", service_name: "auth-service", avg_latency_ms: 400, p99_latency_ms: 900, error_rate: 0.02, capacity_score: 0.7, in_degree: 1, out_degree: 1 },
            { service_id: "mongo", service_name: "mongodb", avg_latency_ms: 2200, p99_latency_ms: 4500, error_rate: 0.08, capacity_score: 0.4, in_degree: 4, out_degree: 0 },
            { service_id: "redis", service_name: "redis-cache", avg_latency_ms: 100, p99_latency_ms: 200, error_rate: 0.0, capacity_score: 0.9, in_degree: 3, out_degree: 0 },
          ],
          edges: [
            ["nginx", "api"],
            ["nginx", "auth"],
            ["api", "mongo"],
            ["api", "redis"],
            ["auth", "mongo"],
            ["auth", "redis"],
          ],
        }),
      });
      if (r.ok) {
        const data = await r.json();
        if (data.data?.prediction) {
          setPrediction(data.data.prediction);
        }
        await fetchStatus();
      } else {
        setError(`HTTP ${r.status}: ${await r.text()}`);
      }
    } catch (e: any) {
      setError(e?.message || "Failed to run prediction");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
    fetchPrediction();
    const interval = setInterval(fetchPrediction, 10000);
    return () => clearInterval(interval);
  }, []);

  const probability = prediction ? Math.round(prediction.bottleneck_probability * 100) : 0;
  const isAlert = prediction?.is_bottleneck ?? false;

  return (
    <Card className="w-full">
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <span className="text-2xl">🔮</span>
            <span>التنبؤ الاستباقي — CruxSight.ai</span>
          </CardTitle>
          <div className="flex items-center gap-2">
            {status && (
              <Badge variant="outline" className="text-xs">
                {status.model_version}
              </Badge>
            )}
            <button
              onClick={runDemoPrediction}
              disabled={loading}
              className="px-3 py-1 text-xs bg-accent text-white rounded hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "جاري التحليل..." : "تشغيل تحليل تجريبي"}
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div className="bg-destructive/10 text-destructive text-sm p-3 rounded-md mb-4">
            {error}
          </div>
        )}

        {!prediction ? (
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">في انتظار أول تنبؤ...</p>
            <p className="text-xs mt-2">
              اضغط "تشغيل تحليل تجريبي" لمحاكاة bottleneck متوقع
            </p>
          </div>
        ) : (
          <div className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div className={`p-4 rounded-lg ${isAlert ? "bg-destructive/10" : "bg-emerald-500/10"}`}>
                <div className="text-xs text-muted-foreground">احتمالية Bottleneck</div>
                <div className={`text-3xl font-bold ${isAlert ? "text-destructive" : "text-emerald-500"}`}>
                  {probability}%
                </div>
                <div className="text-xs mt-1">
                  {isAlert ? "⚠️ تحذير" : "✅ نظام سليم"}
                </div>
              </div>
              <div className="p-4 rounded-lg bg-muted">
                <div className="text-xs text-muted-foreground">النمط المكتشف</div>
                <div className="text-lg font-semibold">
                  {PATTERN_LABELS[prediction.pattern] || prediction.pattern}
                </div>
                <div className="text-xs mt-1">
                  ثقة: {Math.round(prediction.pattern_confidence * 100)}%
                </div>
              </div>
              <div className="p-4 rounded-lg bg-muted">
                <div className="text-xs text-muted-foreground">الوقت للفشل</div>
                <div className="text-2xl font-bold">
                  {prediction.minutes_to_breach != null
                    ? `${prediction.minutes_to_breach.toFixed(1)} د`
                    : "—"}
                </div>
                <div className="text-xs mt-1 text-muted-foreground">
                  {prediction.graph_nodes} nodes, {prediction.graph_edges} edges
                </div>
              </div>
            </div>

            {prediction.root_cause_ranking.length > 0 && (
              <div>
                <div className="text-sm font-semibold mb-2">الترتيب حسب RCS (Resource Constraint Score)</div>
                <div className="space-y-2">
                  {prediction.root_cause_ranking.map((s) => (
                    <div
                      key={s.service_id}
                      className="flex items-center justify-between p-2 rounded bg-muted/50"
                    >
                      <div className="flex items-center gap-2">
                        <span className="text-xs font-mono text-muted-foreground">#{s.rank}</span>
                        <span className="font-medium">{s.service_name}</span>
                      </div>
                      <div className="flex items-center gap-2">
                        <div className="w-24 h-2 bg-muted rounded overflow-hidden">
                          <div
                            className="h-full bg-accent"
                            style={{ width: `${Math.min(s.rcs_score * 100, 100)}%` }}
                          />
                        </div>
                        <span className="text-xs font-mono">
                          {s.rcs_score.toFixed(3)}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            <div className="text-xs text-muted-foreground pt-2 border-t">
              <span>آخر تحديث: {new Date(prediction.timestamp * 1000).toLocaleTimeString("ar-EG")}</span>
              <span className="mx-2">•</span>
              <span>استغرق التحليل: {prediction.inference_time_ms.toFixed(1)}ms</span>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
