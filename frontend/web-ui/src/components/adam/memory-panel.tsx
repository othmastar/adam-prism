"use client";

import { useState, useEffect, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { getFastApiUrl, fetchMemoryStats } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Card } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Database, Brain, BookOpen, Layers, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

type MemoryStats = {
  short_term_count: number;
  episodic_count: number;
  collections: string[];
};

export function MemoryPanel() {
  const { settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const [stats, setStats] = useState<MemoryStats | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchStats = useCallback(async () => {
    setLoading(true);
    try {
      const data = await fetchMemoryStats();
      setStats(data as MemoryStats);
    } catch {
      setStats(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => { fetchStats(); }, [fetchStats]);

  const items = [
    { icon: Brain, label: isArabic ? "ذاكرة قصيرة" : "Short-term", value: stats?.short_term_count ?? 0, color: "text-cyan-400" },
    { icon: BookOpen, label: isArabic ? "ذاكرة أحداث" : "Episodic", value: stats?.episodic_count ?? 0, color: "text-purple-400" },
    { icon: Layers, label: isArabic ? "المجموعات" : "Collections", value: stats?.collections?.length ?? 0, color: "text-emerald-400" },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Database className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">{isArabic ? "الذاكرة" : "Memory"}</h2>
          <Button variant="ghost" size="icon" className="h-7 w-7 ml-auto" onClick={fetchStats}>
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>

        {loading && !stats ? (
          <p className="text-sm text-muted-foreground">{isArabic ? "جاري التحميل..." : "Loading..."}</p>
        ) : !stats ? (
          <p className="text-sm text-muted-foreground">{isArabic ? "الذاكرة غير متصلة" : "Memory not connected"}</p>
        ) : (
          <>
            <div className="grid grid-cols-3 gap-3">
              {items.map((item) => (
                <Card key={item.label} className="p-4 border-border/50 bg-card/50 backdrop-blur-sm text-center">
                  <item.icon className={cn("h-6 w-6 mx-auto mb-2", item.color)} />
                  <p className="text-2xl font-bold">{item.value}</p>
                  <p className="text-xs text-muted-foreground mt-1">{item.label}</p>
                </Card>
              ))}
            </div>

            <Card className="p-4 border-border/50">
              <h3 className="text-sm font-medium mb-3 flex items-center gap-2">
                <Layers className="h-4 w-4 text-primary" />
                {isArabic ? "المجموعات" : "Collections"}
              </h3>
              {stats.collections.length === 0 ? (
                <p className="text-xs text-muted-foreground">{isArabic ? "لا توجد مجموعات" : "No collections"}</p>
              ) : (
                <div className="flex flex-wrap gap-2">
                  {stats.collections.map((col) => (
                    <Badge key={col} variant="outline" className="text-xs border-primary/30 text-primary bg-primary/5">
                      {col}
                    </Badge>
                  ))}
                </div>
              )}
            </Card>
          </>
        )}
      </div>
    </div>
  );
}
