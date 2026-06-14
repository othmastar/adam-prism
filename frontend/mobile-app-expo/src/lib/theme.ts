/**
 * [PHASE6] Theme system for mobile (dark/light/system).
 * Adapts to OS preference by default, persisted in SecureStore.
 */
import { create } from "zustand";
import { Appearance, ColorSchemeName } from "react-native";
import * as SecureStore from "expo-secure-store";

type ThemeMode = "dark" | "light" | "system";

interface ThemeState {
  mode: ThemeMode;
  systemScheme: ColorSchemeName;
  setMode: (mode: ThemeMode) => Promise<void>;
  loadStored: () => Promise<void>;
  isDark: () => boolean;
}

const STORAGE_KEY = "@adam_prism:theme_mode";

export const useThemeStore = create<ThemeState>((set, get) => ({
  mode: "system",
  systemScheme: Appearance.getColorScheme(),

  async setMode(mode) {
    set({ mode });
    try {
      await SecureStore.setItemAsync(STORAGE_KEY, mode);
    } catch {
      // ignore
    }
  },

  async loadStored() {
    try {
      const stored = await SecureStore.getItemAsync(STORAGE_KEY);
      if (stored === "dark" || stored === "light" || stored === "system") {
        set({ mode: stored });
      }
    } catch {
      // ignore
    }
    // Listen for system changes
    Appearance.addChangeListener(({ colorScheme }) => {
      set({ systemScheme: colorScheme });
    });
  },

  isDark() {
    const { mode, systemScheme } = get();
    if (mode === "system") {
      return systemScheme !== "light";
    }
    return mode === "dark";
  },
}));

export const colors = {
  // [PHASE6] Centralized color tokens (dark mode)
  dark: {
    bg: "#0a0a0f",
    surface: "#1f2937",
    text: "#e5e7eb",
    textMuted: "#9ca3af",
    accent: "#10b981",
    error: "#ef4444",
    warning: "#f59e0b",
    success: "#10b981",
    border: "#374151",
  },
  light: {
    bg: "#ffffff",
    surface: "#f3f4f6",
    text: "#111827",
    textMuted: "#6b7280",
    accent: "#059669",
    error: "#dc2626",
    warning: "#d97706",
    success: "#059669",
    border: "#e5e7eb",
  },
};

export function getColors(isDark: boolean) {
  return isDark ? colors.dark : colors.light;
}
