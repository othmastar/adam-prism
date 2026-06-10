"use client";

import { useState, useEffect, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { getFastApiUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Package, Upload, Trash2, RefreshCw } from "lucide-react";
import { cn } from "@/lib/utils";

type PluginInfo = {
  name: string;
  version?: string;
  description?: string;
  enabled: boolean;
};

export function PluginManager() {
  const { settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const url = getFastApiUrl();

  const [plugins, setPlugins] = useState<PluginInfo[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadPath, setLoadPath] = useState("");
  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const fetchPlugins = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${url}/api/plugins`);
      if (res.ok) {
        const data = await res.json();
        setPlugins(data.plugins || []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => { fetchPlugins(); }, [fetchPlugins]);

  const showMsg = (type: "ok" | "err", text: string) => {
    setMsg({ type, text });
    setTimeout(() => setMsg(null), 3000);
  };

  const loadPlugin = async () => {
    if (!loadPath.trim()) return;
    try {
      const res = await fetch(`${url}/api/plugins/load`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ path: loadPath.trim() }),
      });
      if (res.ok) { showMsg("ok", isArabic ? "تم تحميل الإضافة" : "Plugin loaded"); setLoadPath(""); fetchPlugins(); }
      else { const d = await res.json(); showMsg("err", d.detail || "Failed"); }
    } catch { showMsg("err", "Error"); }
  };

  const unloadPlugin = async (name: string) => {
    try {
      const res = await fetch(`${url}/api/plugins/${name}`, { method: "DELETE" });
      if (res.ok) { showMsg("ok", isArabic ? "تم إلغاء التحميل" : "Plugin unloaded"); fetchPlugins(); }
      else showMsg("err", isArabic ? "فشل" : "Failed");
    } catch { showMsg("err", "Error"); }
  };

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Package className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">{isArabic ? "إدارة الإضافات" : "Plugin Manager"}</h2>
          <Button variant="ghost" size="icon" className="h-7 w-7 ml-auto" onClick={fetchPlugins}>
            <RefreshCw className={cn("h-4 w-4", loading && "animate-spin")} />
          </Button>
        </div>

        {msg && (
          <div className={cn("px-3 py-2 rounded-lg text-sm", msg.type === "ok" ? "bg-emerald-500/10 text-emerald-400" : "bg-destructive/10 text-destructive")}>
            {msg.text}
          </div>
        )}

        <Card className="p-4 border-border/50 space-y-3">
          <h3 className="text-sm font-medium flex items-center gap-2"><Upload className="h-4 w-4" /> {isArabic ? "تحميل إضافة" : "Load Plugin"}</h3>
          <div className="flex gap-2">
            <Input
              placeholder={isArabic ? "مسار الإضافة" : "Plugin path"}
              value={loadPath}
              onChange={(e) => setLoadPath(e.target.value)}
              className="text-sm flex-1"
              onKeyDown={(e) => e.key === "Enter" && loadPlugin()}
            />
            <Button onClick={loadPlugin} size="sm" className="shrink-0 gap-1.5">
              <Upload className="h-4 w-4" /> {isArabic ? "تحميل" : "Load"}
            </Button>
          </div>
        </Card>

        <div className="space-y-2">
          {loading ? (
            <p className="text-sm text-muted-foreground">{isArabic ? "جاري التحميل..." : "Loading..."}</p>
          ) : plugins.length === 0 ? (
            <p className="text-sm text-muted-foreground">{isArabic ? "لا توجد إضافات محملة" : "No plugins loaded"}</p>
          ) : plugins.map((plugin) => (
            <Card key={plugin.name} className="p-3 border-border/50 bg-card/50 backdrop-blur-sm">
              <div className="flex items-center justify-between gap-2">
                <div className="min-w-0 flex-1">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium truncate">{plugin.name}</span>
                    {plugin.version && <span className="text-[10px] text-muted-foreground/60">v{plugin.version}</span>}
                    <Badge className={cn("text-[10px]", plugin.enabled ? "bg-emerald-500/10 text-emerald-400" : "bg-muted/50 text-muted-foreground")}>
                      {plugin.enabled ? (isArabic ? "نشط" : "Active") : (isArabic ? "متوقف" : "Inactive")}
                    </Badge>
                  </div>
                  {plugin.description && <p className="text-xs text-muted-foreground mt-0.5">{plugin.description}</p>}
                </div>
                <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-destructive/60 hover:text-destructive" onClick={() => unloadPlugin(plugin.name)}>
                  <Trash2 className="h-4 w-4" />
                </Button>
              </div>
            </Card>
          ))}
        </div>
      </div>
    </div>
  );
}
