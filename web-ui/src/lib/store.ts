import React from "react";
import { create } from "zustand";

// --- Types ---

export type CognitiveMode =
  | "analyst"
  | "builder"
  | "corrector"
  | "engineer"
  | "researcher"
  | "communicator"
  | "strategist";

export type Message = {
  id: string;
  role: "user" | "assistant" | "system";
  content: string;
  timestamp: number;
  mode?: CognitiveMode;
  intent?: Record<string, unknown>;
  knowledgeUsed?: number;
  cycle?: number;
  durationMs?: number;
  audioUrl?: string;
};

export type Conversation = {
  id: string;
  title: string;
  messages: Message[];
  createdAt: number;
  updatedAt: number;
};

export type ViewType = "chat" | "knowledge" | "notebook" | "tools" | "settings" | "monitor" | "pipeline";

export type AppSettings = {
  // Model
  modelName: string;
  inferenceMode: "ollama" | "lora";
  loraServerUrl: string;
  temperature: number;
  topP: number;
  topK: number;
  // Language
  language: "ar" | "en";
  // API
  ollamaUrl: string;
  fastApiUrl: string;
  // Qdrant
  qdrantUrl: string;
  qdrantApiKey: string;
  // Telegram
  telegramBotToken: string;
  telegramChatId: string;
  // Security
  authorizedUsers: string;
  // Tailscale
  tailscaleIp: string;
  tailscaleStatus: string;
  // System
  systemPrompt: string;
};

export type KnowledgeStats = {
  totalEntries: number;
  collections: string[];
  lastUpdated: string;
};

export type NotebookStats = {
  pagesRead: number;
  ideasExtracted: number;
  connectionsMade: number;
  pendingQuestions: number;
};

export type SearchResult = {
  id: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
  collection?: string;
};

export type NotebookEntry = {
  id: string;
  date: string;
  title: string;
  content: string;
  connections: string[];
  pendingQuestions: string[];
  tags: string[];
};

export type ProcessingStep = {
  step: string;
  status: "running" | "done" | "blocked" | "error";
  details: Record<string, unknown>;
  cycle: number;
  timestamp: string;
};

export type SystemHealth = {
  api: string;
  engine: {
    session_id: string | null;
    model: string | null;
    active_mode: string | null;
    cycle_count: number;
    conversation_length: number;
  };
  system: {
    cpu_percent: number | null;
    memory_percent: number | null;
  };
  ollama: { connected: boolean; models?: string[] } | null;
  qdrant: { connected: boolean } | null;
};

export type SummarizeProgress = {
  status: "idle" | "processing" | "done" | "error";
  progress: number;
  chunksProcessed: number;
  totalChunks: number;
  result?: string;
  error?: string;
};

type AppState = {
  // View
  activeView: ViewType;
  setActiveView: (view: ViewType) => void;

  // Sidebar
  sidebarOpen: boolean;
  setSidebarOpen: (open: boolean) => void;

  // Monitoring
  processingSteps: ProcessingStep[];
  setProcessingSteps: (steps: ProcessingStep[]) => void;
  addProcessingStep: (step: ProcessingStep) => void;
  clearProcessingSteps: () => void;
  systemHealth: SystemHealth | null;
  setSystemHealth: (health: SystemHealth | null) => void;

  // Conversations
  conversations: Conversation[];
  activeConversationId: string | null;
  setActiveConversationId: (id: string | null) => void;
  addConversation: (conv: Conversation) => void;
  updateConversation: (id: string, updates: Partial<Conversation>) => void;
  deleteConversation: (id: string) => void;

  // Chat state
  isStreaming: boolean;
  setIsStreaming: (streaming: boolean) => void;
  activeMode: CognitiveMode;
  setActiveMode: (mode: CognitiveMode) => void;

  // Settings
  settings: AppSettings;
  updateSettings: (updates: Partial<AppSettings>) => void;

  // API Health
  apiConnected: boolean;
  setApiConnected: (connected: boolean) => void;
  ollamaConnected: boolean;
  setOllamaConnected: (connected: boolean) => void;
  ollamaModels: string[];
  setOllamaModels: (models: string[]) => void;

  // Knowledge
  knowledgeStats: KnowledgeStats | null;
  setKnowledgeStats: (stats: KnowledgeStats | null) => void;
  searchResults: SearchResult[];
  setSearchResults: (results: SearchResult[]) => void;
  isSearching: boolean;
  setIsSearching: (searching: boolean) => void;

  // Notebook
  notebookStats: NotebookStats | null;
  setNotebookStats: (stats: NotebookStats | null) => void;
  notebookEntries: NotebookEntry[];
  setNotebookEntries: (entries: NotebookEntry[]) => void;

  // Tools / Summarization
  summarizeProgress: SummarizeProgress;
  setSummarizeProgress: (progress: Partial<SummarizeProgress>) => void;

  // Floating monitor
  monitorVisible: boolean;
  setMonitorVisible: (visible: boolean) => void;
  gpuPercent: number;
  setGpuPercent: (percent: number) => void;

  // Conversation history panel toggle
  historyPanelOpen: boolean;
  setHistoryPanelOpen: (open: boolean) => void;

  // Self-Healing diagnostics
  issueCount: number;
  setIssueCount: (count: number) => void;
  diagnosticsOpen: boolean;
  setDiagnosticsOpen: (open: boolean) => void;
  diagnosticsLog: string[];
  addDiagnosticsLog: (line: string) => void;
  clearDiagnosticsLog: () => void;

  // Security shield
  shieldActive: boolean;
  setShieldActive: (active: boolean) => void;

  // Model orchestrator
  orchestratorOpen: boolean;
  setOrchestratorOpen: (open: boolean) => void;
  consultationMode: boolean;
  setConsultationMode: (mode: boolean) => void;

  // Daily reflection
  dailyReflection: string;
  setDailyReflection: (text: string) => void;

  // Capability usage tracking (for بطاقات نابضة)
  capabilityUseCount: Record<string, number>;
  incrementCapabilityUse: (id: string) => void;
  activeCapability: string | null;
  setActiveCapability: (id: string | null) => void;

  // Synced session IDs (for Ghost Sidebar)
  syncedSessionIds: string[];
  addSyncedSessionId: (id: string) => void;

  // Permission (Phase 1c)
  permissionPending: {
    action: string;
    reason: string;
    level: string;
    category: string;
    request_id: string;
  } | null;
  setPermissionPending: (perm: any) => void;
};

