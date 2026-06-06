"use client";

import { useAppStore } from "@/lib/store";
import { Shield, ShieldCheck } from "lucide-react";
import { cn } from "@/lib/utils";

export function ShieldPulse() {
  const { shieldActive } = useAppStore();

  return (
    <div className="relative flex items-center justify-center">
      {shieldActive && (
        <span className="absolute inline-flex h-6 w-6 rounded-full bg-emerald-400 opacity-30 animate-ping" />
      )}
      <div
        className={cn(
          "h-6 w-6 rounded-full flex items-center justify-center transition-all duration-500",
          shieldActive
            ? "bg-emerald-500/20 text-emerald-400"
            : "bg-muted/20 text-muted-foreground"
        )}
      >
        {shieldActive ? (
          <ShieldCheck className="h-3.5 w-3.5" />
        ) : (
          <Shield className="h-3.5 w-3.5" />
        )}
      </div>
    </div>
  );
}
