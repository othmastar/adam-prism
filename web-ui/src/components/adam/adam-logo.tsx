"use client";

import { motion } from "framer-motion";

export function AdamLogo({ size = 48, animate = true }: { size?: number; animate?: boolean }) {
  return (
    <div className="relative inline-flex items-center justify-center" style={{ width: size, height: size }}>
      {/* Outer glow ring */}
      {animate && (
        <motion.div
          className="absolute inset-0 rounded-full"
          style={{
            border: `2px solid rgba(139, 92, 246, 0.3)`,
          }}
          animate={{
            scale: [1, 1.15, 1],
            opacity: [0.5, 0.2, 0.5],
          }}
          transition={{
            duration: 3,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />
      )}

      {/* Main prism shape */}
      <svg
        width={size}
        height={size}
        viewBox="0 0 100 100"
        fill="none"
        xmlns="http://www.w3.org/2000/svg"
        className={animate ? "prism-glow" : ""}
      >
        {/* Prism triangle */}
        <motion.path
          d="M50 10 L85 80 L15 80 Z"
          fill="url(#prismGradient)"
          stroke="url(#prismStroke)"
          strokeWidth="2"
          strokeLinejoin="round"
          {...(animate
            ? {
                animate: {
                  filter: [
                    "drop-shadow(0 0 4px rgba(139, 92, 246, 0.3))",
                    "drop-shadow(0 0 12px rgba(6, 182, 212, 0.6))",
                    "drop-shadow(0 0 4px rgba(139, 92, 246, 0.3))",
                  ],
                },
                transition: { duration: 3, repeat: Infinity, ease: "easeInOut" },
              }
            : {})}
        />

        {/* Light beam entering */}
        <motion.line
          x1="5"
          y1="45"
          x2="35"
          y2="45"
          stroke="#8b5cf6"
          strokeWidth="2.5"
          strokeLinecap="round"
          {...(animate
            ? {
                animate: { opacity: [0.4, 1, 0.4] },
                transition: { duration: 2, repeat: Infinity, ease: "easeInOut" },
              }
            : {})}
        />

        {/* Refracted beams - purple, cyan, blue */}
        <motion.line
          x1="65"
          y1="55"
          x2="95"
          y2="35"
          stroke="#8b5cf6"
          strokeWidth="1.5"
          strokeLinecap="round"
          {...(animate
            ? {
                animate: { opacity: [0.3, 0.9, 0.3] },
                transition: { duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.3 },
              }
            : {})}
        />
        <motion.line
          x1="65"
          y1="55"
          x2="95"
          y2="55"
          stroke="#06b6d4"
          strokeWidth="1.5"
          strokeLinecap="round"
          {...(animate
            ? {
                animate: { opacity: [0.3, 0.9, 0.3] },
                transition: { duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.5 },
              }
            : {})}
        />
        <motion.line
          x1="65"
          y1="55"
          x2="95"
          y2="75"
          stroke="#3b82f6"
          strokeWidth="1.5"
          strokeLinecap="round"
          {...(animate
            ? {
                animate: { opacity: [0.3, 0.9, 0.3] },
                transition: { duration: 2, repeat: Infinity, ease: "easeInOut", delay: 0.7 },
              }
            : {})}
        />

        {/* Inner core dot */}
        <motion.circle
          cx="50"
          cy="55"
          r="4"
          fill="url(#coreGradient)"
          {...(animate
            ? {
                animate: { r: [3, 5, 3], opacity: [0.6, 1, 0.6] },
                transition: { duration: 2.5, repeat: Infinity, ease: "easeInOut" },
              }
            : {})}
        />

        <defs>
          <linearGradient id="prismGradient" x1="50" y1="10" x2="50" y2="80" gradientUnits="userSpaceOnUse">
            <stop stopColor="rgba(139, 92, 246, 0.15)" />
            <stop offset="0.5" stopColor="rgba(6, 182, 212, 0.1)" />
            <stop offset="1" stopColor="rgba(59, 130, 246, 0.05)" />
          </linearGradient>
          <linearGradient id="prismStroke" x1="15" y1="80" x2="85" y2="80" gradientUnits="userSpaceOnUse">
            <stop stopColor="#8b5cf6" />
            <stop offset="0.5" stopColor="#06b6d4" />
            <stop offset="1" stopColor="#3b82f6" />
          </linearGradient>
          <radialGradient id="coreGradient" cx="50" cy="55" r="5" gradientUnits="userSpaceOnUse">
            <stop stopColor="#06b6d4" />
            <stop offset="1" stopColor="#8b5cf6" />
          </radialGradient>
        </defs>
      </svg>
    </div>
  );
}

export function AdamLogoFull({ animate = true }: { animate?: boolean }) {
  return (
    <div className="flex items-center gap-3">
      <AdamLogo size={36} animate={animate} />
      <div className="flex flex-col">
        <span className="text-lg font-bold prism-text tracking-wide">آدم بريزم</span>
        <span className="text-[10px] text-muted-foreground tracking-widest uppercase">Adam Prism</span>
      </div>
    </div>
  );
}