const defaultSettings: AppSettings = {
  modelName: "othmastar-v3",
  inferenceMode: "ollama",
  loraServerUrl: "http://localhost:8080",
  temperature: 0.7,
  topP: 0.9,
  topK: 40,
  language: "ar",
  ollamaUrl: "http://localhost:11434",
  fastApiUrl: "http://localhost:8000",
  qdrantUrl: "http://localhost:6333",
  qdrantApiKey: "",
  telegramBotToken: "",
  telegramChatId: "",
  authorizedUsers: "OthMastar",
  tailscaleIp: "",
  tailscaleStatus: "disconnected",
  systemPrompt: "أنت آدم بريزم، مساعد ذكي لـ OthMastar. تجيب بالعربي. مختصر وواضح.",
};

function loadFromLocalStorage<T>(key: string, fallback: T): T {
  if (typeof window === "undefined") return fallback;
  try {
    const stored = localStorage.getItem(key);
    return stored ? JSON.parse(stored) : fallback;
  } catch {
    return fallback;
  }
}

function saveToLocalStorage(key: string, value: unknown) {
  if (typeof window === "undefined") return;
  try {
    localStorage.setItem(key, JSON.stringify(value));
  } catch {
    // ignore
  }
}

export const useAppStore = create<AppState>((set, get) => ({
  // View
  activeView: "chat",
  setActiveView: (view) => set({ activeView: view }),

  // Sidebar
  sidebarOpen: false,
  setSidebarOpen: (open) => set({ sidebarOpen: open }),

  // Monitoring
  processingSteps: [],
  setProcessingSteps: (steps) => set({ processingSteps: steps }),
  addProcessingStep: (step) =>
    set((s) => ({ processingSteps: [...s.processingSteps, step] })),
  clearProcessingSteps: () => set({ processingSteps: [] }),
  systemHealth: null,
  setSystemHealth: (health) => set({ systemHealth: health }),

  // Conversations
  conversations: [],
  activeConversationId: null,
  setActiveConversationId: (id) => set({ activeConversationId: id }),
  addConversation: (conv) => {
    const updated = [conv, ...get().conversations];
    set({ conversations: updated });
    saveToLocalStorage("adam-conversations", updated);
  },
  updateConversation: (id, updates) => {
    const updated = get().conversations.map((c) =>
      c.id === id ? { ...c, ...updates, updatedAt: Date.now() } : c
    );
    set({ conversations: updated });
    saveToLocalStorage("adam-conversations", updated);
  },
  deleteConversation: (id) => {
    const updated = get().conversations.filter((c) => c.id !== id);
    const newActiveId =
      get().activeConversationId === id ? null : get().activeConversationId;
    set({ conversations: updated, activeConversationId: newActiveId });
    saveToLocalStorage("adam-conversations", updated);
  },

  // Chat state
  isStreaming: false,
  setIsStreaming: (streaming) => set({ isStreaming: streaming }),
  activeMode: "analyst",
  setActiveMode: (mode) => set({ activeMode: mode }),

  // Settings
  settings: defaultSettings,
  updateSettings: (updates) => {
    const updated = { ...get().settings, ...updates };
    set({ settings: updated });
    saveToLocalStorage("adam-settings", updated);
  },

  // API Health
  apiConnected: false,
  setApiConnected: (connected) => set({ apiConnected: connected }),
  ollamaConnected: false,
  setOllamaConnected: (connected) => set({ ollamaConnected: connected }),
  ollamaModels: [],
  setOllamaModels: (models) => set({ ollamaModels: models }),

  // Knowledge
  knowledgeStats: null,
  setKnowledgeStats: (stats) => set({ knowledgeStats: stats }),
  searchResults: [],
  setSearchResults: (results) => set({ searchResults: results }),
  isSearching: false,
  setIsSearching: (searching) => set({ isSearching: searching }),

  // Notebook
  notebookStats: null,
  setNotebookStats: (stats) => set({ notebookStats: stats }),
  notebookEntries: [],
  setNotebookEntries: (entries) => set({ notebookEntries: entries }),

  // Tools / Summarization
  summarizeProgress: {
    status: "idle",
    progress: 0,
    chunksProcessed: 0,
    totalChunks: 0,
  },
  setSummarizeProgress: (progress) =>
    set((s) => ({ summarizeProgress: { ...s.summarizeProgress, ...progress } })),

  // Floating monitor
  monitorVisible: true,
  setMonitorVisible: (visible) => set({ monitorVisible: visible }),
  gpuPercent: 0,
  setGpuPercent: (percent) => set({ gpuPercent: percent }),

  // Conversation history panel toggle
  historyPanelOpen: true,
  setHistoryPanelOpen: (open) => set({ historyPanelOpen: open }),

  // Self-Healing diagnostics
  issueCount: 0,
  setIssueCount: (count) => set({ issueCount: count }),
  diagnosticsOpen: false,
  setDiagnosticsOpen: (open) => set({ diagnosticsOpen: open, ...(open ? { orchestratorOpen: false } : {}) }),
  diagnosticsLog: [],
  addDiagnosticsLog: (line) => set((s) => ({ diagnosticsLog: [...s.diagnosticsLog, line] })),
  clearDiagnosticsLog: () => set({ diagnosticsLog: [] }),

  // Security shield
  shieldActive: false,
  setShieldActive: (active) => set({ shieldActive: active }),

  // Model orchestrator
  orchestratorOpen: false,
  setOrchestratorOpen: (open) => set({ orchestratorOpen: open, ...(open ? { diagnosticsOpen: false } : {}) }),
  consultationMode: false,
  setConsultationMode: (mode) => set({ consultationMode: mode }),

  // Daily reflection
  dailyReflection: "",
  setDailyReflection: (text) => set({ dailyReflection: text }),

  // Capability usage tracking
  capabilityUseCount: {},
  incrementCapabilityUse: (id) => set((s) => ({
    capabilityUseCount: { ...s.capabilityUseCount, [id]: (s.capabilityUseCount[id] || 0) + 1 },
  })),
  activeCapability: null,
  setActiveCapability: (id) => set({ activeCapability: id }),

  // Synced session IDs
  syncedSessionIds: [],
  addSyncedSessionId: (id) => set((s) => ({
    syncedSessionIds: s.syncedSessionIds.includes(id) ? s.syncedSessionIds : [...s.syncedSessionIds, id],
  })),

  // Permission
  permissionPending: null,
  setPermissionPending: (perm) => set({ permissionPending: perm }),
}));

