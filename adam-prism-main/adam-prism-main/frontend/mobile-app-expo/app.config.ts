import { defineConfig } from "expo/config"

export default defineConfig({
  scheme: "adamprism",
  name: "Adam Prism",
  slug: "adam-prism",
  version: "1.0.0",
  orientation: "portrait",
  userInterfaceStyle: "dark",
  newArchEnabled: true,
  ios: {
    bundleIdentifier: "com.adamprism.mobile",
    supportsTablet: true,
    infoPlist: {
      NSMicrophoneUsageDescription: "Adam Prism uses the microphone for voice input.",
      NSCameraUsageDescription: "Adam Prism uses the camera to capture images for AI analysis.",
    },
  },
  android: {
    package: "com.adamprism.mobile",
    permissions: ["RECORD_AUDIO", "CAMERA", "INTERNET"],
    adaptiveIcon: {
      foregroundImage: "./src/assets/icon.png",
      backgroundColor: "#0a0a0f",
    },
  },
  web: {
    bundler: "metro",
    output: "static",
  },
  plugins: [
    "expo-router",
    "expo-secure-store",
  ],
  experiments: {
    typedRoutes: true,
  },
  extra: {
    router: {
      origin: false,
    },
    apiUrl: process.env.EXPO_PUBLIC_API_URL || "http://localhost:8000",
  },
})
