"use client";

/**
 * [PHASE5] Audit Log Viewer
 * Shows security events, tool calls, and admin actions.
 */
import { useEffect, useState } from "react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Shield, AlertTriangle, CheckCircle, XCircle } from "lucide-react";

interface AuditEntry {
  timestamp?: number;
  action?: string;
  user_id?: string;
  ip_address?: string;
  details?: Record<string, unknown>;
  severity?: "info" | "warning" | "critical";
}

const SEVERITY_STYLES = {
  info: { icon: CheckCircle, className: "text-blue-500", variant: "outline" as const, label: "Info" },
  warning: { icon: AlertTriangle, className: "text-yellow-500", variant: "secondary" as const, label: "Warning" },
  critical: { icon: XCircle, className: "text-red-500", variant: "destructive" as const, label: "Critical" },
};

export function AuditLogViewer() {
  const [entries, setEntries] = useState<AuditEntry[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [filter, setFilter] = useState<"all" | "warning" | "critical">("all");

  const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const apiKey = process.env.NEXT_PUBLIC_API_KEY || "";

  const fetchAudit = async () => {
    setLoading(true);
    setError(null);
    try {
      const r = await fetch(`${apiUrl}/api/audit?limit=200`, {
        headers: apiKey ? { Authorization: `Bearer ${apiKey}` } : {},
      });
      if (r.ok) {
        const data = await r.json();
        setEntries(data.entries || []);
      } else {
        setError(`HTTP ${r.status}: ${await r.text()}`);
      }
    } catch (e: any) {
      setError(e?.message || "Failed to load audit log");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchAudit();
    const interval = setInterval(fetchAudit, 30000);  // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const filteredEntries = entries.filter(e => {
    if (filter === "all") return true;
    return e.severity === filter;
  });

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <CardTitle className="flex items-center gap-2">
            <Shield className="h-5 w-5" />
            <span>سجل التدقيق الأمني</span>
            <span className="text-sm text-muted-foreground" dir="ltr">
              ({entries.length})
            </span>
          </CardTitle>
          <div className="flex items-center gap-2">
            <select
              value={filter}
              onChange={(e) => setFilter(e.target.value as any)}
              className="text-xs border rounded px-2 py-1 bg-background"
              aria-label="Filter by severity"
            >
              <option value="all">الكل</option>
              <option value="warning">تحذيرات</option>
              <option value="critical">حرجة</option>
            </select>
            <button
              onClick={fetchAudit}
              disabled={loading}
              className="text-xs px-2 py-1 bg-accent text-white rounded hover:opacity-90 disabled:opacity-50"
            >
              {loading ? "جاري التحميل..." : "تحديث"}
            </button>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {error && (
          <div role="alert" className="bg-destructive/10 text-destructive text-sm p-3 rounded-md mb-4">
            {error}
          </div>
        )}

        {!loading && filteredEntries.length === 0 && (
          <div className="text-center py-8 text-muted-foreground">
            <p className="text-sm">لا توجد سجلات</p>
          </div>
        )}

        <div className="space-y-2 max-h-[500px] overflow-y-auto" role="log" aria-live="polite">
          {filteredEntries.map((entry, i) => {
            const sev = entry.severity || "info";
            const Style = SEVERITY_STYLES[sev];
            const Icon = Style.icon;
            return (
              <div
                key={i}
                className="flex items-start gap-3 p-3 rounded border bg-card/50"
              >
                <Icon className={`h-4 w-4 mt-0.5 ${Style.className}`} aria-hidden="true" />
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="font-medium text-sm">
                      {entry.action || "unknown"}
                    </span>
                    <Badge variant={Style.variant} className="text-xs">
                      {Style.label}
                    </Badge>
                    {entry.user_id && (
                      <span className="text-xs text-muted-foreground" dir="ltr">
                        {entry.user_id}
                      </span>
                    )}
                  </div>
                  {entry.details && Object.keys(entry.details).length > 0 && (
                    <pre className="text-xs text-muted-foreground mt-1 overflow-x-auto" dir="ltr">
                      {JSON.stringify(entry.details, null, 2)}
                    </pre>
                  )}
                </div>
                {entry.timestamp && (
                  <time
                    dateTime={new Date(entry.timestamp * 1000).toISOString()}
                    className="text-xs text-muted-foreground whitespace-nowrap"
                  >
                    {new Date(entry.timestamp * 1000).toLocaleString("ar-EG")}
                  </time>
                )}
              </div>
            );
          })}
        </div>
      </CardContent>
    </Card>
  );
}
