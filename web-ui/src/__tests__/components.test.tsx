import { describe, it, expect, vi, beforeEach } from "vitest";
import { render, screen } from "@testing-library/react";

// Mock fetch
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
  if (typeof window !== "undefined") {
    localStorage.clear();
    localStorage.setItem("adam-settings", JSON.stringify({ fastApiUrl: "http://localhost:8002", language: "ar", ollamaUrl: "http://localhost:11434" }));
  }
});

describe("AdamLogo", () => {
  it("renders without crashing", async () => {
    const { AdamLogoFull } = await import("@/components/adam/adam-logo");
    const { container } = render(<AdamLogoFull />);
    expect(container).toBeTruthy();
  });
});

describe("VoiceButton", () => {
  it("renders without crashing", async () => {
    const { VoiceButton } = await import("@/components/adam/voice-button");
    const { container } = render(<VoiceButton />);
    expect(container).toBeTruthy();
  });
});

describe("ShieldPulse", () => {
  it("renders without crashing", async () => {
    const { ShieldPulse } = await import("@/components/adam/shield-pulse");
    const { container } = render(<ShieldPulse />);
    expect(container).toBeTruthy();
  });
});
