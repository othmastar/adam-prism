"use client";

import { useEffect } from "react";
import { ThemeProvider } from "@teispace/next-themes";
import { useAppStore, useInitializeStore, ViewType } from "@/lib/store";
import { useApiHealthCheck, useEngineStream } from "@/lib/api";
import { useIsMobile } from "@/hooks/use-mobile";
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
import { LTMMemoryPanel } from "@/components/adam/ltm-memory-panel";
import { BrowserPanel } from "@/components/adam/browser-panel";
import { MCPPanel } from "@/components/adam/mcp-panel";
import { ChannelsPanel } from "@/components/adam/channels-panel";
import { PredictiveMonitor } from "@/components/predictive/predictive-monitor";
import {
  Activity, MessageSquare, Database, Wrench, Settings,
  Cpu, BookOpen, Sparkles, Clock, Package, Bot, Brain, Wifi
} from "lucide-react";
import { cn } from "@/lib/utils";

type MobileNavItem = {
  view: ViewType;
  icon: React.ElementType;
  labelAr: string;
  labelEn: string;
};

const mobileNavItems: MobileNavItem[] = [
  { view: "chat", icon: MessageSquare, labelAr: "محادثة", labelEn: "Chat" },
  { view: "knowledge", icon: Database, labelAr: "المعرفة", labelEn: "Knowledge" },
  { view: "tools", icon: Wrench, labelAr: "أدوات", labelEn: "Tools" },
  { view: "monitor", icon: Activity, labelAr: "النظام", labelEn: "System" },
  { view: "settings", icon: Settings, labelAr: "الإعدادات", labelEn: "Settings" },
];

function MobileBottomNav() {
  const { activeView, setActiveView, settings, setSidebarOpen } = useAppStore();
  const isArabic = settings.language === "ar";

  return (
    <nav
      className="bottom-nav fixed bottom-0 left-0 right-0 z-50 glass border-t border-border flex items-center justify-around safe-area-bottom md:hidden"
      style={{ paddingBottom: "env(safe-area-inset-bottom, 0px)" }}
    >
      {mobileNavItems.map((item) => {
        const Icon = item.icon;
        const isActive = activeView === item.view;
        return (
          <button
            key={item.view}
            onClick={() => setActiveView(item.view)}
            className={cn(
              "flex flex-col items-center gap-0.5 py-1.5 px-3 rounded-lg transition-colors min-h-0",
              isActive
                ? "text-primary"
                : "text-muted-foreground hover:text-foreground"
            )}
          >
            <Icon className={cn("h-5 w-5", isActive && "bottom-nav-active")} />
            <span className="text-[10px] font-medium">{isArabic ? item.labelAr : item.labelEn}</span>
          </button>
        );
      })}
      {/* Menu button to open sidebar */}
      <button
        onClick={() => setSidebarOpen(true)}
        className="flex flex-col items-center gap-0.5 py-1.5 px-3 rounded-lg text-muted-foreground hover:text-foreground min-h-0"
      >
        <svg className="h-5 w-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <line x1="3" y1="6" x2="21" y2="6" />
          <line x1="3" y1="12" x2="21" y2="12" />
          <line x1="3" y1="18" x2="21" y2="18" />
        </svg>
        <span className="text-[10px] font-medium">قائمة</span>
      </button>
    </nav>
  );
}

function AppContent() {
  const { activeView, settings } = useAppStore();
  const isMobile = useIsMobile();

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

  const mainPadding = isMobile ? "pb-[72px]" : "pb-0";

  return (
    <div className="h-dvh flex bg-background overflow-hidden relative">
      {/* Particle background */}
      <div className="particle-field hide-on-mobile" aria-hidden="true">
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

      {/* Sidebar (slides in on mobile) */}
      <ChatSidebar />

      {/* Main content */}
      <main className={`flex-1 h-full flex flex-col min-w-0 relative z-10 ${mainPadding}`}>
        {activeView === "chat" && (
          <ChatInterface />
        )}
        {activeView === "monitor" && (
          <div className="flex-1 overflow-y-auto">
            <SystemDashboard />
          </div>
        )}
        {activeView === "pipeline" && (
          <div className="flex-1 overflow-y-auto p-4 pb-20">
            <div className="flex items-center gap-2 mb-4">
              <Activity className="h-5 w-5 text-primary" />
              <h2 className="text-lg font-semibold">
                {settings.language === "ar" ? "سير المعالجة" : "Processing Pipeline"}
              </h2>
            </div>
            <PipelineMonitor />
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
        {activeView === "ltm" && (
          <div className="flex-1 overflow-y-auto p-4">
            <LTMMemoryPanel />
          </div>
        )}
        {activeView === "browser" && (
          <div className="flex-1 overflow-y-auto p-4">
            <BrowserPanel />
          </div>
        )}
        {activeView === "mcp" && (
          <div className="flex-1 overflow-y-auto p-4">
            <MCPPanel />
          </div>
        )}
      </main>

      {/* Mobile bottom navigation */}
      <MobileBottomNav />

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
