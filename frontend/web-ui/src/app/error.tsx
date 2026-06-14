"use client";

import { useEffect } from "react";
import Link from "next/link";

/**
 * [PHASE1-SECURITY] Route-level error boundary
 * Catches errors in nested route segments
 */
export default function Error({
  error,
  reset,
}: {
  error: Error & { digest?: string };
  reset: () => void;
}) {
  useEffect(() => {
    console.error("Route error:", error);
  }, [error]);

  return (
    <div style={{
      minHeight: "60vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      padding: "2rem"
    }}>
      <div style={{ maxWidth: "32rem", textAlign: "center" }}>
        <h2 style={{ fontSize: "1.5rem", marginBottom: "0.75rem" }}>
          ⚠️ حدث خطأ في هذه الصفحة
        </h2>
        <p style={{ marginBottom: "1.5rem", color: "#9ca3af" }}>
          Something went wrong on this page. You can try again or go back to the home page.
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
  );
}
