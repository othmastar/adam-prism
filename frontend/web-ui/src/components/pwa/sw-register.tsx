"use client";

import { useEffect } from "react";

/**
 * [PHASE2] PWA Service Worker Registration
 * Registers /sw.js to enable offline support and PWA installation.
 */
export function ServiceWorkerRegister() {
  useEffect(() => {
    if (typeof window === "undefined" || !("serviceWorker" in navigator)) {
      return;
    }

    // Only register in production to avoid dev-mode caching issues
    if (process.env.NODE_ENV !== "production") {
      return;
    }

    const register = async () => {
      try {
        const registration = await navigator.serviceWorker.register("/sw.js", {
          scope: "/",
        });

        registration.addEventListener("updatefound", () => {
          const newWorker = registration.installing;
          if (!newWorker) return;

          newWorker.addEventListener("statechange", () => {
            if (newWorker.state === "installed" && navigator.serviceWorker.controller) {
              // New version available — could show update prompt here
              console.info("[PWA] New version available, refresh to update");
            }
          });
        });

        console.info("[PWA] Service worker registered");
      } catch (err) {
        console.warn("[PWA] Service worker registration failed:", err);
      }
    };

    // Defer registration to avoid blocking main thread
    if (document.readyState === "complete") {
      register();
    } else {
      window.addEventListener("load", register);
      return () => window.removeEventListener("load", register);
    }
  }, []);

  return null;
}
