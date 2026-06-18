"use client";
/**
 * [PHASE7] Admin Dashboard
 * Tabs: WAF stats, Webhooks, AI Observability, Health
 */
import { useEffect, useState } from "react";
import { useSession } from "next-auth/react";
import Link from "next/link";

interface WafStats {
  total_blocked?: number;
  by_category?: Record<string, number>;
  recent_blocks?: Array<{ ts: string; category: string; severity: string; path: string }>;
}

interface WebhookSub {
  id: string;
  url: string;
  events: string[];
  active: boolean;
  created_at: string;
}

interface AiStats {
  total_calls: number;
  total_tokens: number;
  total_cost_usd: number;
  by_model: Record<string, { calls: number; tokens: number; cost_usd: number }>;
}

export default function AdminDashboardPage() {
  const { data: session, status } = useSession();
  const [tab, setTab] = useState<"waf" | "webhooks" | "ai" | "health">("waf");
  const [waf, setWaf] = useState<WafStats | null>(null);
  const [webhooks, setWebhooks] = useState<WebhookSub[]>([]);
  const [ai, setAi] = useState<AiStats | null>(null);
  const [health, setHealth] = useState<Record<string, string> | null>(null);
  const [loading, setLoading] = useState(false);

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const token = (session as { apiToken?: string } | null)?.apiToken;

  useEffect(() => {
    if (status !== "authenticated" || !token) return;
    setLoading(true);
    const headers = { Authorization: `Bearer ${token}` };
    Promise.all([
      fetch(`${apiUrl}/api/waf/stats`, { headers }).then((r) => r.json()).catch(() => null),
      fetch(`${apiUrl}/api/webhooks/subscriptions`, { headers }).then((r) => r.json()).catch(() => null),
      fetch(`${apiUrl}/api/ai-observability/stats`, { headers }).then((r) => r.json()).catch(() => null),
      fetch(`${apiUrl}/healthz/live`, {}).then((r) => r.statusText).catch(() => "down"),
    ]).then(([w, wh, a, h]) => {
      setWaf(w);
      setWebhooks(Array.isArray(wh?.subscriptions) ? wh.subscriptions : []);
      setAi(a);
      setHealth({ api: typeof h === "string" ? h : "ok" });
      setLoading(false);
    });
  }, [status, token, apiUrl]);

  if (status === "loading") return <div className="p-8">Loading…</div>;
  if (status === "unauthenticated") {
    return (
      <div className="p-8">
        <h1 className="text-2xl font-bold mb-4">Admin Dashboard</h1>
        <p>You must <Link href="/login" className="text-accent underline">sign in</Link> to access this page.</p>
      </div>
    );
  }

  return (
    <div className="p-6 max-w-6xl mx-auto" dir="ltr">
      <h1 className="text-3xl font-bold mb-2">Admin Dashboard</h1>
      <p className="text-muted-foreground mb-6">
        WAF • Webhooks • AI Observability • Health
      </p>

      <div className="border-b border-border mb-4 flex gap-1" role="tablist">
        {(["waf", "webhooks", "ai", "health"] as const).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            role="tab"
            aria-selected={tab === t}
            className={`px-4 py-2 rounded-t-md ${
              tab === t ? "bg-accent text-white" : "hover:bg-muted"
            }`}
          >
            {t === "waf" && "WAF"}
            {t === "webhooks" && "Webhooks"}
            {t === "ai" && "AI Observability"}
            {t === "health" && "Health"}
          </button>
        ))}
      </div>

      {loading && <div>Loading data…</div>}

      {!loading && tab === "waf" && waf && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Total blocked" value={waf.total_blocked ?? 0} />
            <StatCard label="Categories" value={Object.keys(waf.by_category ?? {}).length} />
            <StatCard label="Recent blocks" value={(waf.recent_blocks ?? []).length} />
          </div>
          {waf.by_category && (
            <div className="border border-border rounded-md p-4">
              <h3 className="font-semibold mb-2">By category</h3>
              <div className="space-y-1">
                {Object.entries(waf.by_category).map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span className="text-sm">{k}</span>
                    <span className="font-mono text-sm">{v}</span>
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      )}

      {!loading && tab === "webhooks" && (
        <div className="space-y-3">
          <div className="flex justify-between items-center">
            <h2 className="text-xl font-semibold">Active subscriptions</h2>
            <Link href="/admin/webhooks/new" className="px-3 py-1.5 bg-accent text-white rounded-md text-sm">
              + New subscription
            </Link>
          </div>
          {webhooks.length === 0 ? (
            <p className="text-muted-foreground">No webhooks configured.</p>
          ) : (
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left border-b border-border">
                  <th className="py-2">ID</th>
                  <th>URL</th>
                  <th>Events</th>
                  <th>Active</th>
                </tr>
              </thead>
              <tbody>
                {webhooks.map((w) => (
                  <tr key={w.id} className="border-b border-border">
                    <td className="py-2 font-mono text-xs">{w.id.slice(0, 8)}…</td>
                    <td className="font-mono text-xs">{w.url}</td>
                    <td>{w.events.length} events</td>
                    <td>{w.active ? "✓" : "✗"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>
      )}

      {!loading && tab === "ai" && ai && (
        <div className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Total calls" value={ai.total_calls ?? 0} />
            <StatCard label="Total tokens" value={(ai.total_tokens ?? 0).toLocaleString()} />
            <StatCard label="Total cost (USD)" value={`$${(ai.total_cost_usd ?? 0).toFixed(4)}`} />
          </div>
          {ai.by_model && (
            <div className="border border-border rounded-md p-4">
              <h3 className="font-semibold mb-2">By model</h3>
              <table className="w-full text-sm">
                <thead>
                  <tr className="text-left border-b border-border">
                    <th className="py-2">Model</th>
                    <th>Calls</th>
                    <th>Tokens</th>
                    <th>Cost</th>
                  </tr>
                </thead>
                <tbody>
                  {Object.entries(ai.by_model).map(([model, data]) => (
                    <tr key={model} className="border-b border-border">
                      <td className="py-2 font-mono">{model}</td>
                      <td>{data.calls}</td>
                      <td>{data.tokens.toLocaleString()}</td>
                      <td>${data.cost_usd.toFixed(4)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}

      {!loading && tab === "health" && health && (
        <div className="space-y-2">
          {Object.entries(health).map(([k, v]) => (
            <div key={k} className="flex justify-between border-b border-border py-2">
              <span className="font-medium">{k}</span>
              <span className={v === "ok" ? "text-green-600" : "text-red-600"}>{v}</span>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}

function StatCard({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="border border-border rounded-md p-4">
      <div className="text-xs text-muted-foreground uppercase">{label}</div>
      <div className="text-2xl font-bold mt-1">{value}</div>
    </div>
  );
}
