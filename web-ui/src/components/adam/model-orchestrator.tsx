"use client";

import { useAppStore } from "@/lib/store";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { cn } from "@/lib/utils";
import { X, Brain, Cpu, Shield, Zap, Network, GitBranch, Sparkles, ArrowRight, CheckCircle2 } from "lucide-react";
import { useState } from "react";

const models = [
  { name: "Gemma 4", role: "Orchestrator & Synthesis", roleAr: "التنسيق والتركيب", color: "#8b5cf6", icon: Brain, active: true },
  { name: "DeepSeek", role: "Technical Analysis", roleAr: "التحليل التقني", color: "#06b6d4", icon: Cpu, active: true },
  { name: "Llama Guard", role: "Security & Safety", roleAr: "الأمان والسلامة", color: "#ef4444", icon: Shield, active: true },
  { name: "Nomic Embed", role: "Vector Embeddings", roleAr: "التضمين المتجهي", color: "#10b981", icon: Zap, active: true },
  { name: "Qwen 2.5", role: "Code Generation", roleAr: "توليد الكود", color: "#f59e0b", icon: GitBranch, active: false },
  { name: "Mistral", role: "Reasoning", roleAr: "الاستدلال المنطقي", color: "#ec4899", icon: Network, active: false },
];

const consultationChains = [
  {
    title: "تحليل مشكلة أمنية",
    titleEn: "Security Analysis",
    steps: [
      { model: 2, action: "فحص الطلب", actionEn: "Scan request", duration: "0.3s" },
      { model: 1, action: "تحليل تقني", actionEn: "Technical analysis", duration: "1.2s" },
      { model: 0, action: "صياغة الرد", actionEn: "Synthesize response", duration: "0.8s" },
    ],
  },
  {
    title: "توليد تقرير ذكي",
    titleEn: "Smart Report",
    steps: [
      { model: 3, action: "تضمين المعرفة", actionEn: "Knowledge embedding", duration: "0.5s" },
      { model: 1, action: "تحليل البيانات", actionEn: "Data analysis", duration: "2.1s" },
      { model: 0, action: "صياغة التقرير", actionEn: "Report generation", duration: "1.5s" },
      { model: 2, action: "فحص أمني", actionEn: "Security check", duration: "0.4s" },
    ],
  },
];

