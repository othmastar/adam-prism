"use client";

import { useAppStore, SearchResult } from "@/lib/store";
import { searchKnowledge, addKnowledge, uploadKnowledgeFile } from "@/lib/api";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Separator } from "@/components/ui/separator";
import {
  Search,
  Database,
  Menu,
  RefreshCw,
  FileText,
  Hash,
  Clock,
  AlertCircle,
  Sparkles,
  Layers,
  CheckCircle2,
  Network,
  PlusCircle,
  Loader2,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { useCallback, useEffect, useState } from "react";
import { KnowledgeGraph } from "@/components/adam/knowledge-graph";

export function KnowledgePanel() {
  const {
    settings,
    setSidebarOpen,
    apiConnected,
    knowledgeStats,
    setKnowledgeStats,
    searchResults,
    setSearchResults,
    isSearching,
    setIsSearching,
  } = useAppStore();

  const [query, setQuery] = useState("");
  const [collection, setCollection] = useState("knowledge");
  const [topK, setTopK] = useState(5);
  const [error, setError] = useState<string | null>(null);
  const isArabic = settings.language === "ar";
  const t = isArabic ? knowledgeAr : knowledgeEn;

  // Add knowledge state
  const [addText, setAddText] = useState("");
  const [addCollection, setAddCollection] = useState("knowledge");
  const [isAdding, setIsAdding] = useState(false);
  const [addResult, setAddResult] = useState<string | null>(null);

  // Upload knowledge state
  const [uploadFile, setUploadFile] = useState<File | null>(null);
  const [uploadCollection, setUploadCollection] = useState("knowledge");
  const [isUploading, setIsUploading] = useState(false);
  const [uploadResult, setUploadResult] = useState<string | null>(null);

  // Fetch knowledge stats on mount
  const fetchStats = useCallback(async () => {
    if (!apiConnected) return;
    try {
      const [colRes, recentRes] = await Promise.all([
        fetch(`${settings.fastApiUrl}/api/knowledge/collections`, {
          signal: AbortSignal.timeout(5000),
        }),
        fetch(`${settings.fastApiUrl}/api/knowledge/recent?limit=5`, {
          signal: AbortSignal.timeout(5000),
        }),
      ]);
      const colData = colRes.ok ? await colRes.json() : null;
      const recentData = recentRes.ok ? await recentRes.json() : null;
      setKnowledgeStats({
        totalEntries: colData?.total ?? 0,
        collections: colData?.collections?.map((c: any) => c.name) ?? ["knowledge"],
        lastUpdated: new Date().toISOString(),
      });
    } catch {
      // Use placeholder stats
      if (!knowledgeStats) {
        setKnowledgeStats({
          totalEntries: 0,
          collections: ["knowledge"],
          lastUpdated: new Date().toISOString(),
        });
      }
    }
  }, [apiConnected, settings.fastApiUrl, setKnowledgeStats, knowledgeStats]);

  useEffect(() => {
    fetchStats();
  }, [fetchStats]);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;

    setIsSearching(true);
    setError(null);

    try {
      if (apiConnected) {
        const results = await searchKnowledge(query, collection, topK);
        setSearchResults(
          results.map((r, i) => ({
            id: r.id || `result-${i}`,
            content: r.content,
            score: r.score,
            metadata: r.metadata,
            collection: r.collection || collection,
          }))
        );
      } else {
        // Demo results when API is not connected
        setSearchResults([
          {
            id: "demo-1",
            content: isArabic
              ? "هذه نتيجة تجريبية. قم بتوصيل واجهة API للحصول على نتائج حقيقية."
              : "This is a demo result. Connect the API for real results.",
            score: 0.95,
            collection: "knowledge",
          },
        ]);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : "Search failed");
    } finally {
      setIsSearching(false);
    }
  }, [query, collection, topK, apiConnected, isArabic, setIsSearching, setSearchResults]);

  const handleKeyDown = (e: React.KeyboardEvent) => {
    if (e.key === "Enter") {
      handleSearch();
    }
  };

  const handleAddKnowledge = async () => {
    if (!addText.trim() || isAdding) return;
    setIsAdding(true);
    setAddResult(null);
    try {
      const res = await addKnowledge(addText.trim(), addCollection);
      if (res.success) {
        setAddResult(isArabic ? `تمت الإضافة بنجاح في ${res.collection}` : `Added successfully to ${res.collection}`);
        setAddText("");
        fetchStats();
      } else {
        setAddResult(isArabic ? "فشلت الإضافة" : "Add failed");
      }
    } catch {
      setAddResult(isArabic ? "خطأ في الإضافة" : "Add error");
    } finally {
      setIsAdding(false);
    }
  };

  const handleUploadKnowledge = async () => {
    if (!uploadFile || isUploading) return;
    setIsUploading(true);
    setUploadResult(null);
    try {
      const res = await uploadKnowledgeFile(uploadFile, uploadCollection);
      setUploadResult(
        isArabic
          ? `تم رفع ${res.filename} — ${res.chunks} مقطع, ${res.total_chars} حرف`
          : `${res.filename} uploaded — ${res.chunks} chunks, ${res.total_chars} chars`
      );
      setUploadFile(null);
      fetchStats();
    } catch (err: any) {
      setUploadResult(isArabic ? `فشل الرفع: ${err.message}` : `Upload failed: ${err.message}`);
    } finally {
      setIsUploading(false);
    }
  };

  const getScoreColor = (score: number) => {
    if (score >= 0.8) return "text-emerald-400";
    if (score >= 0.5) return "text-yellow-400";
    return "text-red-400";
  };

  const getScoreBg = (score: number) => {
    if (score >= 0.8) return "bg-emerald-500/10 border-emerald-500/20";
    if (score >= 0.5) return "bg-yellow-500/10 border-yellow-500/20";
    return "bg-red-500/10 border-red-500/20";
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
        <Database className="h-5 w-5 text-primary" />
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
          {apiConnected ? (
            <CheckCircle2 className="h-3 w-3" />
          ) : (
            <AlertCircle className="h-3 w-3" />
          )}
          {apiConnected ? t.apiOnline : t.apiOffline}
        </Badge>
      </div>

      <div className="flex-1 p-4 md:p-6 overflow-y-auto">
        <div className="max-w-4xl mx-auto space-y-6">
          {/* Search Section */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Search className="h-5 w-5 text-primary" />
                {t.semanticSearch}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="flex gap-2">
                <div className="flex-1 relative">
                  <Search className="absolute start-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
                  <Input
                    value={query}
                    onChange={(e) => setQuery(e.target.value)}
                    onKeyDown={handleKeyDown}
                    placeholder={t.searchPlaceholder}
                    className="ps-9 bg-muted/50 border-border"
                    dir={isArabic ? "rtl" : "ltr"}
                  />
                </div>
                <Button
                  onClick={handleSearch}
                  disabled={isSearching || !query.trim()}
                  className="bg-gradient-to-bl from-primary via-purple-500 to-cyan-500 text-white hover:opacity-90 gap-2"
                >
                  {isSearching ? (
                    <RefreshCw className="h-4 w-4 animate-spin" />
                  ) : (
                    <Search className="h-4 w-4" />
                  )}
                  <span className="hidden sm:inline">{t.search}</span>
                </Button>
              </div>

              {/* Search options */}
              <div className="flex flex-wrap items-center gap-3">
                <div className="flex items-center gap-2">
                  <Hash className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">{t.collection}:</span>
                  <select
                    value={collection}
                    onChange={(e) => setCollection(e.target.value)}
                    className="h-7 text-xs bg-muted/50 border border-border rounded-md px-2 text-foreground"
                  >
                    {(knowledgeStats?.collections?.length ? knowledgeStats.collections : ["knowledge"]).map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <div className="flex items-center gap-2">
                  <Layers className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">{t.topK}:</span>
                  <Input
                    type="number"
                    value={topK}
                    onChange={(e) => setTopK(parseInt(e.target.value) || 5)}
                    className="h-7 w-16 text-xs bg-muted/50 border-border"
                    min={1}
                    max={20}
                    dir="ltr"
                  />
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Knowledge Base Stats */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-5 w-5 text-cyan-400" />
                {t.stats}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-2 sm:grid-cols-3 gap-3">
                <div className="p-3 rounded-lg bg-muted/50 text-center">
                  <Database className="h-5 w-5 text-primary mx-auto mb-1" />
                  <p className="text-lg font-bold text-primary">
                    {knowledgeStats?.totalEntries ?? "—"}
                  </p>
                  <p className="text-[10px] text-muted-foreground">{t.totalEntries}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 text-center">
                  <Layers className="h-5 w-5 text-cyan-400 mx-auto mb-1" />
                  <p className="text-lg font-bold text-cyan-400">
                    {knowledgeStats?.collections.length ?? "—"}
                  </p>
                  <p className="text-[10px] text-muted-foreground">{t.collections}</p>
                </div>
                <div className="p-3 rounded-lg bg-muted/50 text-center col-span-2 sm:col-span-1">
                  <Clock className="h-5 w-5 text-blue-400 mx-auto mb-1" />
                  <p className="text-xs font-medium text-blue-400 truncate">
                    {knowledgeStats?.lastUpdated
                      ? new Date(knowledgeStats.lastUpdated).toLocaleDateString(isArabic ? "ar-SA" : "en-US")
                      : "—"}
                  </p>
                  <p className="text-[10px] text-muted-foreground">{t.lastUpdated}</p>
                </div>
              </div>

              {knowledgeStats?.collections && knowledgeStats.collections.length > 0 && (
                <div className="mt-3">
                  <p className="text-xs text-muted-foreground mb-2">{t.availableCollections}</p>
                  <div className="flex flex-wrap gap-2">
                    {knowledgeStats.collections.map((c) => (
                      <Badge
                        key={c}
                        variant="outline"
                        className={cn(
                          "text-[10px]",
                          c === collection
                            ? "border-primary text-primary bg-primary/10"
                            : "border-border text-muted-foreground"
                        )}
                      >
                        {c}
                      </Badge>
                    ))}
                  </div>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Knowledge Graph */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <Network className="h-5 w-5 text-primary" />
                {t.knowledgeGraph}
              </CardTitle>
            </CardHeader>
            <CardContent>
              <KnowledgeGraph />
            </CardContent>
          </Card>

          {/* Add Knowledge */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <PlusCircle className="h-5 w-5 text-emerald-400" />
                {t.addKnowledge}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <textarea
                value={addText}
                onChange={(e) => setAddText(e.target.value)}
                placeholder={t.addPlaceholder}
                className="w-full h-24 text-sm bg-muted/50 border border-border rounded-lg p-3 resize-none text-foreground placeholder:text-muted-foreground/40 focus:outline-none focus:border-primary/40 focus:ring-1 focus:ring-primary/20 transition-all"
                dir={isArabic ? "rtl" : "ltr"}
              />
              <div className="flex items-center gap-3">
                <div className="flex items-center gap-2">
                  <Database className="h-3.5 w-3.5 text-muted-foreground" />
                  <span className="text-xs text-muted-foreground">{t.collection}:</span>
                  <select
                    value={addCollection}
                    onChange={(e) => setAddCollection(e.target.value)}
                    className="h-7 text-xs bg-muted/50 border border-border rounded-md px-2 text-foreground"
                  >
                    {(knowledgeStats?.collections?.length ? knowledgeStats.collections : ["knowledge"]).map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <Button
                  onClick={handleAddKnowledge}
                  disabled={isAdding || !addText.trim()}
                  size="sm"
                  className="text-xs gap-1 bg-emerald-600 hover:bg-emerald-500 text-white"
                >
                  {isAdding ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <PlusCircle className="h-3 w-3" />
                  )}
                  {t.add}
                </Button>
              </div>
              {addResult && (
                <div className={cn(
                  "flex items-center gap-2 text-xs p-2 rounded-lg",
                  addResult.includes("نجاح") || addResult.includes("success")
                    ? "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                    : "bg-destructive/10 text-destructive border border-destructive/20"
                )}>
                  <CheckCircle2 className="h-3 w-3 shrink-0" />
                  <span>{addResult}</span>
                </div>
              )}
            </CardContent>
          </Card>

          {/* Upload File */}
          <Card className="glass border-0 prism-border overflow-hidden">
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <FileText className="h-5 w-5 text-cyan-400" />
                {t.uploadFile}
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="flex items-center gap-3">
                <div className="flex-1">
                  <label className="flex items-center gap-2 px-3 py-2 rounded-lg border border-dashed border-border bg-muted/30 cursor-pointer hover:bg-muted/50 transition-colors text-sm text-muted-foreground">
                    <FileText className="h-4 w-4 shrink-0" />
                    <span className="truncate">
                      {uploadFile ? uploadFile.name : (isArabic ? "اختار ملف..." : "Choose a file...")}
                    </span>
                    <input
                      type="file"
                      accept=".pdf,.docx,.txt,.md"
                      className="hidden"
                      onChange={(e) => setUploadFile(e.target.files?.[0] || null)}
                    />
                  </label>
                </div>
                <div className="flex items-center gap-2">
                  <Database className="h-3.5 w-3.5 text-muted-foreground" />
                  <select
                    value={uploadCollection}
                    onChange={(e) => setUploadCollection(e.target.value)}
                    className="h-7 text-xs bg-muted/50 border border-border rounded-md px-2 text-foreground"
                  >
                    {(knowledgeStats?.collections?.length ? knowledgeStats.collections : ["knowledge"]).map((c) => (
                      <option key={c} value={c}>{c}</option>
                    ))}
                  </select>
                </div>
                <Button
                  onClick={handleUploadKnowledge}
                  disabled={isUploading || !uploadFile}
                  size="sm"
                  className="text-xs gap-1 bg-cyan-600 hover:bg-cyan-500 text-white whitespace-nowrap"
                >
                  {isUploading ? (
                    <Loader2 className="h-3 w-3 animate-spin" />
                  ) : (
                    <FileText className="h-3 w-3" />
                  )}
                  {t.upload}
                </Button>
              </div>
              {uploadResult && (
                <div className={cn(
                  "flex items-center gap-2 text-xs p-2 rounded-lg",
                  uploadResult.includes("فشل") || uploadResult.includes("fail") || uploadResult.includes("error")
                    ? "bg-destructive/10 text-destructive border border-destructive/20"
                    : "bg-emerald-500/10 text-emerald-400 border border-emerald-500/20"
                )}>
                  <CheckCircle2 className="h-3 w-3 shrink-0" />
                  <span className="truncate">{uploadResult}</span>
                </div>
              )}
              <p className="text-[10px] text-muted-foreground/60">
                {t.supportedFormats}
              </p>
            </CardContent>
          </Card>

          {/* Search Results */}
          {searchResults.length > 0 && (
            <Card className="glass border-0 prism-border overflow-hidden">
              <CardHeader className="pb-3">
                <CardTitle className="flex items-center gap-2 text-base">
                  <Sparkles className="h-5 w-5 text-primary" />
                  {t.results} ({searchResults.length})
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3 max-h-96 overflow-y-auto">
                  {searchResults.map((result, i) => (
                    <div
                      key={result.id}
                      className={cn(
                        "p-4 rounded-lg border transition-colors hover:bg-muted/50",
                        getScoreBg(result.score)
                      )}
                    >
                      <div className="flex items-start justify-between gap-3 mb-2">
                        <div className="flex items-center gap-2">
                          <span className="text-xs text-muted-foreground font-mono">
                            #{i + 1}
                          </span>
                          {result.collection && (
                            <Badge variant="outline" className="text-[9px] border-border">
                              {result.collection}
                            </Badge>
                          )}
                        </div>
                        <div className={cn("flex items-center gap-1 text-xs font-mono", getScoreColor(result.score))}>
                          <div className={cn("h-1.5 w-1.5 rounded-full", result.score >= 0.8 ? "bg-emerald-400" : result.score >= 0.5 ? "bg-yellow-400" : "bg-red-400")} />
                          {(result.score * 100).toFixed(1)}%
                        </div>
                      </div>
                      <p className="text-sm leading-relaxed text-foreground/90">
                        {result.content}
                      </p>
                      {/* Relevance bar */}
                      <div className="mt-2 h-1 rounded-full bg-muted overflow-hidden">
                        <div
                          className={cn(
                            "h-full rounded-full transition-all",
                            result.score >= 0.8
                              ? "bg-emerald-500"
                              : result.score >= 0.5
                              ? "bg-yellow-500"
                              : "bg-red-500"
                          )}
                          style={{ width: `${result.score * 100}%` }}
                        />
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          )}

          {/* Error */}
          {error && (
            <div className="flex items-center gap-2 p-3 rounded-xl bg-destructive/10 border border-destructive/20 text-destructive text-xs max-w-md mx-auto">
              <AlertCircle className="h-4 w-4 shrink-0" />
              <span>{error}</span>
            </div>
          )}

          {/* Empty state */}
          {searchResults.length === 0 && !error && (
            <div className="text-center py-12">
              <Database className="h-12 w-12 mx-auto text-primary/20 mb-3" />
              <p className="text-sm text-muted-foreground">{t.emptyState}</p>
              <p className="text-xs text-muted-foreground mt-1">{t.emptyHint}</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

const knowledgeAr = {
  title: "قاعدة المعرفة",
  semanticSearch: "البحث الدلالي",
  searchPlaceholder: "ابحث في قاعدة المعرفة...",
  search: "بحث",
  collection: "المجموعة",
  topK: "عدد النتائج",
  stats: "إحصائيات قاعدة المعرفة",
  totalEntries: "إجمالي الإدخالات",
  collections: "المجموعات",
  lastUpdated: "آخر تحديث",
  availableCollections: "المجموعات المتاحة",
  results: "النتائج",
  knowledgeGraph: "خريطة المعرفة",
  emptyState: "لا توجد نتائج بحث بعد",
  emptyHint: "استخدم البحث أعلاه للبحث في قاعدة المعرفة",
  apiOnline: "API متصل",
  apiOffline: "API غير متصل",
  addKnowledge: "إضافة معرفة جديدة",
  addPlaceholder: "اكتب النص اللي عاوز تضيفه للمعرفة...",
  add: "إضافة",
  uploadFile: "رفع ملف",
  upload: "رفع",
  supportedFormats: "يدعم PDF, DOCX, TXT, MD — التقطيع والتشفير بيتم تلقائياً",
};

const knowledgeEn = {
  title: "Knowledge Base",
  semanticSearch: "Semantic Search",
  searchPlaceholder: "Search the knowledge base...",
  search: "Search",
  collection: "Collection",
  topK: "Top K",
  stats: "Knowledge Base Stats",
  totalEntries: "Total Entries",
  collections: "Collections",
  lastUpdated: "Last Updated",
  availableCollections: "Available Collections",
  results: "Results",
  knowledgeGraph: "Knowledge Graph",
  emptyState: "No search results yet",
  emptyHint: "Use the search above to query the knowledge base",
  apiOnline: "API Online",
  apiOffline: "API Offline",
  addKnowledge: "Add Knowledge",
  addPlaceholder: "Enter the text you want to add to the knowledge base...",
  add: "Add",
  uploadFile: "Upload File",
  upload: "Upload",
  supportedFormats: "Supports PDF, DOCX, TXT, MD — auto-chunked and embedded",
};
