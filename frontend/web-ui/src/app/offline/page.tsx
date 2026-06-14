"use client";

import Link from "next/link";

/**
 * [PHASE2] PWA Offline Page
 * Shown when the user is offline and navigates to a page that isn't cached.
 */
export default function OfflinePage() {
  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="max-w-md text-center space-y-4">
        <div className="text-6xl">📡</div>
        <h1 className="text-2xl font-bold">أنت غير متصل بالإنترنت</h1>
        <p className="text-muted-foreground">
          يبدو أنك فقدت الاتصال. تحقق من اتصالك وحاول مرة أخرى.
          <br />
          You appear to be offline. Check your connection and try again.
        </p>
        <Link
          href="/"
          className="inline-block px-4 py-2 bg-accent text-white rounded-md hover:opacity-90 transition"
        >
          إعادة المحاولة
        </Link>
      </div>
    </div>
  );
}
