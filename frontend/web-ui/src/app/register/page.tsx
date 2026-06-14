"use client";

import { signIn } from "next-auth/react";
import { useRouter } from "next/navigation";
import { useState } from "react";
import Link from "next/link";

const API_BASE = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

/**
 * [PHASE3] Register page
 */
export default function RegisterPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [confirm, setConfirm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    if (password !== confirm) {
      setError("كلمة المرور مش متطابقة / Passwords don't match");
      return;
    }
    if (password.length < 8) {
      setError("كلمة المرور قصيرة جداً (8+ حروف)");
      return;
    }
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/api/auth/register`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ email, username, password }),
      });
      if (!res.ok) {
        const data = await res.json().catch(() => ({}));
        setError(data.detail || "فشل التسجيل / Registration failed");
        setLoading(false);
        return;
      }
      // Auto-login after registration
      await signIn("credentials", { username, password, redirect: false });
      router.push("/");
      router.refresh();
    } catch (err: any) {
      setError(err?.message || "Registration failed");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center bg-background p-4">
      <div className="w-full max-w-md space-y-6 bg-card p-8 rounded-lg border shadow-sm">
        <div className="space-y-2 text-center">
          <h1 className="text-2xl font-bold">إنشاء حساب جديد</h1>
          <p className="text-muted-foreground text-sm">Create Adam Prism account</p>
        </div>

        {error && (
          <div role="alert" className="bg-destructive/10 text-destructive text-sm p-3 rounded-md">
            {error}
          </div>
        )}

        <form onSubmit={handleSubmit} className="space-y-4">
          <div className="space-y-2">
            <label htmlFor="email" className="text-sm font-medium">البريد الإلكتروني</label>
            <input id="email" type="email" required value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="you@example.com" />
          </div>
          <div className="space-y-2">
            <label htmlFor="username" className="text-sm font-medium">اسم المستخدم</label>
            <input id="username" type="text" required minLength={3}
              autoComplete="username" value={username}
              onChange={(e) => setUsername(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="username" />
          </div>
          <div className="space-y-2">
            <label htmlFor="password" className="text-sm font-medium">كلمة المرور (8+ حروف)</label>
            <input id="password" type="password" required minLength={8}
              autoComplete="new-password" value={password}
              onChange={(e) => setPassword(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="••••••••" />
          </div>
          <div className="space-y-2">
            <label htmlFor="confirm" className="text-sm font-medium">تأكيد كلمة المرور</label>
            <input id="confirm" type="password" required minLength={8}
              autoComplete="new-password" value={confirm}
              onChange={(e) => setConfirm(e.target.value)}
              className="w-full px-3 py-2 border rounded-md bg-background focus:outline-none focus:ring-2 focus:ring-accent"
              placeholder="••••••••" />
          </div>
          <button type="submit" disabled={loading}
            className="w-full bg-accent text-white py-2 rounded-md hover:opacity-90 transition disabled:opacity-50">
            {loading ? "جاري الإنشاء..." : "إنشاء حساب / Sign up"}
          </button>
        </form>

        <p className="text-center text-sm text-muted-foreground">
          عندك حساب بالفعل؟{" "}
          <Link href="/login" className="text-accent hover:underline">تسجيل دخول</Link>
        </p>
      </div>
    </div>
  );
}
