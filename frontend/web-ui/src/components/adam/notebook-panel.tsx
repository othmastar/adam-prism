"use client";

import { useAppStore, NotebookEntry } from "@/lib/store";
import { fetchNotebook, fetchNotebookStats } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  BookOpen,
  Menu,
  Calendar,
  Lightbulb,
  Link2,
  HelpCircle,
  FileText,
  AlertCircle,
  ChevronLeft,
  ChevronRight,
  Sparkles,
  Brain,
  CheckCircle2,
  PenLine,
  X,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCallback, useEffect, useState } from "react";

export function NotebookPanel() {
  const {
    settings,
    setSidebarOpen,
    setActiveView,
    apiConnected,
    notebookStats,
    setNotebookStats,
    notebookEntries,
    setNotebookEntries,
    dailyReflection,
  } = useAppStore();

  const [selectedDate, setSelectedDate] = useState(
    new Date().toISOString().split("T")[0]
  );
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const isArabic = settings.language === "ar";
  const t = isArabic ? notebookAr : notebookEn;

  // Fetch notebook stats
  const loadStats = useCallback(async () => {
    if (!apiConnected) {
      // Use demo stats
      setNotebookStats({
        pagesRead: 0,
        ideasExtracted: 0,
        connectionsMade: 0,
        pendingQuestions: 0,
      });
      return;
    }
    try {
      const data = await fetchNotebookStats();
      setNotebookStats({
        pagesRead: (data as Record<string, number>).pages_read || (data as Record<string, number>).pagesRead || 0,
        ideasExtracted: (data as Record<string, number>).ideas_extracted || (data as Record<string, number>).ideasExtracted || 0,
        connectionsMade: (data as Record<string, number>).connections_made || (data as Record<string, number>).connectionsMade || 0,
        pendingQuestions: (data as Record<string, number>).pending_questions || (data as Record<string, number>).pendingQuestions || 0,
      });
    } catch {
      setNotebookStats({
        pagesRead: 0,
        ideasExtracted: 0,
        connectionsMade: 0,
        pendingQuestions: 0,
      });
    }
  }, [apiConnected, setNotebookStats]);

  // Fetch notebook entries for selected date
  const loadEntries = useCallback(async () => {
    if (!apiConnected) {
      // Demo entries
      setNotebookEntries([
        {
          id: "demo-1",
          date: selectedDate,
          title: isArabic ? "ملاحظات تجريبية" : "Demo Notes",
          content: isArabic
            ? "هذه ملاحظات تجريبية. قم بتوصيل واجهة API للحصول على بيانات حقيقية."
            : "These are demo notes. Connect the API for real data.",
          connections: [],
          pendingQuestions: [
            isArabic ? "كيف يمكن تحسين البحث الدلالي؟" : "How can semantic search be improved?",
          ],
          tags: ["demo"],
        },
      ]);
      return;
    }
    setLoading(true);
    setError(null);
    try {
      const data = await fetchNotebook(selectedDate);
      const entries = Array.isArray(data)
        ? data.map((e: Record<string, unknown>, i: number) => ({
            id: (e.id as string) || `entry-${i}`,
            date: (e.date as string) || selectedDate,
            title: (e.title as string) || "Untitled",
            content: (e.content as string) || "",
            connections: (e.connections as string[]) || [],
            pendingQuestions: (e.pending_questions as string[]) || (e.pendingQuestions as string[]) || [],
            tags: (e.tags as string[]) || [],
          }))
        : [];
      setNotebookEntries(entries);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load notebook");
      setNotebookEntries([]);
    } finally {
      setLoading(false);
    }
  }, [apiConnected, selectedDate, isArabic, setNotebookEntries]);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  useEffect(() => {
    loadEntries();
  }, [loadEntries]);

  const navigateDate = (direction: number) => {
    const d = new Date(selectedDate);
    d.setDate(d.getDate() + direction);
    setSelectedDate(d.toISOString().split("T")[0]);
  };

  const formatDate = (dateStr: string) => {
    const d = new Date(dateStr);
    return d.toLocaleDateString(isArabic ? "ar-SA" : "en-US", {
      weekday: "long",
      year: "numeric",
      month: "long",
      day: "numeric",
    });
  };

  return (
    <div className="flex-1 flex flex-col h-full">
      {/* Top bar */}
      <div className="h-14 border-b border-border flex items-center px-4 gap-3 glass-subtle shrink-0">
        <Button
          variant="ghost"
          size="icon"
          className="md:hidden text-muted-foreground hover:text-primary"
          onClick={() => setSidebarOpen(true)}
        >
          <Menu className="h-5 w-5" />
        </Button>
        <BookOpen className="h-5 w-5 text-primary" />
        <span className="text-sm font-medium">{t.title}</span>
        <div className="flex-1" />
        <Badge
          variant="outline"
          className={cn(
            "text-[10px] gap-1",
            apiConnected
              ? "border-emerald-500/30 text-emerald-400"
              : "border-destructive/30 text-destructive"
          )}
        >
          {apiConnected ? <CheckCircle2 className="h-3 w-3" /> : <AlertCircle className="h-3 w-3" />}
          {apiConnected ? t.apiOnline : t.apiOffline}
        </Badge>
        <Button
          variant="ghost"
          size="icon"
          className="text-muted-foreground hover:text-primary"
          onClick={() => setActiveView("chat")}
          title={isArabic ? "عودة للمحادثة" : "Back to chat"}
        >
          <X className="h-5 w-5" />
        </Button>
      </div>

      <div className="flex-1 p-4 md:p-6 overflow-y-auto">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Date Navigation */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardContent className="p-4">
              <div className="flex items-center justify-between">
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigateDate(1)}
                  className="text-muted-foreground hover:text-primary"
                >
                  <ChevronRight className="h-5 w-5" />
                </Button>
                <div className="flex items-center gap-2">
                  <Calendar className="h-4 w-4 text-primary" />
                  <span className="text-sm font-medium">{formatDate(selectedDate)}</span>
                </div>
                <Button
                  variant="ghost"
                  size="icon"
                  onClick={() => navigateDate(-1)}
                  className="text-muted-foreground hover:text-primary"
                >
                  <ChevronLeft className="h-5 w-5" />
                </Button>
              </div>
            </CardContent>
          </Card>

          {/* Daily Reflection — Active Memory */}
          {dailyReflection && (
            <Card className="glass border-0 prism-border overflow-hidden">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <PenLine className="h-5 w-5 text-cyan-400" />
                  {t.dailyReflection}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="p-4 rounded-lg bg-gradient-to-r from-cyan-500/5 via-purple-500/5 to-blue-500/5 border border-cyan-500/20">
                  <div className="flex items-start gap-3">
                    <Brain className="h-5 w-5 text-cyan-400 shrink-0 mt-0.5" />
                    <div>
                      <p className="text-sm text-foreground/80 leading-relaxed">{dailyReflection}</p>
                      <p className="text-[10px] text-muted-foreground mt-2">
                        {t.reflectionAutoGenerated}
                      </p>
                    </div>
                  </div>
                </div>
              </CardContent>
            </Card>
          )}

          {/* Stats */}
          <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
            {[
              { icon: FileText, label: t.pagesRead, value: notebookStats?.pagesRead ?? "—", color: "text-primary" },
              { icon: Lightbulb, label: t.ideasExtracted, value: notebookStats?.ideasExtracted ?? "—", color: "text-cyan-400" },
              { icon: Link2, label: t.connectionsMade, value: notebookStats?.connectionsMade ?? "—", color: "text-blue-400" },
              { icon: HelpCircle, label: t.pendingQuestions, value: notebookStats?.pendingQuestions ?? "—", color: "text-yellow-400" },
            ].map((stat) => (
              <Card key={stat.label} className="glass border-0 prism-border overflow-hidden">
                <CardContent className="p-4 text-center">
                  <stat.icon className={cn("h-5 w-5 mx-auto mb-1.5", stat.color)} />
                  <p className={cn("text-lg font-bold", stat.color)}>{stat.value}</p>
                  <p className="text-[10px] text-muted-foreground">{stat.label}</p>
                </CardContent>
              </Card>
            ))}
          </div>

          {/* Timeline Entries */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Calendar className="h-5 w-5 text-primary" />
                {t.timeline}
              </CardTitle>
            </CardHeader>
            <CardContent>
              {loading ? (
                <div className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <div key={i} className="p-4 rounded-lg shimmer h-24" />
                  ))}
                </div>
              ) : notebookEntries.length === 0 ? (
                <div className="text-center py-8">
                  <BookOpen className="h-10 w-10 mx-auto text-primary/20 mb-2" />
                  <p className="text-sm text-muted-foreground">{t.noEntries}</p>
                </div>
              ) : (
                <div className="relative space-y-4">
                  {/* Timeline line */}
                  <div className="absolute start-4 top-0 bottom-0 w-px bg-gradient-to-b from-primary/40 via-cyan-400/30 to-blue-400/20" />

                  {notebookEntries.map((entry, i) => (
                    <NotebookEntryCard key={entry.id} entry={entry} index={i} isArabic={isArabic} t={t} />
                  ))}
                </div>
              )}
            </CardContent>
          </Card>

          {/* Pending Questions */}
          {notebookEntries.some((e) => e.pendingQuestions.length > 0) && (
            <Card className="glass border-0 prism-border overflow-hidden">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <HelpCircle className="h-5 w-5 text-yellow-400" />
                  {t.pendingQuestionsTitle}
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {notebookEntries
                    .filter((e) => e.pendingQuestions.length > 0)
                    .flatMap((e) => e.pendingQuestions)
                    .map((q, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 p-3 rounded-lg bg-yellow-500/5 border border-yellow-500/10"
                      >
                        <HelpCircle className="h-4 w-4 text-yellow-400 shrink-0 mt-0.5" />
                        <p className="text-sm text-foreground/80">{q}</p>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function NotebookEntryCard({
  entry,
  index,
  isArabic,
  t,
}: {
  entry: NotebookEntry;
  index: number;
  isArabic: boolean;
  t: Record<string, string>;
}) {
  return (
    <div className="relative ps-10 animate-fade-in-up" style={{ animationDelay: `${index * 100}ms` }}>
      {/* Timeline dot */}
      <div className="absolute start-3 top-4 h-3 w-3 rounded-full bg-primary ring-2 ring-background z-10" />

      <div className="p-4 rounded-lg bg-muted/30 border border-border/50 hover:border-primary/30 transition-colors">
        <div className="flex items-start justify-between gap-3 mb-2">
          <h3 className="text-sm font-medium flex items-center gap-2">
            <Brain className="h-3.5 w-3.5 text-primary" />
            {entry.title}
          </h3>
          {entry.tags.length > 0 && (
            <div className="flex gap-1 shrink-0">
              {entry.tags.slice(0, 3).map((tag) => (
                <Badge key={tag} variant="outline" className="text-[9px] border-primary/30 text-primary">
                  {tag}
                </Badge>
              ))}
            </div>
          )}
        </div>

        <p className="text-sm text-muted-foreground leading-relaxed">{entry.content}</p>

        {/* Connections */}
        {entry.connections.length > 0 && (
          <div className="mt-3 pt-3 border-t border-border/50">
            <p className="text-[10px] text-muted-foreground mb-1.5">{t.connections}:</p>
            <div className="flex flex-wrap gap-1.5">
              {entry.connections.map((conn, ci) => (
                <span
                  key={ci}
                  className="inline-flex items-center gap-1 text-[10px] px-2 py-0.5 rounded-full bg-cyan-500/10 text-cyan-400 border border-cyan-500/20"
                >
                  <Link2 className="h-2.5 w-2.5" />
                  {conn}
                </span>
              ))}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}

const notebookAr = {
  title: "الدفتر اليومي",
  timeline: "الجدول الزمني",
  pagesRead: "صفحات مقروءة",
  ideasExtracted: "أفكار مستخرجة",
  connectionsMade: "روابط",
  pendingQuestions: "أسئلة معلقة",
  pendingQuestionsTitle: "الأسئلة المعلقة",
  connections: "الروابط",
  noEntries: "لا توجد ملاحظات لهذا اليوم",
  dailyReflection: "الذاكرة الحية — خاطرة اليوم",
  reflectionAutoGenerated: "آدم يكتب خاطرة تقنية يومية تلخص ما تعلمه من OthMastar",
  apiOnline: "API متصل",
  apiOffline: "API غير متصل",
};

const notebookEn = {
  title: "Daily Notebook",
  timeline: "Timeline",
  pagesRead: "Pages Read",
  ideasExtracted: "Ideas Extracted",
  connectionsMade: "Connections",
  pendingQuestions: "Pending Qs",
  pendingQuestionsTitle: "Pending Questions",
  connections: "Connections",
  noEntries: "No notes for this day",
  dailyReflection: "Active Memory — Today's Reflection",
  reflectionAutoGenerated: "Adam writes a daily technical reflection summarizing what OthMastar explored",
  apiOnline: "API Online",
  apiOffline: "API Offline",
};