// Hook to initialize store from localStorage
export function useInitializeStore() {
  const { updateSettings, conversations, addConversation } = useAppStore();

  React.useEffect(() => {
    const savedSettings = loadFromLocalStorage<AppSettings>(
      "adam-settings",
      defaultSettings
    );
    updateSettings(savedSettings);

    const savedConversations = loadFromLocalStorage<Conversation[]>(
      "adam-conversations",
      []
    );
    if (savedConversations.length > 0 && conversations.length === 0) {
      savedConversations.forEach((c) => addConversation(c));
    }
  }, [updateSettings, conversations.length, addConversation]);
}

// --- Cognitive Mode Helpers ---

export const cognitiveModes: {
  key: CognitiveMode;
  labelAr: string;
  labelEn: string;
  icon: string;
  color: string;
}[] = [
  { key: "analyst", labelAr: "محلل", labelEn: "Analyst", icon: "🔍", color: "#8b5cf6" },
  { key: "builder", labelAr: "بنّاء", labelEn: "Builder", icon: "🏗️", color: "#f59e0b" },
  { key: "corrector", labelAr: "مصحح", labelEn: "Corrector", icon: "✏️", color: "#ef4444" },
  { key: "engineer", labelAr: "مهندس", labelEn: "Engineer", icon: "⚙️", color: "#06b6d4" },
  { key: "researcher", labelAr: "باحث", labelEn: "Researcher", icon: "🔬", color: "#3b82f6" },
  { key: "communicator", labelAr: "متواصل", labelEn: "Communicator", icon: "💬", color: "#ec4899" },
  { key: "strategist", labelAr: "استراتيجي", labelEn: "Strategist", icon: "🎯", color: "#10b981" },
];

export function getModeInfo(mode: CognitiveMode, lang: "ar" | "en") {
  const m = cognitiveModes.find((c) => c.key === mode);
  return m
    ? { label: lang === "ar" ? m.labelAr : m.labelEn, icon: m.icon, color: m.color }
    : { label: mode, icon: "🤖", color: "#8b5cf6" };
}
