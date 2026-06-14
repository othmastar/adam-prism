/**
 * [PHASE5] Crash reporting + analytics for desktop app.
 * Captures unhandled errors and sends to configured endpoint.
 */
interface CrashReport {
  timestamp: number;
  app_version: string;
  os: string;
  arch: string;
  error: {
    message: string;
    stack?: string;
    name: string;
  };
  context: Record<string, unknown>;
  user_id?: string;
}

export class CrashReporter {
  private endpoint: string | null = null;
  private appVersion = "1.0.0";
  private userId: string | null = null;
  private enabled = false;

  /**
   * [PHASE5] Configure the crash reporter.
   */
  configure(options: {
    endpoint?: string;
    appVersion?: string;
    userId?: string;
    enabled?: boolean;
  }): void {
    this.endpoint = options.endpoint || null;
    this.appVersion = options.appVersion || "1.0.0";
    this.userId = options.userId || null;
    this.enabled = options.enabled ?? false;
  }

  /**
   * [PHASE5] Capture an error.
   */
  async captureError(
    error: Error,
    context: Record<string, unknown> = {},
  ): Promise<void> {
    if (!this.enabled) {
      console.error("[CRASH]", error.message, error.stack);
      return;
    }

    const report: CrashReport = {
      timestamp: Date.now(),
      app_version: this.appVersion,
      os: this.getOS(),
      arch: this.getArch(),
      error: {
        message: error.message,
        stack: error.stack,
        name: error.name,
      },
      context,
      user_id: this.userId || undefined,
    };

    if (this.endpoint) {
      try {
        await fetch(this.endpoint, {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(report),
        });
      } catch (err) {
        console.error("[CRASH] Failed to send report:", err);
      }
    } else {
      // Local-only mode - log to console
      console.error("[CRASH]", JSON.stringify(report, null, 2));
    }
  }

  /**
   * [PHASE5] Set up global error handlers.
   */
  installGlobalHandlers(): void {
    if (typeof window === "undefined") return;

    window.addEventListener("error", (event) => {
      if (event.error) {
        this.captureError(event.error, {
          type: "uncaught",
          filename: event.filename,
          lineno: event.lineno,
          colno: event.colno,
        });
      }
    });

    window.addEventListener("unhandledrejection", (event) => {
      this.captureError(
        event.reason instanceof Error
          ? event.reason
          : new Error(String(event.reason)),
        { type: "unhandledrejection" },
      );
    });
  }

  private getOS(): string {
    if (typeof window === "undefined") return "unknown";
    const ua = window.navigator.userAgent;
    if (ua.includes("Mac")) return "macos";
    if (ua.includes("Windows")) return "windows";
    if (ua.includes("Linux")) return "linux";
    return "unknown";
  }

  private getArch(): string {
    if (typeof window === "undefined") return "unknown";
    // @ts-expect-error - userAgentData may not be available
    return navigator.userAgentData?.platform || "unknown";
  }
}

export const crashReporter = new CrashReporter();
