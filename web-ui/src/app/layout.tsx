import type { Metadata } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "آدم بريزم | Adam Prism - Personal Digital Twin AI",
  description: "نظام التوأم الرقمي الذكي لـ Osama - مساعد شخصي متطور مدعوم بالذكاء الاصطناعي",
  keywords: ["Adam Prism", "آدم بريزم", "Digital Twin", "AI Assistant", "Ollama"],
  authors: [{ name: "Osama" }],
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl" suppressHydrationWarning>
      <body
        className={`${inter.variable} antialiased bg-background text-foreground`}
        style={{ fontFamily: "'Noto Sans Arabic', 'Inter', system-ui, sans-serif" }}
      >
        {children}
        <Toaster />
      </body>
    </html>
  );
}
