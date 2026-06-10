"use client";

import { useAppStore, ProcessingStep } from "@/lib/store";
import { ScrollArea } from "@/components/ui/scroll-area";
import { Badge } from "@/components/ui/badge";
import {
  ShieldCheck,
  Brain,
  FileSearch,
  Database,
  Sparkles,
  Scale,
  BookOpen,
  Save,
  CheckCircle2,
  Clock,
  Loader2,
  AlertTriangle,
  XCircle,
} from "lucide-react";
import { cn } from "@/lib/utils";

const stepConfig: Record<string, { icon: React.ElementType; labelAr: string; labelEn: string; color: string }> = {
  استقبال: { icon: Brain, labelAr: "استقبال", labelEn: "Reception", color: "#8b5cf6" },
  "فحص الأمان": { icon: ShieldCheck, labelAr: "فحص الأمان", labelEn: "Security Check", color: "#ef4444" },
  "تحليل القصد": { icon: Brain, labelAr: "تحليل القصد", labelEn: "Intent Analysis", color: "#f59e0b" },
  "بناء السياق": { icon: FileSearch, labelAr: "بناء السياق", labelEn: "Context Building", color: "#3b82f6" },
  "البحث في الذاكرة": { icon: Database, labelAr: "البحث في الذاكرة", labelEn: "Memory Search", color: "#06b6d4" },
  التوليد: { icon: Sparkles, labelAr: "التوليد", labelEn: "Generation", color: "#10b981" },
  "التقييم الأخلاقي": { icon: Scale, labelAr: "التقييم الأخلاقي", labelEn: "Ethics Evaluation", color: "#ec4899" },
  "التسجيل في الدفتر": { icon: BookOpen, labelAr: "التسجيل في الدفتر", labelEn: "Notebook Recording", color: "#a855f7" },
  "الحفظ في الذاكرة": { icon: Save, labelAr: "الحفظ في الذاكرة", labelEn: "Memory Save", color: "#14b8a6" },
  "اكتمال الدورة": { icon: CheckCircle2, labelAr: "اكتمال الدورة", labelEn: "Cycle Complete", color: "#22c55e" },
};

function StepIcon({ status }: { status: string }) {
  if (status === "running") return <Loader2 className="h-4 w-4 animate-spin text-amber-400" />;
  if (status === "done") return <CheckCircle2 className="h-4 w-4 text-emerald-400" />;
  if (status === "blocked") return <XCircle className="h-4 w-4 text-red-400" />;
  return <AlertTriangle className="h-4 w-4 text-amber-400" />;
}

function StepRow({ step, isLatest }: { step: ProcessingStep; isLatest: boolean }) {
  const { settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const config = stepConfig[step.step];
  const Icon = config?.icon || Brain;
  const label = isArabic ? (config?.labelAr || step.step) : (config?.labelEn || step.step);
  const color = config?.color || "#8b5cf6";

  return (
    <div
      className={cn(
        "flex items-center gap-3 px-3 py-2.5 rounded-lg transition-all",
        step.status === "running" && "bg-primary/5 border border-primary/20",
        step.status === "done" && "text-muted-foreground",
        step.status === "blocked" && "bg-destructive/10",
        isLatest && step.status === "running" && "animate-pulse-glow"
      )}
    >
      <div
        className="h-8 w-8 rounded-lg flex items-center justify-center shrink-0"
        style={{ backgroundColor: `${color}20` }}
      >
        {step.status === "running" ? (
          <Loader2 className="h-4 w-4 animate-spin" style={{ color }} />
        ) : (
          <Icon className="h-4 w-4" style={{ color }} />
        )}
      </div>
      <div className="flex-1 min-w-0">
        <div className="flex items-center gap-2">
          <span className="text-sm font-medium">{label}</span>
          {step.status === "running" && (
            <span className="text-[10px] text-amber-400 animate-pulse">⏳</span>
          )}
        </div>
        {step.details && Object.keys(step.details).length > 0 && (
          <div className="text-[10px] text-muted-foreground mt-0.5">
            {Object.entries(step.details).map(([k, v]) => (
              <span key={k} className="ml-2">{k}: {String(v)}</span>
            ))}
          </div>
        )}
      </div>
      <Badge
        variant="outline"
        className={cn(
          "text-[9px] shrink-0",
          step.status === "running" && "border-amber-500/30 text-amber-400",
          step.status === "done" && "border-emerald-500/30 text-emerald-400",
          step.status === "blocked" && "border-red-500/30 text-red-400"
        )}
      >
        {step.status === "running" ? (isArabic ? "جاري" : "Running") :
         step.status === "done" ? (isArabic ? "تم" : "Done") :
         step.status === "blocked" ? (isArabic ? "مرفوض" : "Blocked") : step.status}
      </Badge>
    </div>
  );
}

export function PipelineMonitor() {
  const { processingSteps, settings, systemHealth } = useAppStore();
  const isArabic = settings.language === "ar";
  const currentCycleSteps = processingSteps.filter(s => s.cycle === (processingSteps.length > 0 ? processingSteps[processingSteps.length - 1].cycle : 0));

  if (processingSteps.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-40 text-center p-6">
        <Brain className="h-10 w-10 text-primary/30 mb-3" />
        <p className="text-sm text-muted-foreground">
          {isArabic ? "لا توجد معالجة حالية. أرسل رسالة لبدء دورة معالجة." : "No active processing. Send a message to start a processing cycle."}
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-1">
      <div className="flex items-center justify-between px-1 mb-2">
        <div className="flex items-center gap-2">
          <Clock className="h-3.5 w-3.5 text-muted-foreground" />
          <span className="text-[10px] text-muted-foreground">
            {isArabic ? `الدورة ${currentCycleSteps[0]?.cycle || ""}` : `Cycle ${currentCycleSteps[0]?.cycle || ""}`}
          </span>
        </div>
        {currentCycleSteps.some(s => s.status === "running") && (
          <Badge variant="outline" className="text-[9px] border-amber-500/30 text-amber-400 animate-pulse">
            <Loader2 className="h-3 w-3 animate-spin ml-1" />
            {isArabic ? "قيد المعالجة" : "Processing"}
          </Badge>
        )}
      </div>
      <div className="space-y-1">
        {currentCycleSteps.map((step, i) => (
          <StepRow key={`${step.step}-${i}`} step={step} isLatest={i === currentCycleSteps.length - 1} />
        ))}
      </div>
    </div>
  );
}
