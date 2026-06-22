"use client";

import { useAppStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { X, Terminal, CheckCircle2, RefreshCw, AlertTriangle, Loader2, Wrench } from "lucide-react";
import { useEffect, useRef, useState, useCallback } from "react";
import { getFastApiUrl } from "@/lib/api";

type DiagnosticCheck = {
  check: string;
  status: "pass" | "fail";
};

type DiagnosticResult = {
  status: string;
  timestamp: string;
  checks: DiagnosticCheck[];
  summary: { passed: number; failed: number; total: number };
};

const t = (isArabic: boolean, ar: string, en: string) => isArabic ? ar : en;

export function IssueTerminal() {
  const { diagnosticsOpen, setDiagnosticsOpen, settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const [result, setResult] = useState<DiagnosticResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [healing, setHealing] = useState(false);
  const [logs, setLogs] = useState<string[]>([]);
  const terminalRef = useRef<HTMLDivElement>(null);

  const fetchDiagnostics = useCallback(async () => {
    setLoading(true);
    setLogs([]);
    setResult(null);

    const baseLog = [
      t(isArabic,
        "> adam.diagnostics() — تشخيص ذاتي للنظام",
        "> adam.diagnostics() — system self-diagnosis"),
      "  ╔══════════════════════════════════════╗",
      "  ║  ADAM PRISM — AUTO-DIAGNOSTIC v2.0  ║",
      "  ╚══════════════════════════════════════╝",
      "",
    ];
    setLogs(baseLog);

    try {
      const url = getFastApiUrl();
      const res = await fetch(`${url}/api/engine/diagnostics`);
      const data: DiagnosticResult = await res.json();

      const checkLines: string[] = [];
      for (const check of data.checks) {
        const icon = check.status === "pass" ? "[OK]" : "[FAIL]";
        const color = check.status === "pass" ? "✅" : "❌";
        checkLines.push(`${icon}    ${check.check} — ${color}`);
      }

      for (let i = 0; i < checkLines.length; i++) {
        await new Promise((r) => setTimeout(r, 300));
        setLogs((prev) => [...prev, checkLines[i]]);
      }

      await new Promise((r) => setTimeout(r, 400));
      const statusMsg = data.status === "healthy"
        ? t(isArabic, "✅ النظام سليم", "✅ System healthy")
        : t(isArabic, "⚠️ هناك مشاكل", "⚠️ Issues detected");
      setLogs((prev) => [
        ...prev,
        "",
        `[DONE]  ${data.summary.passed}/${data.summary.total} ${t(isArabic, "نجح", "passed")}, ${data.summary.failed} ${t(isArabic, "فشل", "failed")} — ${statusMsg}`,
        "",
        data.status === "healthy"
          ? `> ${t(isArabic, "لا توجد مشكلات حرجة", "No critical issues.")}`
          : `> ${data.summary.failed} ${t(isArabic, "مشكلة تم اكتشافها", "issue(s) detected.")}`,
      ]);

      setResult(data);
    } catch {
      setLogs((prev) => [
        ...prev,
        "",
        `[FAIL]  ${t(isArabic, "تعذر الاتصال بخادم التشخيص", "Connection to diagnostic server failed")}`,
        "",
        `> ${t(isArabic, "تحقق من تشغيل الخادم", "Check if server is running.")}`,
      ]);
    } finally {
      setLoading(false);
    }
  }, [isArabic]);

  const runHealing = useCallback(async () => {
    if (healing) return;
    setHealing(true);
    setLogs((prev) => [...prev, "", `> ${t(isArabic, "بدء التصليح الذاتي...", "Starting self-healing...")}`]);

    try {
      const url = getFastApiUrl();
      const res = await fetch(`${url}/api/engine/heal`, { method: "POST" });
      const data = await res.json();

      const actions = data.actions_taken || [];
      for (const action of actions) {
        await new Promise((r) => setTimeout(r, 400));
        setLogs((prev) => [...prev, `  [FIX]  ${action}`]);
      }

      await new Promise((r) => setTimeout(r, 300));
      setLogs((prev) => [
        ...prev,
        "",
        data.status === "healed"
          ? `[DONE]  ${actions.length} ${t(isArabic, "إجراء تم بنجاح", "action(s) completed successfully")}`
          : `[DONE]  ${t(isArabic, "لا توجد إجراءات مطلوبة", "No actions required")}`,
      ]);

      await new Promise((r) => setTimeout(r, 500));
      setResult(null);
      fetchDiagnostics();
    } catch (err) {
      setLogs((prev) => [...prev, "", `[FAIL]  ${t(isArabic, "فشل التصليح:", "Healing failed:")} ${err}`]);
    } finally {
      setHealing(false);
    }
  }, [fetchDiagnostics, healing, isArabic]);

  useEffect(() => {
    if (diagnosticsOpen && !result && !loading) {
      fetchDiagnostics();
    }
  }, [diagnosticsOpen, result, loading, fetchDiagnostics]);

  useEffect(() => {
    if (terminalRef.current) {
      terminalRef.current.scrollTop = terminalRef.current.scrollHeight;
    }
  }, [logs]);

  if (!diagnosticsOpen) return null;

  const isHealthy = result?.status === "healthy";
  const failedCount = result?.summary.failed ?? 0;

  return (
    <div className={cn("fixed inset-0 z-[80] flex items-center backdrop-blur-sm", isArabic ? "justify-start" : "justify-center")}
      style={{ backgroundColor: 'rgba(0,0,0,0.7)' }}
      onClick={() => setDiagnosticsOpen(false)}>
      <div className="w-full max-w-2xl mx-4" onClick={(e) => e.stopPropagation()}>
        {/* Terminal header */}
        <div className="flex items-center justify-between px-4 py-2.5 bg-zinc-900 border border-zinc-700 rounded-t-xl">
          <div className="flex items-center gap-2">
            <div className="flex gap-1.5">
              <div className="h-3 w-3 rounded-full bg-red-500" />
              <div className="h-3 w-3 rounded-full bg-yellow-500" />
              <div className="h-3 w-3 rounded-full bg-emerald-500" />
            </div>
            <span className="text-[11px] text-zinc-400 font-mono ms-2">{t(isArabic, "آدم@تشخيص", "adam@diagnostics")} — {t(isArabic, "فوري", "real-time")}</span>
          </div>
          <div className="flex items-center gap-2">
            {!loading && result && result.summary.failed > 0 && (
              <Button variant="ghost" size="sm" className="h-6 text-[10px] text-amber-400 hover:text-amber-300 gap-1"
                onClick={runHealing} disabled={healing}>
                <Wrench className="h-3 w-3" />
                {t(isArabic, "إصلاح", "Repair")}
              </Button>
            )}
            {!loading && (
              <Button variant="ghost" size="sm" className="h-6 text-[10px] text-zinc-400 hover:text-white gap-1"
                onClick={fetchDiagnostics}>
                <RefreshCw className="h-3 w-3" />
                {t(isArabic, "إعادة", "Refresh")}
              </Button>
            )}
            <Button variant="ghost" size="icon" className="h-6 w-6 text-zinc-400 hover:text-white"
              onClick={() => setDiagnosticsOpen(false)}>
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Terminal body */}
        <div ref={terminalRef} className="border-x border-b border-zinc-700 rounded-b-xl p-4 max-h-[60vh] overflow-y-auto font-mono text-xs space-y-0.5" style={{ backgroundColor: 'rgba(0,0,0,0.95)' }}>
          {logs.map((line, i) => {
            if (!line) return <div key={i} className="h-2" />;
            let color = "text-zinc-300";
            let prefix = "";
            if (line.startsWith("[OK]")) { color = "text-emerald-400"; prefix = "✅ "; }
            else if (line.startsWith("[FAIL]")) { color = "text-red-400"; prefix = "❌ "; }
            else if (line.startsWith("[FIX]")) { color = "text-amber-400"; prefix = "🔧 "; }
            else if (line.startsWith("[DONE]")) { color = "text-emerald-400"; prefix = "🎯 "; }
            else if (line.startsWith(">")) { color = "text-purple-400"; prefix = ""; }
            else if (line.startsWith("  ╔") || line.startsWith("  ╚") || line.startsWith("  ║")) { color = "text-zinc-500"; }
            return (
              <div key={i} className={cn("leading-5", color)}>
                {prefix}{line}
              </div>
            );
          })}

          {loading && (
            <div className="flex items-center gap-2 text-zinc-500 mt-2">
              <Loader2 className="h-3 w-3 animate-spin" />
              <span className="animate-pulse">{t(isArabic, "جاري التشخيص...", "Running diagnostics...")}</span>
            </div>
          )}
          {healing && (
            <div className="flex items-center gap-2 text-amber-500 mt-2">
              <Wrench className="h-3 w-3 animate-bounce" />
              <span className="animate-pulse">{t(isArabic, "جاري التصليح الذاتي...", "Self-healing in progress...")}</span>
            </div>
          )}

          {!loading && result && (
            <div className={cn(
              "flex items-center gap-2 mt-3 pt-2 border-t border-zinc-800",
              isHealthy ? "text-emerald-400" : "text-red-400"
            )}>
              {isHealthy ? (
                <CheckCircle2 className="h-4 w-4" />
              ) : (
                <AlertTriangle className="h-4 w-4" />
              )}
              <span className="text-xs font-medium">
                {isHealthy
                  ? t(isArabic, "Self-healing complete — النظام سليم", "Self-healing complete — system healthy")
                  : `${failedCount} ${t(isArabic, "مشكلة تم اكتشافها", "issue(s) detected")}`}
              </span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
