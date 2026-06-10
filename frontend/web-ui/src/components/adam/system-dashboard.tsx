"use client";

import { useAppStore } from "@/lib/store";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  Cpu,
  MemoryStick,
  Activity,
  Brain,
  Database,
  Wifi,
  WifiOff,
  Zap,
  MessageSquare,
  Clock,
  Server,
  Layers,
} from "lucide-react";

function HealthCard({
  icon,
  label,
  value,
  status,
  color,
}: {
  icon: React.ElementType;
  label: string;
  value: string;
  status: "good" | "warn" | "bad";
  color: string;
}) {
  const Icon = icon;
  return (
    <Card className="glass border-border/50">
      <CardContent className="p-3 flex items-center gap-3">
        <div className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0" style={{ backgroundColor: `${color}20` }}>
          <Icon className="h-4 w-4" style={{ color }} />
        </div>
        <div className="flex-1 min-w-0">
          <p className="text-[10px] text-muted-foreground">{label}</p>
          <p className="text-sm font-medium truncate">{value}</p>
        </div>
        <div className={cn(
          "h-2 w-2 rounded-full shrink-0",
          status === "good" && "bg-emerald-400",
          status === "warn" && "bg-amber-400",
          status === "bad" && "bg-red-400",
        )} />
      </CardContent>
    </Card>
  );
}

export function SystemDashboard() {
  const { systemHealth, settings, apiConnected, ollamaConnected, ollamaModels } = useAppStore();
  const isArabic = settings.language === "ar";

  const t = isArabic ? {
    title: "لوحة النظام",
    engine: "المحرك",
    model: "الموديل",
    mode: "الوضع",
    cycles: "الدورات",
    messages: "الرسائل",
    uptime: "وقت التشغيل",
    system: "النظام",
    cpu: "المعالج",
    memory: "الذاكرة",
    services: "الخدمات",
    api: "API",
    ollama: "Ollama",
    qdrant: "Qdrant",
    models: "الموديلات",
    connected: "متصل",
    disconnected: "غير متصل",
    noData: "لا توجد بيانات",
  } : {
    title: "System Dashboard",
    engine: "Engine",
    model: "Model",
    mode: "Mode",
    cycles: "Cycles",
    messages: "Messages",
    uptime: "Uptime",
    system: "System",
    cpu: "CPU",
    memory: "Memory",
    services: "Services",
    api: "API",
    ollama: "Ollama",
    qdrant: "Qdrant",
    models: "Models",
    connected: "Connected",
    disconnected: "Disconnected",
    noData: "No data available",
  };

  return (
    <div className="p-4 space-y-4">
      <div className="flex items-center gap-2 mb-2">
        <Activity className="h-5 w-5 text-primary" />
        <h2 className="text-lg font-semibold">{t.title}</h2>
      </div>

      {/* Engine Stats */}
      <div>
        <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
          <Brain className="h-3.5 w-3.5" /> {t.engine}
        </h3>
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-2">
          <HealthCard
            icon={Server}
            label={t.model}
            value={systemHealth?.engine?.model || "—"}
            status="good"
            color="#8b5cf6"
          />
          <HealthCard
            icon={Layers}
            label={t.mode}
            value={systemHealth?.engine?.active_mode || "—"}
            status="good"
            color="#f59e0b"
          />
          <HealthCard
            icon={Zap}
            label={t.cycles}
            value={String(systemHealth?.engine?.cycle_count ?? "—")}
            status="good"
            color="#06b6d4"
          />
          <HealthCard
            icon={MessageSquare}
            label={t.messages}
            value={String(systemHealth?.engine?.conversation_length ?? "—")}
            status="good"
            color="#10b981"
          />
        </div>
      </div>

      {/* System Resources */}
      <div>
        <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
          <Cpu className="h-3.5 w-3.5" /> {t.system}
        </h3>
        <div className="grid grid-cols-2 gap-2">
          <HealthCard
            icon={Cpu}
            label={t.cpu}
            value={systemHealth?.system?.cpu_percent != null ? `${systemHealth.system.cpu_percent}%` : "—"}
            status={systemHealth?.system?.cpu_percent != null && systemHealth.system.cpu_percent > 80 ? "warn" : "good"}
            color="#3b82f6"
          />
          <HealthCard
            icon={MemoryStick}
            label={t.memory}
            value={systemHealth?.system?.memory_percent != null ? `${systemHealth.system.memory_percent}%` : "—"}
            status={systemHealth?.system?.memory_percent != null && systemHealth.system.memory_percent > 80 ? "warn" : "good"}
            color="#ec4899"
          />
        </div>
      </div>

      {/* Services */}
      <div>
        <h3 className="text-xs font-medium text-muted-foreground uppercase tracking-wider mb-2 flex items-center gap-1">
          <Server className="h-3.5 w-3.5" /> {t.services}
        </h3>
        <div className="grid grid-cols-3 gap-2">
          <HealthCard
            icon={apiConnected ? Wifi : WifiOff}
            label={t.api}
            value={apiConnected ? t.connected : t.disconnected}
            status={apiConnected ? "good" : "bad"}
            color={apiConnected ? "#10b981" : "#ef4444"}
          />
          <HealthCard
            icon={ollamaConnected ? Wifi : WifiOff}
            label={t.ollama}
            value={ollamaConnected ? `${ollamaModels.length} ${t.models}` : t.disconnected}
            status={ollamaConnected ? "good" : "bad"}
            color={ollamaConnected ? "#10b981" : "#ef4444"}
          />
          <HealthCard
            icon={systemHealth?.qdrant?.connected ? Wifi : WifiOff}
            label={t.qdrant}
            value={systemHealth?.qdrant?.connected ? t.connected : t.disconnected}
            status={systemHealth?.qdrant?.connected ? "good" : "bad"}
            color={systemHealth?.qdrant?.connected ? "#10b981" : "#ef4444"}
          />
        </div>
      </div>
    </div>
  );
}
