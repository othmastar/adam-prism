"use client";

import { useAppStore } from "@/lib/store";
import { deleteSessionOnServer, sendChatMessage } from "@/lib/api";
import { AdamLogoFull } from "./adam-logo";
import { Button } from "@/components/ui/button";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from "@/components/ui/separator";
import { Badge } from "@/components/ui/badge";
import { useToast } from "@/hooks/use-toast";
import {
  MessageSquarePlus,
  Settings,
  Trash2,
  FileText,
  X,
  MessageSquare,
  Sparkles,
  Moon,
  Sun,
  BookOpen,
  Brain,
  Wrench,
  Database,
  Wifi,
  WifiOff,
  Activity,
  Cpu,
  ChevronDown,
  ChevronUp,
  History,
  GitBranch,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@teispace/next-themes";
import { ViewType } from "@/lib/store";

const navItems: {
  view: ViewType | "orchestrator";
  icon: React.ElementType;
  labelAr: string;
  labelEn: string;
  descAr: string;
  descEn: string;
}[] = [
  { view: "chat", icon: MessageSquare, labelAr: "محادثة", labelEn: "Chat", descAr: "التواصل المباشر مع آدم", descEn: "Chat with Adam" },
  { view: "monitor", icon: Activity, labelAr: "حالة النظام", labelEn: "Monitor", descAr: "مؤشرات الأداء والصحة", descEn: "System health & performance" },
  { view: "pipeline", icon: Cpu, labelAr: "المعالجة", labelEn: "Pipeline", descAr: "سير خطوات المعالجة", descEn: "Processing pipeline steps" },
  { view: "knowledge", icon: Database, labelAr: "المعرفة", labelEn: "Knowledge", descAr: "قاعدة المعرفة والبحث", descEn: "Knowledge base & search" },
  { view: "notebook", icon: BookOpen, labelAr: "الدفتر", labelEn: "Notebook", descAr: "الملاحظات اليومية", descEn: "Daily notes & ideas" },
  { view: "tools", icon: Wrench, labelAr: "الأدوات", labelEn: "Tools", descAr: "كل أداة ووظيفتها", descEn: "Every tool & its function" },
  { view: "orchestrator", icon: GitBranch, labelAr: "المايسترو", labelEn: "Orchestrator", descAr: "توزيع المهام على الموديلات", descEn: "Multi-model task orchestration" },
  { view: "settings", icon: Settings, labelAr: "الإعدادات", labelEn: "Settings", descAr: "ضبط الموديل واللغة", descEn: "Model & language config" },
];

export function ChatSidebar() {
  const {
    conversations,
    activeConversationId,
    setActiveConversationId,
    addConversation,
    deleteConversation,
    activeView,
    setActiveView,
    sidebarOpen,
    setSidebarOpen,
    settings,
    apiConnected,
    historyPanelOpen,
    setHistoryPanelOpen,
    setOrchestratorOpen,
    syncedSessionIds,
  } = useAppStore();

  const { theme, setTheme } = useTheme();
  const { toast } = useToast();
  const isArabic = settings.language === "ar";
  const isDark = theme === "dark";

  const handleNewChat = () => {
    setActiveConversationId(null);
    setActiveView("chat");
    setSidebarOpen(false);
  };

  const handleSelectConversation = (id: string) => {
    setActiveConversationId(id);
    setActiveView("chat");
    setSidebarOpen(false);
  };

  const handleDeleteConversation = (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    deleteConversation(id);
    if (apiConnected) {
      deleteSessionOnServer(id).catch(() => {});
    }
  };

  const handleSummarizeConversation = async (id: string, e: React.MouseEvent) => {
    e.stopPropagation();
    const conv = conversations.find((c) => c.id === id);
    if (!conv || conv.messages.length === 0) return;

    const text = conv.messages
      .map((m) => `${m.role === "user" ? "س:" : "آدم:"} ${m.content}`)
      .join("\n\n");

    toast({ title: isArabic ? "جاري التلخيص..." : "Summarizing...", duration: 2000 });

    try {
      const result = await sendChatMessage(
        isArabic
          ? `لخص هذه المحادثة بالعربية في 3-5 نقاط:\n\n${text}`
          : `Summarize this conversation in English in 3-5 bullet points:\n\n${text}`,
        { history: [] }
      );
      toast({
        title: isArabic ? "ملخص المحادثة" : "Conversation Summary",
        description: result.response,
        duration: 8000,
      });
    } catch {
      toast({
        title: isArabic ? "فشل التلخيص" : "Summarization failed",
        variant: "destructive",
        duration: 3000,
      });
    }
  };

  const t = isArabic ? translations.ar : translations.en;

  return (
    <>
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div
          className="fixed inset-0 z-40 backdrop-blur-sm md:hidden"
          style={{ backgroundColor: 'rgba(0,0,0,0.6)' }}
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside
        className={cn(
          "fixed top-0 end-0 z-50 h-full w-72 glass flex flex-col transition-transform duration-300 ease-in-out md:relative md:translate-x-0",
          sidebarOpen ? "translate-x-0" : "translate-x-full md:translate-x-0"
        )}
      >
        {/* Header */}
        <div className="p-4 flex items-center justify-between">
          <AdamLogoFull animate={true} />
          <div className="flex items-center gap-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8 text-muted-foreground hover:text-primary"
              onClick={() => setTheme(isDark ? "light" : "dark")}
            >
              {isDark ? (
                <Sun className="h-4 w-4" />
              ) : (
                <Moon className="h-4 w-4" />
              )}
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="md:hidden h-8 w-8 text-muted-foreground hover:text-primary"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="h-4 w-4" />
            </Button>
          </div>
        </div>

        <Separator className="bg-border" />

        {/* API Connection Status */}
        <div className="px-3 py-2">
          <div className={cn(
            "flex items-center gap-2 px-3 py-2 rounded-lg text-xs",
            apiConnected
              ? "bg-emerald-500/10 text-emerald-400"
              : "bg-destructive/10 text-destructive"
          )}>
            {apiConnected ? (
              <Wifi className="h-3.5 w-3.5" />
            ) : (
              <WifiOff className="h-3.5 w-3.5" />
            )}
            <span className="flex-1">
              {apiConnected ? t.apiConnected : t.apiDisconnected}
            </span>
            <div className={cn(
              "h-1.5 w-1.5 rounded-full",
              apiConnected ? "bg-emerald-400 pulse-ring" : "bg-destructive"
            )} />
          </div>
        </div>

        {/* New Chat Button */}
        <div className="px-3 pb-2">
          <Button
            onClick={handleNewChat}
            className="w-full bg-primary/10 text-primary hover:bg-primary/20 border border-primary/30 justify-start gap-2"
            variant="outline"
          >
            <MessageSquarePlus className="h-4 w-4" />
            {t.newChat}
          </Button>
        </div>

        {/* Navigation — قائمة رأسية بأيقونة واسم ووصف */}
        <div className="px-2 pb-2 space-y-0.5">
          {navItems.map((item) => {
            const Icon = item.icon;
            const isActive = activeView === item.view;
            const label = isArabic ? item.labelAr : item.labelEn;
            const desc = isArabic ? item.descAr : item.descEn;
            return (
              <div
                key={item.view}
                role="button"
                tabIndex={0}
                onClick={() => {
                  if (item.view === "orchestrator") {
                    setOrchestratorOpen(true);
                  } else {
                    setActiveView(item.view as ViewType);
                  }
                  setSidebarOpen(false);
                }}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault();
                    if (item.view === "orchestrator") {
                      setOrchestratorOpen(true);
                    } else {
                      setActiveView(item.view as ViewType);
                    }
                    setSidebarOpen(false);
                  }
                }}
                className={cn(
                  "w-full group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors cursor-pointer",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted/30 hover:text-foreground"
                )}
              >
                <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center shrink-0", isActive ? "bg-primary/15" : "bg-muted/20")}>
                  <Icon className={cn("h-4 w-4", isActive && "text-primary")} />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="text-xs font-medium truncate">{label}</p>
                  <p className="text-[10px] text-muted-foreground/60 truncate">{desc}</p>
                </div>
                {isActive && <div className="h-1.5 w-1.5 rounded-full bg-primary shrink-0" />}
              </div>
            );
          })}
        </div>

        <Separator className="bg-border shrink-0" />

        {/* Conversations section — scrollable */}
        <div className="flex flex-col flex-1 min-h-0">
          <div className="px-3 pt-3 pb-1 shrink-0">
            <button
              onClick={() => setHistoryPanelOpen(!historyPanelOpen)}
              className="w-full flex items-center justify-between group cursor-pointer"
            >
              <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
                <History className="h-3 w-3" />
                {t.conversations}
              </span>
              <div className="flex items-center gap-1">
                <span className="text-[9px] text-muted-foreground/50">
                  {conversations.length}
                </span>
                {historyPanelOpen ? (
                  <ChevronDown className="h-3 w-3 text-muted-foreground/50 group-hover:text-muted-foreground transition-colors" />
                ) : (
                  <ChevronUp className="h-3 w-3 text-muted-foreground/50 group-hover:text-muted-foreground transition-colors" />
                )}
              </div>
            </button>
          </div>

          <div className={cn("flex-1 overflow-y-auto px-2 min-h-0", historyPanelOpen ? "block" : "hidden")} style={{ scrollbarWidth: "thin", scrollbarColor: "hsl(var(--border)) transparent" }}>
            <div className="space-y-1 pb-4">
              {conversations.length === 0 ? (
                <div className="px-3 py-8 text-center">
                  <Brain className="h-8 w-8 mx-auto text-primary/30 mb-2" />
                  <p className="text-xs text-muted-foreground">{t.noConversations}</p>
                </div>
              ) : (
                conversations.map((conv) => {
                  const isSynced = syncedSessionIds.includes(conv.id);
                  return (
                  <div
                    key={conv.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => handleSelectConversation(conv.id)}
                    onKeyDown={(e) => {
                      if (e.key === "Enter" || e.key === " ") {
                        e.preventDefault();
                        handleSelectConversation(conv.id);
                      }
                    }}
                    className={cn(
                      "w-full group flex items-center gap-2 px-3 py-2.5 rounded-lg text-sm transition-all duration-700 cursor-pointer",
                      activeConversationId === conv.id
                        ? "bg-primary/10 text-primary"
                        : isSynced
                          ? "text-muted-foreground hover:bg-muted hover:text-foreground"
                          : "text-muted-foreground/40 hover:text-muted-foreground/70 hover:bg-muted/20"
                    )}
                    style={!isSynced && activeConversationId !== conv.id ? {
                      filter: "saturate(0.3) brightness(0.7)",
                      transition: "filter 0.5s ease, all 0.3s ease",
                    } : undefined}
                  >
                    <MessageSquare className="h-4 w-4 shrink-0" />
                    <span className="flex-1 truncate text-xs">{conv.title}</span>
                    <div className="flex items-center gap-0.5 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity">
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-muted-foreground hover:text-cyan-400"
                        onClick={(e) => handleSummarizeConversation(conv.id, e)}
                        title={t.summarize}
                      >
                        <FileText className="h-3 w-3" />
                      </Button>
                      <Button
                        variant="ghost"
                        size="icon"
                        className="h-6 w-6 text-muted-foreground hover:text-destructive"
                        onClick={(e) => handleDeleteConversation(conv.id, e)}
                        title={t.delete}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  );
                })
              )}
            </div>
          </div>
        </div>

        {/* Footer */}
        <div className="p-3 border-t border-border">
          <div className="flex items-center gap-2 px-2">
            <div className="h-8 w-8 rounded-full bg-primary/20 flex items-center justify-center">
              <Sparkles className="h-4 w-4 text-primary" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-xs font-medium truncate">OthMastar</p>
              <p className="text-[10px] text-muted-foreground">{t.owner}</p>
            </div>
            <Badge
              variant="outline"
              className="text-[9px] border-primary/30 text-primary"
            >
              v2.0
            </Badge>
          </div>
        </div>
      </aside>
    </>
  );
}

const translations = {
  ar: {
    newChat: "محادثة جديدة",
    conversations: "المحادثات",
    noConversations: "لا توجد محادثات بعد",
    owner: "صاحب النظام",
    apiConnected: "API متصل",
    apiDisconnected: "API غير متصل",
    delete: "حذف",
    summarize: "تلخيص",
  },
  en: {
    newChat: "New Chat",
    conversations: "Conversations",
    noConversations: "No conversations yet",
    owner: "System Owner",
    apiConnected: "API Connected",
    apiDisconnected: "API Disconnected",
    delete: "Delete",
    summarize: "Summarize",
  },
};
