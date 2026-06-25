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

// [PHASE2] Viewport for PWA + mobile safe areas
export const viewport: Viewport = {
  themeColor: "#10b981",
  width: "device-width",
  initialScale: 1,
  maximumScale: 5,
  userScalable: true,
  viewportFit: "cover",
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
        {/* Clean slate — fixes old 8002 URL and clears cache */}
        <script dangerouslySetInnerHTML={{ __html: '(function(){try{var s=localStorage.getItem("adam-settings");if(s&&s.indexOf("8002")!==-1){localStorage.removeItem("adam-settings");console.log("✅ Fixed old 8002 URL — cleared");}if(!sessionStorage.getItem("sw_cleaned_v4")){["adam-conversations","adam_admin","adam_attempts"].forEach(function(k){localStorage.removeItem(k)});sessionStorage.setItem("sw_cleaned_v4","1");}}catch(e){}})()' }} />
        <footer className="w-full py-3 px-4 border-t border-border">
          <div className="max-w-7xl mx-auto flex items-center justify-center gap-2 text-[10px] text-muted-foreground">
            <span>Powered by</span>
            <a href="https://sovereignneuralfortresses.com" target="_blank" rel="noopener" className="text-primary hover:underline font-medium">Sovereign Neural Fortresses</a>
            <span>·</span>
            <span>Adam v9.5</span>
          </div>
        </footer>
      </body>
    </html>
  );
}
