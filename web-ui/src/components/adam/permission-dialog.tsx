"use client";

import { useAppStore } from "@/lib/store";
import { respondPermission } from "@/lib/api";
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
} from "@/components/ui/alert-dialog";
import { Button } from "@/components/ui/button";
import { Shield, ShieldOff, Info } from "lucide-react";
import { useState } from "react";

export function PermissionDialog() {
  const { permissionPending, setPermissionPending, settings } = useAppStore();
  const [loading, setLoading] = useState(false);

  const isArabic = settings.language === "ar";

  const handleRespond = async (approve: boolean) => {
    if (!permissionPending) return;
    setLoading(true);
    try {
      const level = approve ? permissionPending.level : "once";
      await respondPermission(approve, level);
      setPermissionPending(null);
    } catch {
      // ignore
    }
    setLoading(false);
  };

  if (!permissionPending) return null;

  return (
    <AlertDialog open={!!permissionPending}>
      <AlertDialogContent className="border-border/50 bg-card/95 backdrop-blur-xl max-w-md">
        <AlertDialogHeader>
          <AlertDialogTitle className="flex items-center gap-2">
            {permissionPending.action.startsWith("shell.") ? (
              <Shield className="h-5 w-5 text-destructive" />
            ) : (
              <Info className="h-5 w-5 text-primary" />
            )}
            {isArabic ? "طلب صلاحية" : "Permission Request"}
          </AlertDialogTitle>
          <AlertDialogDescription className="space-y-3 pt-2">
            <div className="rounded-lg bg-muted/50 p-3 space-y-1">
              <p className="text-xs text-muted-foreground">
                {isArabic ? "الإجراء" : "Action"}
              </p>
              <p className="text-sm font-mono text-foreground">
                {permissionPending.action}
              </p>
            </div>
            <div className="rounded-lg bg-muted/50 p-3 space-y-1">
              <p className="text-xs text-muted-foreground">
                {isArabic ? "التصنيف" : "Category"}
              </p>
              <p className="text-sm text-foreground">
                {permissionPending.category}
              </p>
            </div>
            {permissionPending.reason && (
              <div className="rounded-lg bg-muted/50 p-3 space-y-1">
                <p className="text-xs text-muted-foreground">
                  {isArabic ? "السبب" : "Reason"}
                </p>
                <p className="text-sm text-foreground">
                  {permissionPending.reason}
                </p>
              </div>
            )}
          </AlertDialogDescription>
        </AlertDialogHeader>
        <AlertDialogFooter className="gap-2">
          <AlertDialogCancel
            disabled={loading}
            onClick={() => handleRespond(false)}
            className="gap-2"
          >
            <ShieldOff className="h-4 w-4" />
            {isArabic ? "رفض" : "Deny"}
          </AlertDialogCancel>
          <AlertDialogAction
            disabled={loading}
            onClick={() => handleRespond(true)}
            className="gap-2 bg-gradient-to-bl from-primary via-purple-500 to-cyan-500"
          >
            <Shield className="h-4 w-4" />
            {isArabic ? "السماح" : "Allow"}
          </AlertDialogAction>
        </AlertDialogFooter>
      </AlertDialogContent>
    </AlertDialog>
  );
}
