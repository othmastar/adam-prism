"use client";

import { useState, useEffect, useRef } from "react";
import { useAppStore } from "@/lib/store";
import { deleteSessionOnServer, sendChatMessage, searchChatHistory } from "@/lib/api";
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
  Search,
  ChevronDown,
  ChevronUp,
  History,
  Clock,
  Package,
  Bot,
  GitBranch,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useTheme } from "@teispace/next-themes";
import { ViewType } from "@/lib/store";

type NavItem = {
  view: ViewType | "orchestrator";
  icon: React.ElementType;
  labelAr: string;
  labelEn: string;
  descAr: string;
  descEn: string;
};

type NavSection = {
  titleAr: string;
  titleEn: string;
  icon: React.ElementType;
  items: NavItem[];
};

const navSections: NavSection[] = [
  { titleAr: "تواصل", titleEn: "Chat", icon: MessageSquare, items: [
    { view: "chat", icon: MessageSquare, labelAr: "محادثة", labelEn: "Chat", descAr: "التواصل المباشر مع آدم", descEn: "Chat with Adam" },
  ]},
  { titleAr: "النظام", titleEn: "System", icon: Activity, items: [
    { view: "monitor", icon: Activity, labelAr: "حالة النظام", labelEn: "Monitor", descAr: "مؤشرات الأداء والصحة", descEn: "System health & performance" },
    { view: "pipeline", icon: Cpu, labelAr: "المعالجة", labelEn: "Pipeline", descAr: "سير خطوات المعالجة", descEn: "Processing pipeline steps" },
  ]},
  { titleAr: "المعرفة", titleEn: "Knowledge", icon: Database, items: [
    { view: "knowledge", icon: Database, labelAr: "المعرفة", labelEn: "Knowledge", descAr: "قاعدة المعرفة والبحث", descEn: "Knowledge base & search" },
    { view: "memory", icon: Brain, labelAr: "الذاكرة", labelEn: "Memory", descAr: "إدارة الذاكرة الطويلة", descEn: "Long-term memory management" },
    { view: "notebook", icon: BookOpen, labelAr: "الدفتر", labelEn: "Notebook", descAr: "الملاحظات اليومية", descEn: "Daily notes & ideas" },
  ]},
  { titleAr: "الأدوات", titleEn: "Tools", icon: Wrench, items: [
    { view: "tools", icon: Wrench, labelAr: "الأدوات", labelEn: "Tools", descAr: "كل أداة ووظيفتها", descEn: "Every tool & its function" },
    { view: "skills", icon: Sparkles, labelAr: "المهارات", labelEn: "Skills", descAr: "مهارات متخصصة قابلة للتحميل", descEn: "Loadable specialized skills" },
    { view: "scheduler", icon: Clock, labelAr: "المجدول", labelEn: "Scheduler", descAr: "جدولة المهام التلقائية", descEn: "Automated task scheduling" },
    { view: "plugins", icon: Package, labelAr: "الإضافات", labelEn: "Plugins", descAr: "إدارة الإضافات الخارجية", descEn: "Manage external plugins" },
    { view: "subagents", icon: Bot, labelAr: "الوكلاء", labelEn: "Subagents", descAr: "الوكلاء الفرعيون المستقلون", descEn: "Autonomous sub-agents" },
    { view: "orchestrator", icon: GitBranch, labelAr: "المايسترو", labelEn: "Orchestrator", descAr: "توزيع المهام على الموديلات", descEn: "Multi-model task orchestration" },
  ]},
  { titleAr: "القنوات", titleEn: "Channels", icon: Wifi, items: [
    { view: "channels", icon: Wifi, labelAr: "القنوات", labelEn: "Channels", descAr: "إدارة قنوات التواصل الـ 25", descEn: "Manage all 25+ channels" },
  ]},
  { titleAr: "الإعدادات", titleEn: "Settings", icon: Settings, items: [
    { view: "settings", icon: Settings, labelAr: "الإعدادات", labelEn: "Settings", descAr: "ضبط الموديل واللغة", descEn: "Model & language config" },
  ]},
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

  const [searchQuery, setSearchQuery] = useState("");
  const [searchResults, setSearchResults] = useState<Record<string, unknown>[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [expandedSections, setExpandedSections] = useState<Set<string>>(new Set(["chat", "system", "knowledge", "tools", "settings"]));
  const searchRef = useRef<HTMLInputElement>(null);

  const toggleSection = (title: string) => {
    setExpandedSections((prev) => {
      const next = new Set(prev);
      if (next.has(title)) next.delete(title);
      else next.add(title);
      return next;
    });
  };

  useEffect(() => {
    if (!searchQuery.trim()) {
      setSearchResults([]);
      setIsSearching(false);
      return;
    }
    const timer = setTimeout(async () => {
      setIsSearching(true);
      try {
        const res = await searchChatHistory(searchQuery.trim(), 10);
        setSearchResults(res.results);
      } catch {
        setSearchResults([]);
      } finally {
        setIsSearching(false);
      }
    }, 300);
    return () => clearTimeout(timer);
  }, [searchQuery]);

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
          sidebarOpen
            ? "translate-x-0"
            : isArabic
              ? "-translate-x-full md:translate-x-0"
              : "translate-x-full md:translate-x-0"
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

        {/* Navigation — أقسام قابلة للطي */}
        <div className="px-2 pb-2 space-y-1">
          {navSections.map((section) => {
            const SectionIcon = section.icon;
            const sectionTitle = isArabic ? section.titleAr : section.titleEn;
            const isExpanded = expandedSections.has(sectionTitle.toLowerCase());
            return (
              <div key={sectionTitle}>
                <button
                  onClick={() => toggleSection(sectionTitle.toLowerCase())}
                  className="w-full flex items-center gap-2 px-3 py-1.5 rounded-lg text-[11px] font-medium text-muted-foreground hover:text-foreground hover:bg-muted/20 transition-colors cursor-pointer group"
                >
                  <SectionIcon className="h-3.5 w-3.5" />
                  <span className="flex-1 text-left uppercase tracking-wider">{sectionTitle}</span>
                  <ChevronDown className={cn("h-3 w-3 transition-transform", isExpanded && "rotate-180")} />
                </button>
                {isExpanded && (
                  <div className="space-y-0.5 mt-0.5">
                    {section.items.map((item) => {
                      const ItemIcon = item.icon;
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
                            "w-full group flex items-center gap-3 px-3 py-2 rounded-lg text-sm transition-colors cursor-pointer",
                            isActive
                              ? "bg-primary/10 text-primary"
                              : "text-muted-foreground hover:bg-muted/30 hover:text-foreground"
                          )}
                        >
                          <div className={cn("h-7 w-7 rounded-lg flex items-center justify-center shrink-0", isActive ? "bg-primary/15" : "bg-muted/20")}>
                            <ItemIcon className={cn("h-3.5 w-3.5", isActive && "text-primary")} />
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
                )}
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
            <div className="px-1 pt-2">
              <div className="relative">
                <Search className="absolute left-2.5 top-1/2 -translate-y-1/2 h-3.5 w-3.5 text-muted-foreground/50" />
                <input
                  ref={searchRef}
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  placeholder={isArabic ? "ابحث في المحادثات..." : "Search conversations..."}
                  className="w-full h-8 pl-7 pr-3 text-xs rounded-md bg-muted/20 border border-border/30 text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 transition-all"
                />
                {isSearching && (
                  <div className="absolute right-2.5 top-1/2 -translate-y-1/2">
                    <div className="h-3 w-3 border border-primary/40 border-t-transparent rounded-full animate-spin" />
                  </div>
                )}
              </div>
            </div>
          </div>

          <div className={cn("flex-1 overflow-y-auto px-2 min-h-0", historyPanelOpen ? "block" : "hidden")} style={{ scrollbarWidth: "thin", scrollbarColor: "hsl(var(--border)) transparent" }}>
            <div className="space-y-1 pb-4">
              {searchQuery.trim() ? (
                searchResults.length === 0 ? (
                  <div className="px-3 py-6 text-center">
                    <Search className="h-6 w-6 mx-auto text-muted-foreground/30 mb-2" />
                    <p className="text-xs text-muted-foreground/60">
                      {isArabic ? "لا توجد نتائج" : "No results found"}
                    </p>
                  </div>
                ) : (
                  searchResults.map((result) => (
                    <div
                      key={result.id as string}
                      role="button"
                      tabIndex={0}
                      onClick={() => {
                        setActiveConversationId(result.session_id as string);
                        setActiveView("chat");
                        setSidebarOpen(false);
                        setSearchQuery("");
                      }}
                      onKeyDown={(e) => {
                        if (e.key === "Enter" || e.key === " ") {
                          e.preventDefault();
                          setActiveConversationId(result.session_id as string);
                          setActiveView("chat");
                          setSidebarOpen(false);
                          setSearchQuery("");
                        }
                      }}
                      className="w-full group flex items-start gap-2 px-3 py-2 rounded-lg text-sm cursor-pointer hover:bg-muted/20 transition-colors"
                    >
                      <MessageSquare className="h-3.5 w-3.5 text-muted-foreground/50 mt-0.5 shrink-0" />
                      <div className="min-w-0 flex-1">
                        <p className="text-[11px] font-medium text-foreground/80 truncate">
                          {result.role === "user" ? "أنت" : "آدم"}
                        </p>
                        <p className="text-[10px] text-muted-foreground/60 line-clamp-2 mt-0.5">
                          {(result.content as string)?.slice(0, 120)}
                        </p>
                      </div>
                    </div>
                  ))
                )
              ) : conversations.length === 0 ? (
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

        {/* Footer with Model Selector */}
        <div className="p-3 border-t border-border space-y-2">
          {/* Ollama Model Selector */}
          <ModelSelector />
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

// ─── Ollama Model Selector ───────────────────────────────────────────

function ModelSelector() {
  const { settings } = useAppStore();
  const { toast } = useToast();
  const isArabic = settings.language === "ar";
  const [models, setModels] = useState<string[]>([]);
  const [current, setCurrent] = useState(settings.modelName);
  const [loading, setLoading] = useState(false);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setCurrent(settings.modelName);
  }, [settings.modelName]);

  useEffect(() => {
    (async () => {
      try {
        const { fetchOllamaModels } = await import("@/lib/api");
        const list = await fetchOllamaModels();
        setModels(list);
      } catch {}
    })();
  }, []);

  const handleSelect = async (model: string) => {
    setLoading(true);
    try {
      const { selectOllamaModel, fetchOllamaModels } = await import("@/lib/api");
      const ok = await selectOllamaModel(model);
      if (ok) {
        setCurrent(model);
        useAppStore.getState().updateSettings({ modelName: model });
        toast({ title: isArabic ? `تم التبديل لـ ${model}` : `Switched to ${model}` });
        const list = await fetchOllamaModels();
        setModels(list);
      } else {
        toast({ title: isArabic ? "فشل التبديل" : "Switch failed", variant: "destructive" });
      }
    } catch {
      toast({ title: isArabic ? "خطأ في التبديل" : "Switch error", variant: "destructive" });
    } finally {
      setLoading(false);
      setOpen(false);
    }
  };

  return (
    <div className="px-2">
      <button
        onClick={() => setOpen(!open)}
        className="w-full flex items-center gap-2 px-3 py-2 rounded-lg text-xs bg-muted/20 hover:bg-muted/30 border border-border/30 transition-colors"
      >
        <svg className="h-3.5 w-3.5 text-primary shrink-0" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
          <path d="M12 2L2 7l10 5 10-5-10-5z" />
          <path d="M2 17l10 5 10-5" />
          <path d="M2 12l10 5 10-5" />
        </svg>
        <span className="flex-1 text-left truncate">{current || (isArabic ? "اختر موديل" : "Select model")}</span>
        {loading ? (
          <div className="h-3 w-3 border border-primary/40 border-t-transparent rounded-full animate-spin" />
        ) : (
          <ChevronDown className={cn("h-3 w-3 text-muted-foreground transition-transform", open && "rotate-180")} />
        )}
      </button>
      {open && (
        <div className="mt-1 rounded-lg border border-border bg-card shadow-lg overflow-hidden">
          {models.length === 0 ? (
            <div className="px-3 py-4 text-center text-[10px] text-muted-foreground/60">
              {isArabic ? "لا توجد موديلات متاحة" : "No models available"}
            </div>
          ) : (
            <div className="max-h-40 overflow-y-auto" style={{ scrollbarWidth: "thin" }}>
              {models.map((m) => (
                <button
                  key={m}
                  onClick={() => handleSelect(m)}
                  className={cn(
                    "w-full flex items-center gap-2 px-3 py-2 text-xs text-left hover:bg-muted/20 transition-colors",
                    m === current && "bg-primary/10 text-primary"
                  )}
                >
                  <div className={cn("h-1.5 w-1.5 rounded-full shrink-0", m === current ? "bg-primary" : "bg-muted-foreground/30")} />
                  <span className="truncate">{m}</span>
                  {m === current && <Badge variant="outline" className="text-[8px] border-primary/30 text-primary mr-auto px-1 py-0">{isArabic ? "نشط" : "Active"}</Badge>}
                </button>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
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
