/**
 * LTMMemoryPanel — لوحة الذاكرة طويلة المدى (Vector embeddings)
 * ===============================================================
 * تضيف لـ frontend القدرة على:
 * - عرض الذكريات المخزنة
 * - بحث hybrid (BM25 + Vector)
 * - إضافة ذكريات يدوياً
 * - حذف ذكريات
 * - عرض إحصائيات
 *
 * Usage:
 *   <LTMMemoryPanel />
 * أو ضيفها في chat-sidebar كـ tab
 */

"use client";

import { useState, useEffect, useCallback } from "react";
import {
  searchLTM,
  storeLTM,
  deleteLTM,
  getLTMStats,
  getLTMHealth,
  type LTMResult,
} from "@/lib/api-enhanced";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Trash2,
  Search,
  Plus,
  Brain,
  Activity,
  AlertCircle,
} from "lucide-react";
import { useToast } from "@/hooks/use-toast";

export function LTMMemoryPanel() {
  const [results, setResults] = useState<LTMResult[]>([]);
  const [query, setQuery] = useState("");
  const [stats, setStats] = useState<any>(null);
  const [health, setHealth] = useState<any>(null);
  const [loading, setLoading] = useState(false);
  const [showAdd, setShowAdd] = useState(false);
  const [newContent, setNewContent] = useState("");
  const [newType, setNewType] = useState("semantic");
  const [newPriority, setNewPriority] = useState(3);
  const { toast } = useToast();

  const loadStats = useCallback(async () => {
    try {
      const [s, h] = await Promise.all([getLTMStats(), getLTMHealth()]);
      setStats(s);
      setHealth(h);
    } catch (e) {
      console.error("Failed to load LTM stats:", e);
    }
  }, []);

  useEffect(() => {
    loadStats();
  }, [loadStats]);

  const handleSearch = useCallback(async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const data = await searchLTM(query, 10);
      setResults(data.results);
    } catch (e) {
      toast({
        title: "خطأ في البحث",
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    } finally {
      setLoading(false);
    }
  }, [query, toast]);

  const handleStore = useCallback(async () => {
    if (!newContent.trim()) return;
    try {
      await storeLTM(newContent, newType, newPriority);
      toast({ title: "تم الحفظ", description: "الذكرى اتخزنت في LTM" });
      setNewContent("");
      setShowAdd(false);
      loadStats();
    } catch (e) {
      toast({
        title: "فشل الحفظ",
        description: e instanceof Error ? e.message : String(e),
        variant: "destructive",
      });
    }
  }, [newContent, newType, newPriority, toast, loadStats]);

  const handleDelete = useCallback(
    async (id: number) => {
      try {
        await deleteLTM(id);
        setResults((prev) => prev.filter((r) => r.id !== id));
        toast({ title: "تم الحذف" });
        loadStats();
      } catch (e) {
        toast({
          title: "فشل الحذف",
          description: e instanceof Error ? e.message : String(e),
          variant: "destructive",
        });
      }
    },
    [toast, loadStats],
  );

  return (
    <Card className="h-full">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Brain className="h-5 w-5" />
          الذاكرة طويلة المدى (Vector)
        </CardTitle>
        <CardDescription>
          بحث هجين (BM25 + Vector embeddings) — يتذكر كل المحادثات
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Health & Stats */}
        <div className="grid grid-cols-2 gap-2 text-xs">
          <div className="flex items-center gap-2">
            <Activity className="h-3 w-3" />
            <span>DB:</span>
            <Badge variant={health?.db_connected ? "default" : "destructive"}>
              {health?.db_connected ? "متصل" : "غير متصل"}
            </Badge>
          </div>
          <div className="flex items-center gap-2">
            <Activity className="h-3 w-3" />
            <span>Embeddings:</span>
            <Badge variant={health?.embedding_available ? "default" : "secondary"}>
              {health?.embedding_available ? "متاح" : "غير متاح"}
            </Badge>
          </div>
          <div>الإجمالي: {stats?.total || 0}</div>
          <div>بـ embeddings: {stats?.with_embeddings || 0}</div>
        </div>

        {health && !health.embedding_available && (
          <div className="flex items-start gap-2 p-2 rounded bg-yellow-50 border border-yellow-200 text-xs">
            <AlertCircle className="h-4 w-4 flex-shrink-0 mt-0.5" />
            <div>
              <p className="font-medium">Embeddings مش متاح</p>
              <p className="text-muted-foreground">
                شغّل: <code className="bg-muted px-1 rounded">ollama pull nomic-embed-text</code>
              </p>
            </div>
          </div>
        )}

        {/* Search */}
        <div className="flex gap-2">
          <Input
            placeholder="ابحث في الذكريات..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === "Enter" && handleSearch()}
          />
          <Button onClick={handleSearch} disabled={loading} size="icon">
            <Search className="h-4 w-4" />
          </Button>
          <Button onClick={() => setShowAdd(!showAdd)} size="icon" variant="outline">
            <Plus className="h-4 w-4" />
          </Button>
        </div>

        {/* Add new memory */}
        {showAdd && (
          <div className="space-y-2 p-3 rounded border bg-muted/50">
            <Textarea
              placeholder="اكتب الذكرى..."
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              rows={3}
            />
            <div className="flex gap-2">
              <select
                value={newType}
                onChange={(e) => setNewType(e.target.value)}
                className="text-xs px-2 py-1 rounded border"
              >
                <option value="semantic">semantic</option>
                <option value="episodic">episodic</option>
                <option value="procedural">procedural</option>
                <option value="preference">preference</option>
              </select>
              <select
                value={newPriority}
                onChange={(e) => setNewPriority(Number(e.target.value))}
                className="text-xs px-2 py-1 rounded border"
              >
                <option value={1}>أولوية 1</option>
                <option value={2}>أولوية 2</option>
                <option value={3}>أولوية 3</option>
                <option value={4}>أولوية 4</option>
                <option value={5}>أولوية 5</option>
              </select>
              <Button onClick={handleStore} size="sm" className="ml-auto">
                حفظ
              </Button>
            </div>
          </div>
        )}

        {/* Results */}
        <ScrollArea className="h-[400px]">
          {results.length === 0 ? (
            <p className="text-center text-muted-foreground text-sm py-8">
              {query ? "لا توجد نتائج" : "ابحث لعرض الذكريات"}
            </p>
          ) : (
            <div className="space-y-2">
              {results.map((r) => (
                <div
                  key={r.id}
                  className="p-3 rounded border bg-card hover:bg-accent/50 transition-colors"
                >
                  <div className="flex items-start justify-between gap-2 mb-2">
                    <Badge variant="outline" className="text-xs">
                      {r.type}
                    </Badge>
                    <div className="flex items-center gap-2 text-xs">
                      <span className="text-muted-foreground">
                        priority: {r.priority}
                      </span>
                      <span className="text-muted-foreground">
                        score: {r.score}
                      </span>
                      <Button
                        size="icon"
                        variant="ghost"
                        className="h-6 w-6"
                        onClick={() => handleDelete(r.id)}
                      >
                        <Trash2 className="h-3 w-3" />
                      </Button>
                    </div>
                  </div>
                  <p className="text-sm">{r.content}</p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-muted-foreground">
                    <span>BM25: {r.bm25_score}</span>
                    <span>Vector: {r.vector_score}</span>
                    <span>access: {r.access_count}</span>
                  </div>
                </div>
              ))}
            </div>
          )}
        </ScrollArea>
      </CardContent>
    </Card>
  );
}
