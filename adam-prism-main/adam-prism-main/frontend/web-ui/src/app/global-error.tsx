"use client";

import { useEffect } from "react";
import Link from "next/link";

/**
 * [PHASE1-SECURITY] Global error boundary
 * Catches unhandled errors in the app and prevents white screen crashes
 */
export default function GlobalError({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Global error:", error);
  }, [error]);

  return (
    <html lang="ar" dir="rtl">
      <body>
        <div style={{
          minHeight: "100vh",
          display: "flex",
          alignItems: "center",
          justifyContent: "center",
          background: "#0a0a0f",
          color: "#e5e7eb",
          fontFamily: "system-ui, sans-serif",
          padding: "2rem"
        }}>
          <div style={{ maxWidth: "32rem", textAlign: "center" }}>
            <h1 style={{ fontSize: "2rem", marginBottom: "1rem" }}>
              ⚠️ حدث خطأ غير متوقع
            </h1>
            <p style={{ marginBottom: "1.5rem", color: "#9ca3af" }}>
              An unexpected error occurred. The team has been notified.
            </p>
            {error.digest && (
              <p style={{
                fontSize: "0.75rem",
                color: "#6b7280",
                marginBottom: "1.5rem",
                fontFamily: "monospace"
              }}>
                Error ID: {error.digest}
              </p>
            )}
            <div style={{ display: "flex", gap: "1rem", justifyContent: "center" }}>
              <button
                onClick={reset}
                style={{
                  padding: "0.5rem 1.5rem",
                  background: "#10b981",
                  color: "white",
                  border: "none",
                  borderRadius: "0.375rem",
                  cursor: "pointer",
                  fontSize: "0.875rem"
                }}
              >
                إعادة المحاولة
              </button>
              <Link
                href="/"
                style={{
                  padding: "0.5rem 1.5rem",
                  background: "transparent",
                  color: "#9ca3af",
                  border: "1px solid #374151",
                  borderRadius: "0.375rem",
                  textDecoration: "none",
                  fontSize: "0.875rem"
                }}
              >
                الصفحة الرئيسية
              </Link>
            </div>
          </div>
        </div>
      </body>
    </html>
  );
}
