import type { Metadata, Viewport } from "next";
import { Inter } from "next/font/google";
import "./globals.css";
import { Toaster } from "@/components/ui/toaster";
import { ServiceWorkerRegister } from "@/components/pwa/sw-register";

const inter = Inter({
  variable: "--font-geist-sans",
  subsets: ["latin", "latin-ext"],
  display: "swap",
});

export const metadata: Metadata = {
  title: "آدم بريزم | Adam Prism - Personal Digital Twin AI",
  description: "نظام التوأم الرقمي الواعي — إطار عمل ذكاء اصطناعي مفتوح المصدر بمصري طبيعي، ذاكرة طويلة المدى، ووعي هندسي",
  keywords: ["Adam Prism", "آدم بريزم", "Digital Twin", "Conscious AI", "Egyptian Arabic", "Ollama", "Mohamed Othman"],
  authors: [{ name: "Mohamed Othman" }],
  manifest: "/manifest.json",
  appleWebApp: {
    capable: true,
    statusBarStyle: "black-translucent",
    title: "Adam Prism",
  },
  formatDetection: {
    telephone: false,
  },
};

// [PHASE2] Viewport for PWA
export const viewport: Viewport = {
  themeColor: "#10b981",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
};

export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {
  return (
    <html lang="ar" dir="rtl" className="dark" suppressHydrationWarning>
      <head>
        {/* [PHASE2] PWA - Apple Touch Icon */}
        <link rel="apple-touch-icon" href="/logo.svg" />
        {/* [PHASE2] PWA - Theme color for mobile browsers */}
        <meta name="theme-color" content="#10b981" />
        <meta name="mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-capable" content="yes" />
        <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
        <meta name="apple-mobile-web-app-title" content="Adam Prism" />
      </head>
      <body
        className={`${inter.variable} antialiased bg-background text-foreground`}
        style={{ fontFamily: "'Noto Sans Arabic', 'Inter', system-ui, sans-serif" }}
      >
        {children}
        <Toaster />
        <ServiceWorkerRegister />
      </body>
    </html>
  );
}