export function ModelOrchestrator() {
  const { orchestratorOpen, setOrchestratorOpen, consultationMode, setConsultationMode, settings } = useAppStore();
  const isArabic = settings.language === "ar";
  const [activeChain, setActiveChain] = useState(0);

  if (!orchestratorOpen) return null;

  return (
    <div className="fixed inset-0 z-[80] flex items-center justify-center bg-black/70 backdrop-blur-sm"
      onClick={() => setOrchestratorOpen(false)}>
      <div className="w-full max-w-3xl mx-4" onClick={(e) => e.stopPropagation()}>
        {/* Header */}
        <div className="flex items-center justify-between px-5 py-3 bg-zinc-900/95 border border-zinc-700 rounded-t-xl">
          <div className="flex items-center gap-2.5">
            <div className="h-8 w-8 rounded-lg bg-gradient-to-br from-purple-500/30 to-cyan-500/30 flex items-center justify-center">
              <GitBranch className="h-4 w-4 text-primary" />
            </div>
            <div>
              <h3 className="text-sm font-medium">{isArabic ? "المايسترو — توزيع المهام" : "Maestro — Task Orchestration"}</h3>
              <p className="text-[10px] text-muted-foreground">{isArabic ? "كل موديل يؤدي دوره التخصصي" : "Each model plays its specialized role"}</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            <Button variant={consultationMode ? "secondary" : "ghost"} size="sm"
              className={cn("text-[10px] h-7 gap-1", consultationMode && "bg-primary/15 text-primary border border-primary/30")}
              onClick={() => setConsultationMode(!consultationMode)}>
              <Sparkles className="h-3 w-3" />
              {isArabic ? "اجتماع استشاري" : "Consultation"}
            </Button>
            <Button variant="ghost" size="icon" className="h-6 w-6 text-muted-foreground hover:text-white"
              onClick={() => setOrchestratorOpen(false)}>
              <X className="h-3.5 w-3.5" />
            </Button>
          </div>
        </div>

        {/* Body */}
        <div className="border-x border-b border-zinc-700 rounded-b-xl p-5 space-y-5 max-h-[70vh] overflow-y-auto"
          style={{ backgroundColor: 'rgba(0,0,0,0.9)' }}>
          {/* Model pool */}
          <div>
            <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2.5">
              {isArabic ? "مجمع الموديلات" : "Model Pool"}
            </h4>
            <div className="grid grid-cols-3 gap-2">
              {models.map((m, i) => {
                const Icon = m.icon;
                return (
                  <div key={m.name} className={cn(
                    "p-3 rounded-lg border transition-all",
                    m.active ? "border-zinc-700 bg-zinc-900/50" : "border-zinc-800/50 bg-zinc-900/20 opacity-40"
                  )}>
                    <div className="flex items-center gap-2 mb-1.5">
                      <div className="h-6 w-6 rounded-md flex items-center justify-center" style={{ backgroundColor: `${m.color}20` }}>
                        <Icon className="h-3 w-3" style={{ color: m.color }} />
                      </div>
                      <span className="text-xs font-medium">{m.name}</span>
                      {m.active && <Badge className="text-[7px] px-1 py-0 h-3.5 bg-emerald-500/20 text-emerald-400 border-0">active</Badge>}
                    </div>
                    <p className="text-[9px] text-muted-foreground">{isArabic ? m.roleAr : m.role}</p>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Consultation chains */}
          {consultationMode && (
            <div>
              <h4 className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider mb-2.5">
                {isArabic ? "سلاسل الاستشارة" : "Consultation Chains"}
              </h4>
              <div className="space-y-2">
                {consultationChains.map((chain, ci) => (
                  <div key={ci}
                    className={cn(
                      "p-3 rounded-lg border transition-all cursor-pointer",
                      activeChain === ci ? "border-primary/30 bg-primary/5" : "border-zinc-800 bg-zinc-900/30"
                    )}
                    onClick={() => setActiveChain(ci)}>
                    <p className="text-xs font-medium mb-2">{isArabic ? chain.title : chain.titleEn}</p>
                    <div className="flex items-center gap-1.5 flex-wrap">
                      {chain.steps.map((step, si) => {
                        const model = models[step.model];
                        const ModelIcon = model.icon;
                        return (
                          <div key={si} className="flex items-center gap-1">
                            <div className="flex items-center gap-1 px-2 py-1 rounded-md bg-zinc-800/50 text-[9px]">
                              <ModelIcon className="h-2.5 w-2.5" style={{ color: model.color }} />
                              <span className="text-zinc-300">{isArabic ? step.action : step.actionEn}</span>
                              <span className="text-zinc-600">({step.duration})</span>
                            </div>
                            {si < chain.steps.length - 1 && <ArrowRight className="h-2.5 w-2.5 text-zinc-600" />}
                          </div>
                        );
                      })}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Real-time simulation indicator */}
          {consultationMode && (
            <div className="p-3 rounded-lg bg-gradient-to-r from-purple-500/5 via-cyan-500/5 to-blue-500/5 border border-primary/20">
              <div className="flex items-center gap-2 mb-1">
                <span className="relative flex h-2 w-2">
                  <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-cyan-400 opacity-75" />
                  <span className="relative inline-flex rounded-full h-2 w-2 bg-cyan-500" />
                </span>
                <span className="text-xs font-medium text-cyan-400">
                  {isArabic ? "الاجتماع الاستشاري نشط" : "Consultation Meeting Active"}
                </span>
              </div>
              <p className="text-[10px] text-muted-foreground">
                {isArabic
                  ? "آدم يوزع المهام تلقائياً على الموديلات التخصصية حسب نوع المشكلة"
                  : "Adam automatically routes tasks to specialized models based on problem type"}
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
