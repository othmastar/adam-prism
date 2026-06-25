import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  // [PHASE1-SECURITY] TypeScript errors must NOT be ignored
  // They indicate broken type contracts that can cause runtime failures
  typescript: {
    ignoreBuildErrors: false,
  },
  // [PHASE1-SECURITY] React strict mode helps catch subtle bugs
  reactStrictMode: true,
  // [PHASE1-SECURITY] Security headers
  async headers() {
    return [
      {
        source: "/:path*",
        headers: [
          { key: "X-Content-Type-Options", value: "nosniff" },
          { key: "X-Frame-Options", value: "DENY" },
          { key: "X-XSS-Protection", value: "1; mode=block" },
          { key: "Referrer-Policy", value: "strict-origin-when-cross-origin" },
          { key: "Strict-Transport-Security", value: "max-age=31536000; includeSubDomains" },
        ],
      },
    ];
  },
  // [DEV] Proxy /api/* to FastAPI backend (port 8000)
  async rewrites() {
    return [
      {
        source: "/api/:path*",
        destination: "http://localhost:8000/api/:path*",
      },
      {
        source: "/ws/:path*",
        destination: "http://localhost:8000/ws/:path*",
      },
      {
        source: "/healthz/:path*",
        destination: "http://localhost:8000/healthz/:path*",
      },
      {
        source: "/metrics",
        destination: "http://localhost:8000/metrics",
      },
      {
        source: "/docs",
        destination: "http://localhost:8000/docs",
      },
    ];
  },

  allowedDevOrigins: [
    "preview-chat-5cd51445-8812-4a59-a8e3-8bd54cc03b5b.space-z.ai",
    ".space-z.ai",
  ],
};

export default nextConfig;
