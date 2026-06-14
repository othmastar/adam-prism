"use client";

import { signIn } from "next-auth/react";
import { useRouter, useSearchParams } from "next/navigation";
import { useEffect, useState } from "react";
import Link from "next/link";

/**
 * [PHASE3] Login page — next-auth integration
 * [PHASE6] Added SSO buttons (Google, Microsoft, GitHub)
 */
export default function LoginPage() {
  const router = useRouter();
  const search = useSearchParams();
  const callbackUrl = search.get("callbackUrl") || "/";
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await signIn("credentials", {
        username,
        password,
        redirect: false,
        callbackUrl,
      });
      if (res?.error) {
        setError("بيانات الدخول غلط / Invalid credentials");
        setLoading(false);
        return;
      }
      if (res?.ok) {
        router.push(callbackUrl);
        router.refresh();
      }
    } catch (err: any) {
      setError(err?.message || "Login failed");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-6 bg-card p-8 rounded-lg border shadow-sm">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-bold">تسجيل الدخول</h1>
          <p className="text-muted-foreground text-sm">Sign in to Adam Prism</p>
        </div>

        {error && (
          <div
            role="alert"
            className="bg-destructive/10 text-destructive text-sm p-3 rounded-md"
          >
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium">
              اسم المستخدم أو البريد
            </label>
            <input
              id="username"
              type="text"
              required
              autoComplete="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="username or email"
            />
          </div>

          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">
              كلمة المرور
            </label>
            <input
              id="password"
              type="password"
              required
              autoComplete="current-password"
              minLength={8}
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="••••••••"
            />
          </div>

          <button
            type="submit"
            disabled={loading}
            className="w-full bg-accent text-white py-2 rounded-md hover:opacity-90 transition disabled:opacity-50"
          >
            {loading ? "جاري الدخول..." : "دخول / Sign in"}
          </button>

          {/* [PHASE6] SSO Divider */}
          <div className="relative my-6">
            <div className="absolute inset-0 flex items-center" aria-hidden="true">
              <div className="w-full border-t border-border"></div>
            </div>
            <div className="relative flex justify-center text-xs uppercase">
              <span className="bg-card px-2 text-muted-foreground">أو / or</span>
            </div>
          </div>

          {/* [PHASE6] SSO buttons (auto-detected from backend) */}
          <SSOButtons callbackUrl={callbackUrl} />
        </form>

        <p className="text-center text-sm text-muted-foreground">
          ليس لديك حساب؟{" "}
          <Link href="/register" className="text-accent hover:underline">
            إنشاء حساب / Sign up
          </Link>
        </p>

        <div className="text-xs text-center text-muted-foreground pt-4 border-t">
          <p>أول مرة؟ شغّل backend ثم أنشئ أول مستخدم عبر:</p>
          <code className="block mt-1 bg-muted p-2 rounded text-left">
            curl -X POST {process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000"}/api/auth/register \<br />
            {"  "}-H "Content-Type: application/json" \<br />
            {"  "}-d '{{"email":"you@example.com","username":"you","password":"yourpass"}}
          </code>
        </div>
      </div>
    </div>
  );
}

// [PHASE6] SSO buttons component
function SSOButtons({ callbackUrl }: { callbackUrl: string }) {
  const [providers, setProviders] = useState<{ name: string; configured: boolean }[]>([]);
  const [loadingProvider, setLoadingProvider] = useState<string | null>(null);

  useEffect(() => {
    // Fetch configured SSO providers
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    fetch(`${apiUrl}/api/auth/sso/providers`)
      .then((r) => r.json())
      .then((data) => setProviders(data.providers || []))
      .catch(() => setProviders([]));
  }, []);

  const handleSSOLogin = async (provider: string) => {
    setLoadingProvider(provider);
    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
      const resp = await fetch(
        `${apiUrl}/api/auth/sso/${provider}/authorize?redirect_uri=${encodeURIComponent(
          `${window.location.origin}/api/auth/sso/${provider}/callback`
        )}`
      );
      const data = await resp.json();
      if (data.authorization_url) {
        // [PHASE6] Store state in sessionStorage for CSRF protection
        sessionStorage.setItem("sso_state", data.state);
        window.location.href = data.authorization_url;
      }
    } catch (e) {
      console.error("SSO error:", e);
      setLoadingProvider(null);
    }
  };

  if (providers.length === 0) return null;

  return (
    <div className="space-y-2" role="group" aria-label="Single sign-on providers">
      {providers.map((p) => (
        <button
          key={p.name}
          onClick={() => handleSSOLogin(p.name)}
          disabled={loadingProvider !== null}
          className="w-full border border-border bg-background py-2 px-4 rounded-md hover:bg-accent/10 transition disabled:opacity-50 flex items-center justify-center gap-2"
          aria-label={`Sign in with ${p.name}`}
        >
          {loadingProvider === p.name ? (
            <span className="text-sm">جاري التحويل...</span>
          ) : (
            <>
              <span className="text-sm font-medium capitalize">
                {p.name === "google" && "G"}
                {p.name === "microsoft" && "M"}
                {p.name === "github" && "GH"}
                {p.name === "okta" && "OK"}
                {p.name === "keycloak" && "KC"}
                {p.name === "auth0" && "A0"}
              </span>
              <span className="text-sm">دخول عبر {p.name} / Sign in with {p.name}</span>
            </>
          )}
        </button>
      ))}
    </div>
  );
}
