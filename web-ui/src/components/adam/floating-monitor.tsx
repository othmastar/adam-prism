"use client";

import { useAppStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import {
  Cpu,
  MemoryStick,
  Activity,
  Brain,
  Wifi,
  WifiOff,
  X,
  GripHorizontal,
  Eye,
  EyeOff,
  AlertTriangle,
  Globe,
  CloudOff,
} from "lucide-react";
import { useState, useEffect, useRef, useCallback } from "react";

function ResourceBar({ label, value, color, icon }: { label: string; value: number; color: string; icon: React.ElementType }) {
  const Icon = icon;
  const status = value > 80 ? "warn" : value > 50 ? "mid" : "good";
  const pulseDuration = value > 80 ? "0.8s" : value > 50 ? "1.4s" : "2.5s";
  return (
    <div className="flex items-center gap-2">
      <div className="h-6 w-6 rounded-md flex items-center justify-center shrink-0 relative" style={{ backgroundColor: `${color}20` }}>
        <Icon className="h-3 w-3" style={{ color }} />
        <span
          className="absolute inset-0 rounded-md opacity-30"
          style={{
            backgroundColor: color,
            animation: `pulse-ring ${pulseDuration} ease-in-out infinite`,
          }}
        />
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center justify-between">
          <span className="text-[9px] text-muted-foreground">{label}</span>
          <span className="text-[10px] font-mono font-bold" style={{ color }}>{value}%</span>
        </div>
        <div className="h-1.5 rounded-full bg-muted/50 mt-0.5 overflow-hidden">
          <div
            className={cn(
              "h-full rounded-full transition-all duration-1000 ease-out",
              status === "good" && "bg-emerald-400",
              status === "mid" && "bg-amber-400",
              status === "warn" && "bg-red-400",
            )}
            style={{
              width: `${value}%`,
              animation: `pulse-ring ${pulseDuration} ease-in-out infinite`,
            }}
          />
        </div>
      </div>
    </div>
  );
}

export function FloatingMonitor() {
  const {
    systemHealth,
    settings,
    apiConnected,
    ollamaConnected,
    processingSteps,
    isStreaming,
    activeMode,
    monitorVisible,
    setMonitorVisible,
    gpuPercent,
    issueCount,
    setDiagnosticsOpen,
  } = useAppStore();

  const isArabic = settings.language === "ar";
  const [position, setPosition] = useState({ x: 16, y: 80 });
  const [isDragging, setIsDragging] = useState(false);
  const [dragOffset, setDragOffset] = useState({ x: 0, y: 0 });
  const monitorRef = useRef<HTMLDivElement>(null);
  const [currentActivity, setCurrentActivity] = useState("");
  const [internetOnline, setInternetOnline] = useState(true);

  // Track current activity from processing steps
  useEffect(() => {
    const running = processingSteps.filter((s) => s.status === "running").pop();
    if (running) {
      setCurrentActivity(isArabic ? running.step : running.step);
    } else if (isStreaming) {
      setCurrentActivity(isArabic ? "التفكير..." : "Thinking...");
    } else {
      setCurrentActivity(isArabic ? "بانتظار..." : "Idle...");
    }
  }, [processingSteps, isStreaming, isArabic]);

  // Simulate GPU usage from Ollama activity
  useEffect(() => {
    const interval = setInterval(() => {
      const store = useAppStore.getState();
      const base = store.ollamaConnected ? 15 + Math.random() * 30 : 2;
      const activity = store.isStreaming ? 60 + Math.random() * 35 : base;
      store.setGpuPercent(Math.round(activity));
    }, 2000);
    return () => clearInterval(interval);
  }, []);

  // Check actual internet connectivity
  useEffect(() => {
    const check = async () => {
      try {
        const res = await fetch("https://1.1.1.1", { mode: "no-cors", signal: AbortSignal.timeout(3000) });
        setInternetOnline(true);
      } catch {
        setInternetOnline(false);
      }
    };
    check();
    const interval = setInterval(check, 30000);
    return () => clearInterval(interval);
  }, []);

  const handleMouseDown = useCallback((e: React.MouseEvent) => {
    if (monitorRef.current) {
      const rect = monitorRef.current.getBoundingClientRect();
      setDragOffset({ x: e.clientX - rect.left, y: e.clientY - rect.top });
      setIsDragging(true);
    }
  }, []);

  useEffect(() => {
    if (!isDragging) return;
    const handleMouseMove = (e: MouseEvent) => {
      setPosition({
        x: Math.max(0, Math.min(window.innerWidth - 220, e.clientX - dragOffset.x)),
        y: Math.max(0, Math.min(window.innerHeight - 300, e.clientY - dragOffset.y)),
      });
    };
    const handleMouseUp = () => setIsDragging(false);
    window.addEventListener("mousemove", handleMouseMove);
    window.addEventListener("mouseup", handleMouseUp);
    return () => {
      window.removeEventListener("mousemove", handleMouseMove);
      window.removeEventListener("mouseup", handleMouseUp);
    };
  }, [isDragging, dragOffset]);

  if (!monitorVisible) {
    return (
      <Button
        variant="outline"
        size="sm"
        className="fixed bottom-4 left-4 z-50 glass cosmic-border h-8 w-8 rounded-full p-0"
        onClick={() => setMonitorVisible(true)}
      >
        <Activity className="h-4 w-4 text-primary" />
      </Button>
    );
  }

  const cpuPercent = systemHealth?.system?.cpu_percent ?? 0;
  const memPercent = systemHealth?.system?.memory_percent ?? 0;

  return (
    <div
      ref={monitorRef}
      className="fixed z-50 floating-monitor"
      style={{ left: position.x, top: position.y, width: 200 }}
    >
      <div className="glass rounded-xl border border-primary/20 cosmic-border overflow-hidden">
        {/* Header */}
        <div
          className="flex items-center justify-between px-3 py-2 bg-primary/10 cursor-grab active:cursor-grabbing select-none"
          onMouseDown={handleMouseDown}
        >
          <div className="flex items-center gap-1.5">
            <div className="relative flex h-2 w-2">
              {isStreaming && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
              )}
              <span className={cn(
                "relative inline-flex rounded-full h-2 w-2",
                isStreaming ? "bg-cyan-400" : "bg-emerald-400"
              )} />
            </div>
            <span className="text-[10px] font-medium text-muted-foreground">
              {isArabic ? "مراقب آدم" : "Adam Monitor"}
            </span>
          </div>
          <div className="flex items-center gap-0.5">
            <div className="relative">
              <Button
                variant="ghost"
                size="icon"
                className="h-5 w-5 text-muted-foreground hover:text-amber-400"
                onClick={() => setDiagnosticsOpen(true)}
              >
                <AlertTriangle className="h-3 w-3" />
              </Button>
              {issueCount > 0 && (
                <span className="absolute -top-0.5 -end-0.5 h-2.5 w-2.5 rounded-full bg-amber-400 text-[6px] font-bold text-black flex items-center justify-center">
                  {issueCount}
                </span>
              )}
            </div>
            <Button
              variant="ghost"
              size="icon"
              className="h-5 w-5 text-muted-foreground hover:text-primary"
              onClick={() => setMonitorVisible(false)}
            >
              <EyeOff className="h-3 w-3" />
            </Button>
          </div>
        </div>

        {/* Activity indicator */}
        <div className="px-3 py-1.5 border-t border-border/50">
          <div className="flex items-center gap-1.5">
            <Brain className={cn(
              "h-3 w-3",
              isStreaming ? "text-cyan-400 animate-pulse" : "text-muted-foreground"
            )} />
            <span className="text-[9px] text-muted-foreground truncate flex-1">{currentActivity}</span>
            <Badge
              variant="outline"
              className="text-[8px] px-1 py-0 h-4 border-primary/20"
              style={{ color: `var(--mode-color, #8b5cf6)` }}
            >
              {activeMode}
            </Badge>
          </div>
          {/* Activity bar */}
          <div className="h-0.5 rounded-full bg-muted/30 mt-1 overflow-hidden">
            <div className={cn(
              "h-full rounded-full activity-bar",
              isStreaming ? "bg-gradient-to-r from-purple-500 via-cyan-400 to-blue-500" : "bg-muted-foreground/30"
            )} />
          </div>
        </div>

        {/* Resources */}
        <div className="px-3 py-2 space-y-2 border-t border-border/50">
          <ResourceBar label={isArabic ? "المعالج" : "CPU"} value={cpuPercent} color="#3b82f6" icon={Cpu} />
          <ResourceBar label={isArabic ? "الذاكرة" : "RAM"} value={memPercent} color="#ec4899" icon={MemoryStick} />
          <ResourceBar label={isArabic ? "GPU" : "GPU"} value={gpuPercent} color="#8b5cf6" icon={Cpu} />
          {/* Internet status */}
          <div className="flex items-center gap-2 pt-0.5">
            <div className="h-6 w-6 rounded-md flex items-center justify-center shrink-0 relative" style={{ backgroundColor: internetOnline ? 'rgba(16,185,129,0.2)' : 'rgba(239,68,68,0.2)' }}>
              {internetOnline ? <Globe className="h-3 w-3 text-emerald-400" /> : <CloudOff className="h-3 w-3 text-red-400" />}
              {internetOnline && <span className="absolute -top-0.5 -end-0.5 h-1.5 w-1.5 rounded-full bg-emerald-400 animate-ping" />}
            </div>
            <div className="flex-1 min-w-0">
              <div className="flex items-center justify-between">
                <span className="text-[9px] text-muted-foreground">{isArabic ? "الإنترنت" : "Internet"}</span>
                <span className={cn("text-[10px] font-mono font-bold", internetOnline ? "text-emerald-400" : "text-red-400")}>
                  {internetOnline ? (isArabic ? "متصل" : "Online") : (isArabic ? "منقطع" : "Offline")}
                </span>
              </div>
              <div className="h-1.5 rounded-full bg-muted/50 mt-0.5 overflow-hidden">
                <div className={cn(
                  "h-full rounded-full transition-all duration-1000",
                  internetOnline ? "bg-emerald-400" : "bg-red-400"
                )} style={{ width: internetOnline ? "100%" : "25%" }} />
              </div>
            </div>
          </div>
        </div>

        {/* Services status */}
        <div className="px-3 py-1.5 border-t border-border/50 flex items-center justify-between">
          <div className="flex items-center gap-1.5">
            <div className={cn(
              "h-1.5 w-1.5 rounded-full",
              apiConnected ? "bg-emerald-400 pulse-ring" : "bg-destructive"
            )} />
            <span className="text-[8px] text-muted-foreground">API</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className={cn(
              "h-1.5 w-1.5 rounded-full",
              ollamaConnected ? "bg-emerald-400 pulse-ring" : "bg-destructive"
            )} />
            <span className="text-[8px] text-muted-foreground">Ollama</span>
          </div>
          <div className="flex items-center gap-1.5">
            <div className={cn(
              "h-1.5 w-1.5 rounded-full",
              systemHealth?.qdrant?.connected ? "bg-emerald-400 pulse-ring" : "bg-destructive"
            )} />
            <span className="text-[8px] text-muted-foreground">Qdrant</span>
          </div>
        </div>
      </div>
    </div>
  );
}
