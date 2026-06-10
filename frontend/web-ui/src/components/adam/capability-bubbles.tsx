"use client";

import { useAppStore } from "@/lib/store";
import { cn } from "@/lib/utils";
import {
  Sparkles,
  Brain,
  Globe,
  Shield,
  Zap,
  TrendingUp,
  Users,
  MessageSquare,
  Eye,
  GripHorizontal,
  Bug,
  Monitor,
  BarChart3,
} from "lucide-react";

export type Capability = {
  id: string;
  icon: React.ElementType;
  labelAr: string;
  labelEn: string;
  descriptionAr: string;
  descriptionEn: string;
  color: string;
  prompt: string;
  gradient: string;
};

const capabilities: Capability[] = [
  {
    id: "decode",
    icon: Shield,
    labelAr: "فك التشفير",
    labelEn: "Decode",
    descriptionAr: "فك شفرة النصوص والرموز الغامضة",
    descriptionEn: "Decode ciphers and cryptic messages",
    color: "#8b5cf6",
    gradient: "from-purple-600/30 via-purple-500/20 to-fuchsia-600/30",
    prompt: "فك لي هذه الشفرة أو الرمز المشفر:",
  },
  {
    id: "market-analysis",
    icon: TrendingUp,
    labelAr: "تحليل سوقي",
    labelEn: "Market Analysis",
    descriptionAr: "تحليل أسواق خيالي وتوقع الاتجاهات",
    descriptionEn: "Fantastical market analysis and trend prediction",
    color: "#06b6d4",
    gradient: "from-cyan-600/30 via-cyan-500/20 to-blue-600/30",
    prompt: "حلل لي السوق بشكل خيالي وتوقع الاتجاهات:",
  },
  {
    id: "brand-identity",
    icon: Eye,
    labelAr: "هوية العلامة",
    labelEn: "Brand Identity",
    descriptionAr: "بناء هوية علامة تجارية من الصفر",
    descriptionEn: "Build complete brand identity from scratch",
    color: "#f59e0b",
    gradient: "from-amber-600/30 via-amber-500/20 to-orange-600/30",
    prompt: "صمم لي هوية علامة تجارية متكاملة:",
  },
  {
    id: "global-trade",
    icon: BarChart3,
    labelAr: "حركة التجارة العالمية",
    labelEn: "Global Trade Trends",
    descriptionAr: "دراسة حركة التجارة العالمية وتحليل النيش الطاغي",
    descriptionEn: "Global trade movement analysis and dominant niche research",
    color: "#14b8a6",
    gradient: "from-teal-600/30 via-teal-500/20 to-emerald-600/30",
    prompt: "حلل حركة التجارة العالمية والنيش الطاغي:",
  },
  {
    id: "pentest",
    icon: Bug,
    labelAr: "اختبار أمان الأنظمة",
    labelEn: "Penetration Test",
    descriptionAr: "اختبار اختراق للأنظمة والكشف عن الثغرات الأمنية",
    descriptionEn: "Penetration testing and vulnerability discovery",
    color: "#ef4444",
    gradient: "from-red-600/30 via-red-500/20 to-rose-600/30",
    prompt: "اختبر أمان النظام وابحث عن الثغرات:",
  },
  {
    id: "remote-control",
    icon: Monitor,
    labelAr: "تحكم عن بعد",
    labelEn: "Remote Control",
    descriptionAr: "التحكم في الأجهزة عن بعد وإدارة الأنظمة",
    descriptionEn: "Remote device control and system management",
    color: "#6366f1",
    gradient: "from-indigo-600/30 via-indigo-500/20 to-violet-600/30",
    prompt: "تحكم في الجهاز التالي عن بعد:",
  },
  {
    id: "viral",
    icon: Zap,
    labelAr: "انتشار فيروسي",
    labelEn: "Viral Growth",
    descriptionAr: "تصميم حملات انتشار فيروسي خيالي",
    descriptionEn: "Design fantastical viral growth campaigns",
    color: "#f97316",
    gradient: "from-orange-600/30 via-orange-500/20 to-red-600/30",
    prompt: "صمم لي حملة انتشار فيروسي مبهرة:",
  },
  {
    id: "global",
    icon: Globe,
    labelAr: "توسع عالمي",
    labelEn: "Global Expansion",
    descriptionAr: "استراتيجيات توسع عالمي في أسواق خيالية",
    descriptionEn: "Global expansion strategies in fantasy markets",
    color: "#a855f7",
    gradient: "from-violet-600/30 via-violet-500/20 to-purple-600/30",
    prompt: "ضع لي خطة توسع عالمي في أسواق خيالية:",
  },
];

