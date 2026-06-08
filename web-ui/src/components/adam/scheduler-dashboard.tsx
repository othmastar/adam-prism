"use client";

import { useState, useEffect, useCallback } from "react";
import { useAppStore } from "@/lib/store";
import { getFastApiUrl } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Clock, Plus, Trash2, Play, Calendar, RefreshCw, Timer } from "lucide-react";
import { cn } from "@/lib/utils";

type ScheduledJob = {
  id: string;
  name: string;
  type: string;
  schedule: string;
  next_run?: string;
  enabled: boolean;
};

type TabType = "list" | "cron" | "interval" | "once";

export function SchedulerDashboard() {
  const { settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const url = getFastApiUrl();

  const [jobs, setJobs] = useState<ScheduledJob[]>([]);
  const [loading, setLoading] = useState(true);
  const [tab, setTab] = useState<TabType>("list");

  const [cronId, setCronId] = useState("");
  const [cronExpr, setCronExpr] = useState("");
  const [cronAction, setCronAction] = useState("");
  const [cronName, setCronName] = useState("");

  const [intId, setIntId] = useState("");
  const [intSec, setIntSec] = useState("300");
  const [intAction, setIntAction] = useState("");
  const [intName, setIntName] = useState("");

  const [onceId, setOnceId] = useState("");
  const [onceDt, setOnceDt] = useState("");
  const [onceAction, setOnceAction] = useState("");
  const [onceName, setOnceName] = useState("");

  const [msg, setMsg] = useState<{ type: "ok" | "err"; text: string } | null>(null);

  const fetchJobs = useCallback(async () => {
    setLoading(true);
    try {
      const res = await fetch(`${url}/api/scheduler/jobs`);
      if (res.ok) {
        const data = await res.json();
        setJobs(data.jobs || []);
      }
    } catch {
      // ignore
    } finally {
      setLoading(false);
    }
  }, [url]);

  useEffect(() => { fetchJobs(); }, [fetchJobs]);

  const showMsg = (type: "ok" | "err", text: string) => {
    setMsg({ type, text });
    setTimeout(() => setMsg(null), 3000);
  };

  const deleteJob = async (id: string) => {
    try {
      const res = await fetch(`${url}/api/scheduler/jobs/${id}`, { method: "DELETE" });
      if (res.ok) { showMsg("ok", isArabic ? "تم الحذف" : "Deleted"); fetchJobs(); }
      else showMsg("err", isArabic ? "فشل الحذف" : "Delete failed");
    } catch { showMsg("err", "Error"); }
  };

  const addCron = async () => {
    if (!cronId || !cronExpr || !cronAction) return;
    try {
      const res = await fetch(`${url}/api/scheduler/cron`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: cronId, cron: cronExpr, action: cronAction, name: cronName || cronId }),
      });
      if (res.ok) { showMsg("ok", isArabic ? "تمت الإضافة" : "Added"); setCronId(""); setCronExpr(""); setCronAction(""); setCronName(""); fetchJobs(); setTab("list"); }
      else showMsg("err", isArabic ? "فشل" : "Failed");
    } catch { showMsg("err", "Error"); }
  };

  const addInterval = async () => {
    if (!intId || !intSec || !intAction) return;
    try {
      const res = await fetch(`${url}/api/scheduler/interval`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: intId, seconds: parseInt(intSec), action: intAction, name: intName || intId }),
      });
      if (res.ok) { showMsg("ok", isArabic ? "تمت الإضافة" : "Added"); setIntId(""); setIntSec("300"); setIntAction(""); setIntName(""); fetchJobs(); setTab("list"); }
      else showMsg("err", isArabic ? "فشل" : "Failed");
    } catch { showMsg("err", "Error"); }
  };

  const addOnce = async () => {
    if (!onceId || !onceDt || !onceAction) return;
    try {
      const res = await fetch(`${url}/api/scheduler/once`, {
        method: "POST", headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: onceId, run_at: onceDt, action: onceAction, name: onceName || onceId }),
      });
      if (res.ok) { showMsg("ok", isArabic ? "تمت الإضافة" : "Added"); setOnceId(""); setOnceDt(""); setOnceAction(""); setOnceName(""); fetchJobs(); setTab("list"); }
      else showMsg("err", isArabic ? "فشل" : "Failed");
    } catch { showMsg("err", "Error"); }
  };

  const tabs: { key: TabType; label: string; icon: React.ElementType }[] = [
    { key: "list", label: isArabic ? "المهام" : "Jobs", icon: Clock },
    { key: "cron", label: "Cron", icon: Calendar },
    { key: "interval", label: isArabic ? "دوري" : "Interval", icon: RefreshCw },
    { key: "once", label: isArabic ? "مرة" : "Once", icon: Timer },
  ];

  return (
    <div className="flex-1 overflow-y-auto p-4">
      <div className="max-w-3xl mx-auto space-y-4">
        <div className="flex items-center gap-2 mb-2">
          <Clock className="h-5 w-5 text-primary" />
          <h2 className="text-lg font-semibold">{isArabic ? "جدولة المهام" : "Scheduler"}</h2>
        </div>

        {msg && (
          <div className={cn("px-3 py-2 rounded-lg text-sm", msg.type === "ok" ? "bg-emerald-500/10 text-emerald-400" : "bg-destructive/10 text-destructive")}>
            {msg.text}
          </div>
        )}

        <div className="flex gap-2 flex-wrap">
          {tabs.map((t) => (
            <Button key={t.key} variant={tab === t.key ? "default" : "outline"} size="sm" onClick={() => setTab(t.key)} className="gap-1.5">
              <t.icon className="h-3.5 w-3.5" /> {t.label}
            </Button>
          ))}
        </div>

        {tab === "list" && (
          <div className="space-y-2">
            {loading ? (
              <p className="text-sm text-muted-foreground">{isArabic ? "جاري التحميل..." : "Loading..."}</p>
            ) : jobs.length === 0 ? (
              <p className="text-sm text-muted-foreground">{isArabic ? "لا توجد مهام مجدولة" : "No scheduled jobs"}</p>
            ) : jobs.map((job) => (
              <Card key={job.id} className="p-3 border-border/50 bg-card/50 backdrop-blur-sm">
                <div className="flex items-center justify-between gap-2">
                  <div className="min-w-0 flex-1">
                    <div className="flex items-center gap-2">
                      <span className="text-sm font-medium truncate">{job.name || job.id}</span>
                      <Badge variant="outline" className="text-[10px]">{job.type}</Badge>
                      {job.enabled ? <Badge className="bg-emerald-500/10 text-emerald-400 text-[10px]">{isArabic ? "نشط" : "Active"}</Badge> : <Badge variant="outline" className="text-[10px]">{isArabic ? "متوقف" : "Paused"}</Badge>}
                    </div>
                    <p className="text-xs text-muted-foreground mt-0.5">{job.schedule}</p>
                    {job.next_run && <p className="text-[10px] text-muted-foreground/60">{isArabic ? "التشغيل القادم" : "Next run"}: {job.next_run}</p>}
                  </div>
                  <Button variant="ghost" size="icon" className="h-8 w-8 shrink-0 text-destructive/60 hover:text-destructive" onClick={() => deleteJob(job.id)}>
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </div>
              </Card>
            ))}
          </div>
        )}

        {tab === "cron" && (
          <Card className="p-4 border-border/50 space-y-3">
            <h3 className="text-sm font-medium flex items-center gap-2"><Calendar className="h-4 w-4" /> {isArabic ? "إضافة مهمة Cron" : "Add Cron Job"}</h3>
            <Input placeholder="ID" value={cronId} onChange={(e) => setCronId(e.target.value)} className="text-sm" />
            <Input placeholder={isArabic ? "صيغة Cron (مثال: 0 8 * * *)" : "Cron expression (e.g. 0 8 * * *)"} value={cronExpr} onChange={(e) => setCronExpr(e.target.value)} className="text-sm" />
            <Input placeholder={isArabic ? "الإجراء (مثال: check_email)" : "Action (e.g. check_email)"} value={cronAction} onChange={(e) => setCronAction(e.target.value)} className="text-sm" />
            <Input placeholder={isArabic ? "الاسم (اختياري)" : "Name (optional)"} value={cronName} onChange={(e) => setCronName(e.target.value)} className="text-sm" />
            <Button onClick={addCron} className="w-full gap-1.5"><Plus className="h-4 w-4" /> {isArabic ? "إضافة" : "Add"}</Button>
          </Card>
        )}

        {tab === "interval" && (
          <Card className="p-4 border-border/50 space-y-3">
            <h3 className="text-sm font-medium flex items-center gap-2"><RefreshCw className="h-4 w-4" /> {isArabic ? "إضافة مهمة دورية" : "Add Interval Job"}</h3>
            <Input placeholder="ID" value={intId} onChange={(e) => setIntId(e.target.value)} className="text-sm" />
            <div className="flex gap-2 items-center">
              <Input type="number" placeholder={isArabic ? "عدد الثواني" : "Seconds"} value={intSec} onChange={(e) => setIntSec(e.target.value)} className="text-sm flex-1" />
              <span className="text-xs text-muted-foreground">sec</span>
            </div>
            <Input placeholder={isArabic ? "الإجراء" : "Action"} value={intAction} onChange={(e) => setIntAction(e.target.value)} className="text-sm" />
            <Input placeholder={isArabic ? "الاسم (اختياري)" : "Name (optional)"} value={intName} onChange={(e) => setIntName(e.target.value)} className="text-sm" />
            <Button onClick={addInterval} className="w-full gap-1.5"><Plus className="h-4 w-4" /> {isArabic ? "إضافة" : "Add"}</Button>
          </Card>
        )}

        {tab === "once" && (
          <Card className="p-4 border-border/50 space-y-3">
            <h3 className="text-sm font-medium flex items-center gap-2"><Timer className="h-4 w-4" /> {isArabic ? "إضافة مهمة لمرة واحدة" : "Add One-time Job"}</h3>
            <Input placeholder="ID" value={onceId} onChange={(e) => setOnceId(e.target.value)} className="text-sm" />
            <Input type="datetime-local" value={onceDt} onChange={(e) => setOnceDt(e.target.value)} className="text-sm" />
            <Input placeholder={isArabic ? "الإجراء" : "Action"} value={onceAction} onChange={(e) => setOnceAction(e.target.value)} className="text-sm" />
            <Input placeholder={isArabic ? "الاسم (اختياري)" : "Name (optional)"} value={onceName} onChange={(e) => setOnceName(e.target.value)} className="text-sm" />
            <Button onClick={addOnce} className="w-full gap-1.5"><Plus className="h-4 w-4" /> {isArabic ? "إضافة" : "Add"}</Button>
          </Card>
        )}
      </div>
    </div>
  );
}
