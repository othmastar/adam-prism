"use client";

import { useEffect } from "react";
import { ThemeProvider } from "@teispace/next-themes";
import { useAppStore, useInitializeStore } from "@/lib/store";
import { useApiHealthCheck, useEngineStream } from "@/lib/api";
import { ChatSidebar } from "@/components/adam/chat-sidebar";
import { ChatInterface } from "@/components/adam/chat-interface";
import { KnowledgePanel } from "@/components/adam/knowledge-panel";
import { NotebookPanel } from "@/components/adam/notebook-panel";
import { ToolsPanel } from "@/components/adam/tools-panel";
import { SkillsPanel } from "@/components/adam/skills-panel";
import { SettingsPanel } from "@/components/adam/settings-panel";
import { PipelineMonitor } from "@/components/adam/pipeline-monitor";
import { SystemDashboard } from "@/components/adam/system-dashboard";
import { FloatingMonitor } from "@/components/adam/floating-monitor";
import { IssueTerminal } from "@/components/adam/issue-terminal";
import { ModelOrchestrator } from "@/components/adam/model-orchestrator";
import { ShieldPulse } from "@/components/adam/shield-pulse";
import { ActionTrace } from "@/components/adam/action-trace";
import { SchedulerDashboard } from "@/components/adam/scheduler-dashboard";
import { PluginManager } from "@/components/adam/plugin-manager";
import { SubagentDashboard } from "@/components/adam/subagent-dashboard";
import { MemoryPanel } from "@/components/adam/memory-panel";
import { ChannelsPanel } from "@/components/adam/channels-panel";
import { PredictiveMonitor } from "@/components/predictive/predictive-monitor";
import { Activity } from "lucide-react";

function AppContent() {
  const { activeView, settings } = useAppStore();

  // Initialize store from localStorage
  useInitializeStore();

  // Periodic API health check
  useApiHealthCheck();

  // Real-time engine pipeline stream
  useEngineStream();

  // Set RTL/LTR based on language
  useEffect(() => {
    const dir = settings.language === "ar" ? "rtl" : "ltr";
    const lang = settings.language === "ar" ? "ar" : "en";
    document.documentElement.dir = dir;
    document.documentElement.lang = lang;
  }, [settings.language]);

  return (
    <div className="h-screen flex bg-background overflow-hidden relative">
      {/* Particle background — قيم ثابتة لتجنب hydration error */}
      <div className="particle-field" aria-hidden="true">
        {Array.from({ length: 30 }).map((_, i) => {
          const seed = (i * 7 + 13) % 100;
          return (
            <div
              key={i}
              className="particle"
              style={{
                left: `${(seed * 3.7) % 100}%`,
                bottom: `${(seed * 1.3) % 20}%`,
                width: `${2 + (seed % 4)}px`,
                height: `${2 + ((seed + 3) % 4)}px`,
                animationDuration: `${15 + (seed % 25)}s`,
                animationDelay: `${(seed * 2.1) % 20}s`,
                opacity: 0.3 + ((seed % 10) / 25),
              }}
            />
          );
        })}
      </div>

      {/* Floating system monitor */}
      <FloatingMonitor />

      {/* ModelOrchestrator — modal overlay */}
      <ModelOrchestrator />

      {/* ActionTrace — terminal line overlay */}
      <ActionTrace />

      {/* Sidebar */}
      <ChatSidebar />

      {/* Main content */}
      <main className="flex-1 h-full flex flex-col min-w-0 relative z-10">
        {activeView === "chat" && (
          <ChatInterface />
        )}
        {activeView === "monitor" && (
          <div className="flex-1 overflow-y-auto">
            <SystemDashboard />
          </div>
        )}
        {activeView === "pipeline" && (
          <div className="flex-1 overflow-y-auto p-4">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">
                {settings.language === "ar" ? "سير المعالجة" : "Processing Pipeline"}
              </h2>
            </div>
            <PipelineMonitor />
            {/* [PHASE4] Predictive monitoring (CruxSight.ai integration) */}
            <div className="mt-4">
              <PredictiveMonitor />
            </div>
          </div>
        )}
        {activeView === "knowledge" && <KnowledgePanel />}
        {activeView === "notebook" && <NotebookPanel />}
        {activeView === "tools" && <ToolsPanel />}
        {activeView === "skills" && <SkillsPanel />}
        {activeView === "settings" && <SettingsPanel />}
        {activeView === "scheduler" && <SchedulerDashboard />}
        {activeView === "plugins" && <PluginManager />}
        {activeView === "subagents" && <SubagentDashboard />}
        {activeView === "channels" && <ChannelsPanel />}
        {activeView === "memory" && <MemoryPanel />}
      </main>

      {/* IssueTerminal — modal overlay (renders last for highest z-index) */}
      <IssueTerminal />
    </div>
  );
}

function ThemedApp() {
  return <AppContent />;
}

export default function Home() {
  return (
    <ThemeProvider attribute="class" defaultTheme="dark" enableSystem={false}>
      <ThemedApp />
    </ThemeProvider>
  );
}
