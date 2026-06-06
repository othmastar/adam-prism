"use client";

import { useAppStore } from "@/lib/store";
import { executeToolAction, summarizeDocument } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Wrench,
  Menu,
  Monitor,
  Camera,
  FileUp,
  Globe,
  Upload,
  Play,
  FileText,
  AlertCircle,
  CheckCircle2,
  Loader2,
  RotateCcw,
  Zap,
  Eye,
  Terminal,
  Download,
  LayoutList,
  Activity,
  Timer,
  ChevronDown,
  ChevronUp,
  ChevronRight,
  Cpu,
  Network,
  Search,
  BookOpen,
  MousePointer2,
  ToggleLeft,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCallback, useRef, useState } from "react";

type TaskItem = {
  id: string;
  name: string;
  status: "running" | "done" | "error";
  progress: number;
  startedAt: number;
};

type ToolEntry = {
  id: string;
  icon: React.ElementType;
  name: string;
  desc: string;
  category: "computer" | "browser" | "summarize";
};

export function ToolsPanel() {
  const { settings, setSidebarOpen, apiConnected, summarizeProgress, setSummarizeProgress } = useAppStore();
  const isArabic = settings.language === "ar";
  const t = isArabic ? toolsAr : toolsEn;

  const [activeTasks, setActiveTasks] = useState<TaskItem[]>([]);
  const [completedCount, setCompletedCount] = useState(0);
  const taskCounter = useRef(0);
  const [controlsOpen, setControlsOpen] = useState(false);
  const [tasksOpen, setTasksOpen] = useState(false);

  const addTask = useCallback((name: string) => {
    taskCounter.current += 1;
    const task: TaskItem = { id: `task-${taskCounter.current}`, name, status: "running", progress: 0, startedAt: Date.now() };
    setActiveTasks((prev) => [task, ...prev].slice(0, 6));
    return task.id;
  }, []);

  const updateTask = useCallback((id: string, updates: Partial<TaskItem>) => {
    setActiveTasks((prev) => {
      const idx = prev.findIndex((t) => t.id === id);
      if (idx === -1) return prev;
      const updated = [...prev];
      updated[idx] = { ...updated[idx], ...updates };
      return updated;
    });
  }, []);

  const completeTask = useCallback((id: string, status: "done" | "error" = "done") => {
    setActiveTasks((prev) => {
      const task = prev.find((t) => t.id === id);
      if (!task) return prev;
      setCompletedCount((c) => c + 1);
      return prev.filter((t) => t.id !== id);
    });
  }, []);

  const simulateConcurrentTasks = useCallback(async () => {
    const taskDefs = [t.taskScanSystem, t.taskAnalyzeTraffic, t.taskProcessData, t.taskGenReport, t.taskOptimizeCache];
    const taskIds: string[] = [];
    for (const name of taskDefs) {
      await new Promise((r) => setTimeout(r, 200));
      taskIds.push(addTask(name));
    }
    for (let i = 0; i < taskIds.length; i++) {
      for (let p = 10; p <= 100; p += 12) {
        await new Promise((r) => setTimeout(r, 200));
        updateTask(taskIds[i], { progress: p, status: p < 100 ? "running" : "done" });
      }
      completeTask(taskIds[i], "done");
    }
  }, [addTask, updateTask, completeTask, t]);

  const [screenshotLoading, setScreenshotLoading] = useState(false);
  const [screenshotResult, setScreenshotResult] = useState<string | null>(null);
  const [browserUrl, setBrowserUrl] = useState("https://");
  const [browserAction, setBrowserAction] = useState("navigate");
  const [browserLoading, setBrowserLoading] = useState(false);
  const [browserResult, setBrowserResult] = useState<string | null>(null);
  const [summarizeText, setSummarizeText] = useState("");
  const [summarizeTitle, setSummarizeTitle] = useState("");
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleScreenshot = useCallback(async () => {
    setScreenshotLoading(true);
    setScreenshotResult(null);
    const taskId = addTask(t.taskScreenshot);
    try {
      if (apiConnected) {
        const result = await executeToolAction({ type: "screenshot" });
        setScreenshotResult((result as Record<string, string>).message || (result as Record<string, string>).path || "Screenshot taken");
      } else {
        for (let p = 10; p <= 100; p += 20) { await new Promise((r) => setTimeout(r, 200)); updateTask(taskId, { progress: p }); }
        setScreenshotResult(isArabic ? "تم التقاط لقطة الشاشة (تجريبي)" : "Screenshot captured (demo)");
      }
      completeTask(taskId, "done");
    } catch (err) { completeTask(taskId, "error"); setScreenshotResult(`Error: ${err instanceof Error ? err.message : "Failed"}`); }
    finally { setScreenshotLoading(false); }
  }, [apiConnected, isArabic, addTask, updateTask, completeTask]);

  const handleBrowserAction = useCallback(async () => {
    if (!browserUrl.trim()) return;
    setBrowserLoading(true);
    setBrowserResult(null);
    const taskId = addTask(t.taskBrowse.replace("{url}", browserUrl.slice(0, 30)));
    try {
      if (apiConnected) {
        const result = await executeToolAction({ type: browserAction, url: browserUrl });
        setBrowserResult((result as Record<string, string>).message || (result as Record<string, string>).content || "Action completed");
      } else {
        for (let p = 10; p <= 100; p += 15) { await new Promise((r) => setTimeout(r, 300)); updateTask(taskId, { progress: p }); }
        setBrowserResult(isArabic ? "تم تنفيذ الإجراء (تجريبي)" : "Action completed (demo)");
      }
      completeTask(taskId, "done");
    } catch (err) { completeTask(taskId, "error"); setBrowserResult(`Error: ${err instanceof Error ? err.message : "Failed"}`); }
    finally { setBrowserLoading(false); }
  }, [apiConnected, browserUrl, browserAction, isArabic, addTask, updateTask, completeTask, t]);

  const handleSummarize = useCallback(async () => {
    if (!summarizeText.trim()) return;
    const taskId = addTask(t.taskSummarize);
    setSummarizeProgress({ status: "processing", progress: 0, chunksProcessed: 0, totalChunks: 10 });
    try {
      const totalChunks = 10;
      for (let i = 1; i <= totalChunks; i++) {
        await new Promise((r) => setTimeout(r, 200));
        const p = (i / totalChunks) * 100;
        updateTask(taskId, { progress: p });
        setSummarizeProgress({ progress: p, chunksProcessed: i, totalChunks });
      }
      if (apiConnected) {
        const result = await summarizeDocument(summarizeText, "upload", summarizeTitle || "Untitled");
        setSummarizeProgress({ status: "done", progress: 100, chunksProcessed: totalChunks, totalChunks,
          result: (result as Record<string, string>).summary || (result as Record<string, string>).result || JSON.stringify(result) });
      } else {
        setSummarizeProgress({ status: "done", progress: 100, chunksProcessed: totalChunks, totalChunks,
          result: isArabic ? "هذا ملخص تجريبي للمستند المقدم." : "Demo summary." });
      }
      completeTask(taskId, "done");
    } catch (err) { completeTask(taskId, "error");
      setSummarizeProgress({ status: "error", progress: 0, chunksProcessed: 0, totalChunks: 0, error: err instanceof Error ? err.message : "Failed" }); }
  }, [apiConnected, summarizeText, summarizeTitle, isArabic, setSummarizeProgress, addTask, updateTask, completeTask, t]);

  const toolsList: ToolEntry[] = [
    { id: "screenshot", icon: Camera, name: t.screenshot, desc: t.screenshotDesc, category: "computer" },
    { id: "file-ops", icon: FileText, name: t.fileOps, desc: t.fileOpsDesc, category: "computer" },
    { id: "terminal", icon: Terminal, name: t.terminal, desc: t.terminalDesc, category: "computer" },
    { id: "download", icon: Download, name: t.download, desc: t.downloadDesc, category: "computer" },
    { id: "mouse", icon: MousePointer2, name: t.mouse, desc: t.mouseDesc, category: "computer" },
    { id: "browser-nav", icon: Globe, name: t.browserNav, desc: t.browserNavDesc, category: "browser" },
    { id: "browser-extract", icon: Eye, name: t.browserExtract, desc: t.browserExtractDesc, category: "browser" },
    { id: "browser-shot", icon: Camera, name: t.browserShot, desc: t.browserShotDesc, category: "browser" },
    { id: "browser-search", icon: Search, name: t.browserSearch, desc: t.browserSearchDesc, category: "browser" },
    { id: "summarize", icon: Zap, name: t.liveSummarization, desc: t.summarizeFuncDesc, category: "summarize" },
    { id: "chunk", icon: LayoutList, name: t.chunking, desc: t.chunkingDesc, category: "summarize" },
    { id: "concepts", icon: BookOpen, name: t.concepts, desc: t.conceptsDesc, category: "summarize" },
  ];

  const categoryMeta = {
    computer: { label: t.catComputer, icon: Monitor, color: "text-cyan-400", bg: "bg-cyan-500/10", border: "border-cyan-500/20" },
    browser: { label: t.catBrowser, icon: Globe, color: "text-violet-400", bg: "bg-violet-500/10", border: "border-violet-500/20" },
    summarize: { label: t.catSummarize, icon: Zap, color: "text-amber-400", bg: "bg-amber-500/10", border: "border-amber-500/20" },
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Top bar */}
      <div className="h-14 border-b border-border flex items-center px-4 gap-3 glass-subtle shrink-0">
        <Button variant="ghost" size="icon" className="md:hidden text-muted-foreground hover:text-primary" onClick={() => setSidebarOpen(true)}>
          <Menu className="h-5 w-5" />
        </Button>
        <Wrench className="h-5 w-5 text-primary" />
        <span className="text-sm font-medium">{t.title}</span>
        <div className="flex-1" />
        {activeTasks.length > 0 && (
          <Badge variant="secondary" className="text-[10px] gap-1 border-primary/20">
            <Activity className="h-3 w-3 text-primary animate-pulse" />
            {activeTasks.length} {isArabic ? "مهام" : "tasks"}
          </Badge>
        )}
        {completedCount > 0 && (
          <span className="text-[9px] text-muted-foreground/50">{completedCount} {isArabic ? "تم" : "done"}</span>
        )}
        <Badge variant="outline" className={cn("text-[10px] gap-1", apiConnected ? "border-emerald-500/30 text-emerald-400" : "border-destructive/30 text-destructive")}>
          {apiConnected ? <CheckCircle2 className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
          {apiConnected ? t.apiOnline : t.apiOffline}
        </Badge>
      </div>

      <ScrollArea className="flex-1">
        <div className="p-4 md:p-6 max-w-4xl mx-auto space-y-4">
          {/* Top controls: Simulate + Toggle */}
          <div className="flex items-center gap-2">
            <Button onClick={simulateConcurrentTasks} disabled={activeTasks.length > 0}
              className="bg-gradient-to-r from-purple-600 via-violet-500 to-cyan-400 text-white hover:opacity-90 gap-1.5 text-xs h-7" size="sm">
              <Activity className="h-3 w-3" />
              {t.simulateTasks}
            </Button>
            <Button variant="ghost" size="sm" className="text-xs gap-1 h-7 text-muted-foreground"
              onClick={() => setTasksOpen(!tasksOpen)}>
              <Cpu className="h-3 w-3" />
              {t.activeTasks} {activeTasks.length > 0 && `(${activeTasks.length})`}
              {tasksOpen ? <ChevronUp className="h-3 w-3" /> : <ChevronDown className="h-3 w-3" />}
            </Button>
          </div>

          {/* Running Tasks (collapsible) */}
          {tasksOpen && activeTasks.length > 0 && (
            <div className="space-y-2 p-3 rounded-lg bg-muted/10 border border-border/30">
              {activeTasks.map((task) => (
                <div key={task.id} className="flex items-center gap-3">
                  {task.status === "running" ? (
                    <Loader2 className="h-3.5 w-3.5 animate-spin text-primary shrink-0" />
                  ) : task.status === "done" ? (
                    <CheckCircle2 className="h-3.5 w-3.5 text-emerald-400 shrink-0" />
                  ) : (
                    <AlertCircle className="h-3.5 w-3.5 text-destructive shrink-0" />
                  )}
                  <span className="text-xs flex-1 truncate">{task.name}</span>
                  <span className="text-[10px] font-mono text-muted-foreground w-8 text-right">{Math.round(task.progress)}%</span>
                  <div className="w-20">
                    <Progress value={task.progress} className="h-1 bg-muted" />
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* ─── FUNCTION LIST: كل أداة ووظيفتها — نمط السايدبار ─── */}
          <div className="space-y-6">
            {(Object.keys(categoryMeta) as ("computer" | "browser" | "summarize")[]).map((cat) => {
              const meta = categoryMeta[cat];
              const CatIcon = meta.icon;
              const items = toolsList.filter((tl) => tl.category === cat);
              return (
                <div key={cat}>
                  {/* Category header */}
                  <div className="flex items-center gap-2 mb-2 px-1">
                    <CatIcon className={cn("h-4 w-4", meta.color)} />
                    <span className={cn("text-xs font-semibold", meta.color)}>{meta.label}</span>
                    <span className="text-[9px] text-muted-foreground/40">{items.length}</span>
                  </div>

                  {/* Tool rows — exactly like conversation history list */}
                  <div className="space-y-0.5">
                    {items.map((tool) => {
                      const Icon = tool.icon;
                      return (
                        <div
                          key={tool.id}
                          role="button"
                          tabIndex={0}
                          className={cn(
                            "w-full group flex items-center gap-3 px-3 py-2.5 rounded-lg text-sm transition-colors cursor-pointer",
                            "text-muted-foreground hover:bg-muted/30 hover:text-foreground"
                          )}
                          onClick={() => setControlsOpen(true)}
                          onKeyDown={(e) => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); setControlsOpen(true); } }}
                        >
                          {/* Icon */}
                          <div className={cn("h-8 w-8 rounded-lg flex items-center justify-center shrink-0", meta.bg)}>
                            <Icon className={cn("h-4 w-4", meta.color)} />
                          </div>

                          {/* Name + Description */}
                          <div className="flex-1 min-w-0">
                            <p className="text-xs font-medium truncate">{tool.name}</p>
                            <p className="text-[10px] text-muted-foreground/60 line-clamp-1">{tool.desc}</p>
                          </div>

                          {/* Status badge */}
                          <Badge variant="outline" className={cn(
                            "text-[8px] px-1.5 py-0 h-4 shrink-0 opacity-0 group-hover:opacity-100 transition-opacity",
                            apiConnected ? "border-emerald-500/20 text-emerald-400" : "border-amber-500/20 text-amber-400"
                          )}>
                            {apiConnected ? t.online : t.offline}
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                </div>
              );
            })}
          </div>

          {/* ─── Interactive Controls (collapsible) ─── */}
          <Separator className="bg-border/50" />
          <button
            onClick={() => setControlsOpen(!controlsOpen)}
            className="w-full flex items-center justify-between group cursor-pointer py-1"
          >
            <span className="text-[11px] font-medium text-muted-foreground uppercase tracking-wider flex items-center gap-1.5">
              <ToggleLeft className="h-3 w-3" />
              {t.controls}
            </span>
            {controlsOpen ? <ChevronUp className="h-3 w-3 text-muted-foreground/50" /> : <ChevronDown className="h-3 w-3 text-muted-foreground/50" />}
          </button>

          {controlsOpen && (
            <div className="space-y-4">
              {/* Screenshot */}
              <div className="flex items-center gap-3 p-3 rounded-lg bg-muted/10 border border-border/30">
                <Camera className="h-4 w-4 text-cyan-400 shrink-0" />
                <span className="text-xs flex-1">{t.screenshot}</span>
                <Button onClick={handleScreenshot} disabled={screenshotLoading}
                  className="bg-primary/10 text-primary hover:bg-primary/20 border border-primary/30 h-7 text-xs" variant="outline" size="sm">
                  {screenshotLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Camera className="h-3 w-3" />}
                  <span className="ms-1">{t.takeScreenshot}</span>
                </Button>
              </div>
              {screenshotResult && <p className="text-[10px] text-muted-foreground px-3">{screenshotResult}</p>}

              {/* Browser */}
              <div className="p-3 rounded-lg bg-muted/10 border border-border/30 space-y-2">
                <div className="flex items-center gap-2">
                  <Globe className="h-4 w-4 text-violet-400 shrink-0" />
                  <span className="text-xs flex-1">{t.browserAutomation}</span>
                </div>
                <div className="flex gap-2">
                  <Input value={browserUrl} onChange={(e) => setBrowserUrl(e.target.value)} placeholder="https://example.com"
                    className="flex-1 h-8 text-xs bg-muted/50 border-border" dir="ltr" />
                  <Button onClick={handleBrowserAction} disabled={browserLoading || !browserUrl.trim()}
                    className="bg-gradient-to-bl from-cyan-500 to-blue-500 text-white hover:opacity-90 h-8 text-xs" size="sm">
                    {browserLoading ? <Loader2 className="h-3 w-3 animate-spin" /> : <Play className="h-3 w-3" />}
                  </Button>
                </div>
                <div className="flex gap-1">
                  {(["navigate", "screenshot", "extract"] as const).map((action) => (
                    <Button key={action} variant={browserAction === action ? "secondary" : "ghost"} size="sm"
                      className={cn("text-[10px] h-6 gap-1", browserAction === action && "bg-primary/10 text-primary")}
                      onClick={() => setBrowserAction(action)}>
                      {action === "navigate" && <Globe className="h-3 w-3" />}
                      {action === "screenshot" && <Camera className="h-3 w-3" />}
                      {action === "extract" && <Eye className="h-3 w-3" />}
                      {t[`browser_${action}` as keyof typeof t] || action}
                    </Button>
                  ))}
                </div>
                {browserResult && <p className="text-[10px] text-muted-foreground p-2 rounded bg-muted/30">{browserResult}</p>}
              </div>

              {/* Summarize */}
              <div className="p-3 rounded-lg bg-muted/10 border border-border/30 space-y-2">
                <div className="flex items-center gap-2">
                  <Zap className="h-4 w-4 text-amber-400 shrink-0" />
                  <span className="text-xs flex-1">{t.liveSummarization}</span>
                  <input ref={fileInputRef} type="file" className="hidden" accept=".txt,.md,.pdf,.doc,.docx" onChange={(e) => {
                    const file = e.target.files?.[0]; if (!file) return;
                    const reader = new FileReader();
                    reader.onload = (ev) => { setSummarizeText(ev.target?.result as string); setSummarizeTitle(file.name.replace(/\.[^/.]+$/, "")); };
                    reader.readAsText(file);
                  }} />
                  <Button variant="outline" size="sm" className="h-7 text-xs gap-1 border-primary/30 text-primary hover:bg-primary/10"
                    onClick={() => fileInputRef.current?.click()}>
                    <Upload className="h-3 w-3" />
                    {t.upload}
                  </Button>
                </div>
                <Textarea value={summarizeText} onChange={(e) => setSummarizeText(e.target.value)} placeholder={t.pasteText}
                  className="min-h-[80px] bg-muted/50 border-border text-xs" dir={isArabic ? "rtl" : "ltr"} />
                <div className="flex items-center gap-2">
                  <Button onClick={handleSummarize} disabled={summarizeProgress.status === "processing" || !summarizeText.trim()}
                    className="bg-gradient-to-bl from-primary via-purple-500 to-cyan-500 text-white hover:opacity-90 gap-1.5 h-7 text-xs" size="sm">
                    {summarizeProgress.status === "processing" ? <Loader2 className="h-3 w-3 animate-spin" /> : <Zap className="h-3 w-3" />}
                    {t.summarize}
                  </Button>
                  {summarizeProgress.status !== "idle" && (
                    <Button variant="ghost" size="sm" onClick={() => { setSummarizeProgress({ status: "idle", progress: 0, chunksProcessed: 0, totalChunks: 0 }); setSummarizeText(""); setSummarizeTitle(""); }} className="text-xs h-7 text-muted-foreground">
                      <RotateCcw className="h-3 w-3 me-1" />
                      {t.reset}
                    </Button>
                  )}
                </div>
                {summarizeProgress.status === "processing" && (
                  <div className="space-y-1">
                    <div className="flex items-center justify-between text-[10px]">
                      <span className="text-muted-foreground">{t.processingChunk} {summarizeProgress.chunksProcessed}/{summarizeProgress.totalChunks}</span>
                      <span className="text-primary font-mono">{Math.round(summarizeProgress.progress)}%</span>
                    </div>
                    <Progress value={summarizeProgress.progress} className="h-1.5 bg-muted" />
                    <div className="flex gap-0.5">
                      {Array.from({ length: summarizeProgress.totalChunks }).map((_, i) => (
                        <div key={i} className={cn("flex-1 h-1 rounded-full", i < summarizeProgress.chunksProcessed ? "bg-gradient-to-r from-primary to-cyan-400" : "bg-muted/50")} />
                      ))}
                    </div>
                  </div>
                )}
                {summarizeProgress.status === "done" && summarizeProgress.result && (
                  <div className="p-3 rounded-lg bg-primary/5 border border-primary/20">
                    <div className="flex items-center gap-2 mb-1"><CheckCircle2 className="h-3 w-3 text-emerald-400" /><span className="text-[10px] font-medium text-emerald-400">{t.complete}</span></div>
                    <p className="text-xs leading-relaxed">{summarizeProgress.result}</p>
                  </div>
                )}
                {summarizeProgress.status === "error" && (
                  <div className="flex items-center gap-2 p-2 rounded-lg bg-destructive/10 border border-destructive/20 text-destructive text-[10px]">
                    <AlertCircle className="h-3 w-3 shrink-0" /><span>{summarizeProgress.error}</span>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </ScrollArea>
    </div>
  );
}

const toolsAr: Record<string, string> = {
  title: "الأدوات والوظائف",
  activeTasks: "المهام النشطة",
  controls: "لوحة التحكم",
  catComputer: "التحكم في الحاسوب",
  catBrowser: "أتمتة المتصفح",
  catSummarize: "التلخيص",
  screenshot: "لقطة شاشة",
  screenshotDesc: "التقاط صورة للشاشة الحالية وحفظها",
  fileOps: "عمليات الملفات",
  fileOpsDesc: "قراءة وكتابة وتنظيم الملفات على النظام",
  browserNav: "تصفح المواقع",
  browserNavDesc: "فتح URL والتنقل بين صفحات الويب",
  browserExtract: "استخراج محتوى",
  browserExtractDesc: "سحب النصوص والبيانات من صفحات الويب",
  browserShot: "لقطة متصفح",
  browserShotDesc: "تصوير صفحة الويب كاملة",
  browserSearch: "بحث في الموقع",
  browserSearchDesc: "البحث داخل محتوى الصفحات المفتوحة",
  terminal: "الطرفية",
  terminalDesc: "تنفيذ أوامر مباشرة على النظام",
  download: "تحميل ملفات",
  downloadDesc: "سحب ملفات من الإنترنت وحفظها محلياً",
  mouse: "تحكم بالفأرة",
  mouseDesc: "نقر، سحب، تمرير وتحريك مؤشر الفأرة",
  liveSummarization: "التلخيص المباشر",
  summarizeFuncDesc: "تقسيم المستندات الضخمة وتلخيصها جزءاً جزءاً",
  chunking: "تقسيم المستندات",
  chunkingDesc: "تقسيم النصوص الطويلة لأجزاء مترابطة",
  concepts: "استخراج المفاهيم",
  conceptsDesc: "استخراج المصطلحات والمفاهيم الرئيسية من النصوص",
  takeScreenshot: "التقط",
  filePath: "مسار الملف...",
  readFile: "قراءة ملف",
  browserAutomation: "أتمتة المتصفح",
  execute: "تنفيذ",
  browser_navigate: "تنقل",
  browser_screenshot: "لقطة",
  browser_extract: "استخراج",
  summarize: "لخص",
  reset: "إعادة",
  processingChunk: "معالجة",
  complete: "اكتمل",
  upload: "رفع",
  pasteText: "الصق النص هنا...",
  apiOnline: "متصل",
  apiOffline: "غير متصل",
  online: "متاح",
  offline: "غير متاح",
  simulateTasks: "محاكاة 5 مهام",
  taskScanSystem: "فحص أمني للنظام",
  taskAnalyzeTraffic: "تحليل حركة الشبكة",
  taskProcessData: "معالجة بيانات ضخمة",
  taskGenReport: "توليد تقرير ذكي",
  taskOptimizeCache: "تحسين الذاكرة المخبأة",
  taskScreenshot: "لالتقاط لقطة شاشة",
  taskBrowse: "تصفح {url}",
  taskSummarize: "تلخيص مستند",
};

const toolsEn: Record<string, string> = {
  title: "Tools & Functions",
  activeTasks: "Active Tasks",
  controls: "Control Panel",
  catComputer: "Computer Control",
  catBrowser: "Browser Automation",
  catSummarize: "Summarization",
  screenshot: "Screenshot",
  screenshotDesc: "Capture the current screen and save it",
  fileOps: "File Operations",
  fileOpsDesc: "Read, write, and organize files on the system",
  browserNav: "Web Navigation",
  browserNavDesc: "Open URLs and browse web pages",
  browserExtract: "Content Extraction",
  browserExtractDesc: "Extract text and data from web pages",
  browserShot: "Browser Screenshot",
  browserShotDesc: "Capture full-page screenshots of websites",
  browserSearch: "Site Search",
  browserSearchDesc: "Search within open web page content",
  terminal: "Terminal",
  terminalDesc: "Execute system commands directly",
  download: "File Download",
  downloadDesc: "Download files from the internet and save locally",
  mouse: "Mouse Control",
  mouseDesc: "Click, drag, scroll, and move the mouse cursor",
  liveSummarization: "Live Summarization",
  summarizeFuncDesc: "Split large documents and summarize them chunk by chunk",
  chunking: "Document Chunking",
  chunkingDesc: "Split long texts into interconnected chunks",
  concepts: "Concept Extraction",
  conceptsDesc: "Extract key terms and concepts from texts",
  takeScreenshot: "Capture",
  filePath: "File path...",
  readFile: "Read File",
  browserAutomation: "Browser Automation",
  execute: "Go",
  browser_navigate: "Navigate",
  browser_screenshot: "Screenshot",
  browser_extract: "Extract",
  summarize: "Summarize",
  reset: "Reset",
  processingChunk: "Chunk",
  complete: "Done",
  upload: "Upload",
  pasteText: "Paste text here...",
  apiOnline: "Online",
  apiOffline: "Offline",
  online: "Available",
  offline: "Unavailable",
  simulateTasks: "Simulate 5 Tasks",
  taskScanSystem: "System Security Scan",
  taskAnalyzeTraffic: "Network Traffic Analysis",
  taskProcessData: "Big Data Processing",
  taskGenReport: "Smart Report Generation",
  taskOptimizeCache: "Cache Optimization",
  taskScreenshot: "Taking Screenshot",
  taskBrowse: "Browsing {url}",
  taskSummarize: "Summarizing Document",
};
