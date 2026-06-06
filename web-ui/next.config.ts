import type { NextConfig } from "next";

const nextConfig: NextConfig = {
  output: "standalone",
  /* config options here */
  typescript: {
    ignoreBuildErrors: true,
  },
  reactStrictMode: false,
  allowedDevOrigins: [
    "preview-chat-5cd51445-8812-4a59-a8e3-8bd54cc03b5b.space-z.ai",
    ".space-z.ai",
  ],
};

export default nextConfig;
