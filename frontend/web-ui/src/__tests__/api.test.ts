import { describe, it, expect, vi, beforeEach } from "vitest";

// Mock fetch globally
const mockFetch = vi.fn();
globalThis.fetch = mockFetch;

beforeEach(() => {
  mockFetch.mockReset();
  if (typeof window !== "undefined") {
    localStorage.clear();
    localStorage.setItem("adam-settings", JSON.stringify({ fastApiUrl: "http://localhost:8002", language: "ar", ollamaUrl: "http://localhost:11434" }));
  }
});

describe("API functions", () => {
  it("fetchChannels returns channels on success", async () => {
    const mockChannels = { telegram: { name: "telegram", running: true, webhook: false } };
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ channels: mockChannels }),
    });

    const { fetchChannels } = await import("@/lib/api");
    const result = await fetchChannels();
    expect(result).toEqual(mockChannels);
  });

  it("fetchChannels returns {} on error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("Network error"));
    const { fetchChannels } = await import("@/lib/api");
    const result = await fetchChannels();
    expect(result).toEqual({});
  });

  it("toggleChannel sends POST with enabled flag", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true });
    const { toggleChannel } = await import("@/lib/api");
    const result = await toggleChannel("telegram", true);
    expect(result).toBe(true);
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8002/api/channels/telegram",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ enabled: true }),
      })
    );
  });

  it("sendChatMessage returns response on success", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: true,
      json: async () => ({ response: "مرحباً", mode: "communicator", intent: {}, knowledge_used: 0, cycle: 1, duration_ms: 100 }),
    });
    const { sendChatMessage } = await import("@/lib/api");
    const result = await sendChatMessage("السلام عليكم");
    expect(result.response).toBe("مرحباً");
  });

  it("sendChatMessage throws on error", async () => {
    mockFetch.mockResolvedValueOnce({
      ok: false,
      json: async () => ({ error: "فشل" }),
    });
    const { sendChatMessage } = await import("@/lib/api");
    await expect(sendChatMessage("test")).rejects.toThrow("فشل");
  });

  it("getFastApiUrl returns default when no localStorage", async () => {
    localStorage.removeItem("adam-settings");
    const mod = await import("@/lib/api");
    expect(mod.getFastApiUrl()).toBe("http://localhost:8002");
  });

  it("getFastApiUrl returns saved value from localStorage", async () => {
    localStorage.setItem("adam-settings", JSON.stringify({ fastApiUrl: "http://localhost:7861" }));
    const mod = await import("@/lib/api");
    expect(mod.getFastApiUrl()).toBe("http://localhost:7861");
  });
});

describe("Store", () => {
  it("has default settings", async () => {
    const { useAppStore } = await import("@/lib/store");
    const state = useAppStore.getState();
    expect(state.settings.language).toBe("ar");
    expect(state.settings.fastApiUrl).toBe("http://localhost:8002");
    expect(state.settings.ollamaUrl).toBe("http://localhost:11434");
  });

  it("updateSettings merges changes", async () => {
    const { useAppStore } = await import("@/lib/store");
    useAppStore.getState().updateSettings({ language: "en" });
    expect(useAppStore.getState().settings.language).toBe("en");
    expect(useAppStore.getState().settings.fastApiUrl).toBe("http://localhost:8002");
  });

  it("has default view as chat", async () => {
    const { useAppStore } = await import("@/lib/store");
    expect(useAppStore.getState().activeView).toBe("chat");
  });

  it("setActiveView changes view", async () => {
    const { useAppStore } = await import("@/lib/store");
    useAppStore.getState().setActiveView("channels");
    expect(useAppStore.getState().activeView).toBe("channels");
  });

  it("manages conversations", async () => {
    const { useAppStore } = await import("@/lib/store");
    const conv = { id: "1", title: "Test", messages: [], createdAt: Date.now(), updatedAt: Date.now() };
    useAppStore.getState().addConversation(conv);
    expect(useAppStore.getState().conversations).toHaveLength(1);
    useAppStore.getState().deleteConversation("1");
    expect(useAppStore.getState().conversations).toHaveLength(0);
  });

  it("tracks API connection state", async () => {
    const { useAppStore } = await import("@/lib/store");
    useAppStore.getState().setApiConnected(true);
    expect(useAppStore.getState().apiConnected).toBe(true);
    useAppStore.getState().setApiConnected(false);
    expect(useAppStore.getState().apiConnected).toBe(false);
  });

  it("supports channels view type", async () => {
    const { useAppStore } = await import("@/lib/store");
    useAppStore.getState().setActiveView("channels");
    expect(useAppStore.getState().activeView).toBe("channels");
    useAppStore.getState().setActiveView("chat");
    expect(useAppStore.getState().activeView).toBe("chat");
  });

  it("manages ollama models", async () => {
    const { useAppStore } = await import("@/lib/store");
    useAppStore.getState().setOllamaModels(["gemma4:e4b", "llama3:8b"]);
    expect(useAppStore.getState().ollamaModels).toHaveLength(2);
  });

  it("toggles isStreaming", async () => {
    const { useAppStore } = await import("@/lib/store");
    expect(useAppStore.getState().isStreaming).toBe(false);
    useAppStore.getState().setIsStreaming(true);
    expect(useAppStore.getState().isStreaming).toBe(true);
  });

  it("updates settings and persists", async () => {
    const { useAppStore } = await import("@/lib/store");
    useAppStore.getState().updateSettings({ temperature: 0.5 });
    expect(useAppStore.getState().settings.temperature).toBe(0.5);
    const saved = JSON.parse(localStorage.getItem("adam-settings") || "{}");
    expect(saved.temperature).toBe(0.5);
  });
});

describe("Channels API", () => {
  it("toggleChannel sends correct request", async () => {
    mockFetch.mockResolvedValueOnce({ ok: true });
    const { toggleChannel } = await import("@/lib/api");
    const result = await toggleChannel("discord", false);
    expect(result).toBe(true);
    expect(mockFetch).toHaveBeenCalledWith(
      "http://localhost:8002/api/channels/discord",
      expect.objectContaining({
        method: "POST",
        body: JSON.stringify({ enabled: false }),
      })
    );
  });

  it("fetchChannelStatus returns null on error", async () => {
    mockFetch.mockRejectedValueOnce(new Error("fail"));
    const { fetchChannelStatus } = await import("@/lib/api");
    const result = await fetchChannelStatus("telegram");
    expect(result).toBeNull();
  });
});

describe("Cognitive Modes", () => {
  it("has 7 modes", async () => {
    const { cognitiveModes } = await import("@/lib/store");
    expect(cognitiveModes).toHaveLength(7);
  });

  it("getModeInfo returns correct info", async () => {
    const { getModeInfo } = await import("@/lib/store");
    const info = getModeInfo("analyst", "ar");
    expect(info.label).toBe("محلل");
    expect(info.icon).toBe("🔍");
  });

  it("getModeInfo returns English label", async () => {
    const { getModeInfo } = await import("@/lib/store");
    const info = getModeInfo("engineer", "en");
    expect(info.label).toBe("Engineer");
  });
});