export function CapabilityBubbles({ onSelect }: { onSelect: (text: string) => void }) {
  const { settings, capabilityUseCount, incrementCapabilityUse, setActiveCapability, activeCapability } = useAppStore();
  const isArabic = settings.language === "ar";

  return (
    <div className="w-full max-w-2xl mx-auto px-4" dir={isArabic ? "rtl" : "ltr"}>
      {/* Section header */}
      <div className="text-center mb-5">
        <div className="inline-flex items-center gap-2 px-4 py-1.5 rounded-full glass border border-primary/20 mb-3">
          <Sparkles className="h-3.5 w-3.5 text-primary" />
          <span className="text-[11px] text-muted-foreground">
            {isArabic ? "قدرات آدم الخيالية" : "Adam's Imaginary Powers"}
          </span>
        </div>
      </div>

      {/* Bubbles grid */}
      <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
        {capabilities.map((cap, i) => {
          const Icon = cap.icon;
          const label = isArabic ? cap.labelAr : cap.labelEn;
          const desc = isArabic ? cap.descriptionAr : cap.descriptionEn;
          return (
            <button
              key={cap.id}
              onClick={() => {
                onSelect(cap.prompt);
                incrementCapabilityUse(cap.id);
                setActiveCapability(cap.id);
                setTimeout(() => setActiveCapability(null), 3000);
              }}
              className={cn(
                "capability-bubble group relative overflow-hidden rounded-xl p-3 text-right",
                "border transition-all duration-300 ease-out cursor-pointer",
                `bg-gradient-to-br ${cap.gradient}`,
                "hover:shadow-lg hover:shadow-purple-500/10",
                `stagger-fade-in stagger-${Math.min(i + 1, 8)}`,
                activeCapability === cap.id
                  ? "border-primary/60 shadow-lg shadow-purple-500/20 scale-[1.03]"
                  : "border-transparent hover:border-primary/30"
              )}
              style={{
                animationDelay: `${i * 80}ms`,
                borderColor: activeCapability === cap.id ? `${cap.color}80` : `${cap.color}20`,
              }}
            >
              {/* Hover glow effect */}
              <div
                className="absolute inset-0 opacity-0 group-hover:opacity-100 transition-opacity duration-500 rounded-xl"
                style={{
                  background: `radial-gradient(600px circle at var(--mouse-x, 50%) var(--mouse-y, 50%), ${cap.color}15, transparent 40%)`,
                }}
              />

              {/* Icon */}
              <div
                className="h-9 w-9 rounded-lg flex items-center justify-center mb-2 relative z-10 transition-transform group-hover:scale-110 group-hover:rotate-3"
                style={{ backgroundColor: `${cap.color}20` }}
              >
                <Icon className="h-4 w-4" style={{ color: cap.color }} />
              </div>

              {/* Label */}
              <p className="text-xs font-semibold text-foreground relative z-10 mb-0.5">{label}</p>

              {/* Description */}
              <p className="text-[9px] text-muted-foreground/70 leading-relaxed relative z-10 line-clamp-2">
                {desc}
              </p>

              {/* Usage count badge */}
              {(capabilityUseCount[cap.id] ?? 0) > 0 && (
                <div
                  className="absolute -top-1.5 -end-1.5 h-4 min-w-[14px] px-1 rounded-full flex items-center justify-center z-20 text-[7px] font-bold text-white"
                  style={{ backgroundColor: cap.color }}
                >
                  {capabilityUseCount[cap.id]}
                </div>
              )}

              {/* Corner sparkle */}
              <div
                className="absolute -top-1 -end-1 h-5 w-5 opacity-0 group-hover:opacity-100 transition-opacity duration-300"
              >
                <Sparkles className="h-3 w-3" style={{ color: cap.color }} />
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
