"use client";

import { useAppStore, ProcessingStep } from "@/lib/store";
import { useEffect, useRef, useState } from "react";

const stepLabels: Record<string, string> = {
  استقبال: "[SYSTEM] Receiving input...",
  "فحص الأمان": "[SECURITY] Scanning request...",
  "تحليل القصد": "[ANALYSIS] Analyzing intent...",
  "بناء السياق": "[CONTEXT] Building context...",
  "البحث في الذاكرة": "[MEMORY] Searching knowledge...",
  التوليد: "[GEN] Generating response...",
  "تنفيذ أداة": "[TOOL] Executing action...",
  "التقييم الأخلاقي": "[ETHICS] Evaluating...",
  "التسجيل والحفظ": "[SAVE] Persisting...",
  "اكتمال الدورة": "[DONE] Cycle complete",
};

export function ActionTrace() {
  const { isStreaming, processingSteps } = useAppStore();
  const [visible, setVisible] = useState(false);
  const [traceText, setTraceText] = useState("");
  const hideTimer = useRef<ReturnType<typeof setTimeout>>();

  useEffect(() => {
    if (!isStreaming) {
      setVisible(false);
      return;
    }

    const running = processingSteps.filter((s) => s.status === "running").pop();
    const latest = processingSteps.filter((s) => s.status === "done").pop();

    let nextText = "";
    if (running) {
      nextText = stepLabels[running.step] || `[SYSTEM] ${running.step}...`;
    } else if (latest) {
      const label = stepLabels[latest.step];
      if (label) {
        nextText = label.includes("Done")
          ? `${label}`
          : `${label.replace("...", "")}... Done.`;
      }
    } else {
      nextText = "[SYSTEM] Processing...";
    }

    if (nextText) {
      setTraceText(nextText);
      setVisible(true);
      clearTimeout(hideTimer.current);
      hideTimer.current = setTimeout(() => setVisible(false), 2500);
    }
  }, [processingSteps, isStreaming]);

  useEffect(() => {
    return () => clearTimeout(hideTimer.current);
  }, []);

  if (!visible && !isStreaming) return null;

  return (
    <div
      className="fixed bottom-16 left-4 z-[70] max-w-[280px] transition-all duration-300"
      style={{
        opacity: visible || isStreaming ? 1 : 0,
        transform: `translateY(${visible || isStreaming ? 0 : 10}px)`,
      }}
    >
      <div className="backdrop-blur-sm border border-zinc-700/50 rounded-lg px-3 py-1.5 font-mono text-[10px] text-emerald-400/90 shadow-lg" style={{ backgroundColor: 'rgba(0,0,0,0.8)' }}>
        <span className="animate-pulse me-1">▸</span>
        {traceText || "[SYSTEM] Idle..."}
      </div>
    </div>
  );
}
