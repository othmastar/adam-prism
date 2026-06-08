import React from "react";
import { useAppStore, SystemHealth, ProcessingStep } from "./store";

const FASTAPI_DEFAULT = "http://localhost:8002";

export function getFastApiUrl(): string {
  if (typeof window === "undefined") return FASTAPI_DEFAULT;
  try {
    const stored = localStorage.getItem("adam-settings");
    if (stored) {
      const settings = JSON.parse(stored);
      return settings.fastApiUrl || FASTAPI_DEFAULT;
    }
  } catch {
    // ignore
  }
  return FASTAPI_DEFAULT;
}

// --- Health Check ---

export async function checkApiHealth(): Promise<{
  connected: boolean;
  status?: string;
  error?: string;
}> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/status`, {
      method: "GET",
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      return { connected: true, status: JSON.stringify(data) };
    }
    return { connected: false, error: `HTTP ${res.status}` };
  } catch (err) {
    return {
      connected: false,
      error: err instanceof Error ? err.message : "Connection failed",
    };
  }
}

// --- Chat ---

export type ChatResponse = {
  response: string;
  mode: string;
  intent: Record<string, unknown>;
  knowledge_used: number;
  cycle: number;
  duration_ms: number;
  audio_url?: string | null;
  permission_pending?: {
    action: string;
    category: string;
    level: string;
    reason: string;
  } | null;
};

export async function sendChatMessage(
  message: string,
  context: Record<string, unknown> = {}
): Promise<ChatResponse> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/chat`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ message, context, voice: true }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

// --- Knowledge ---

export type KnowledgeSearchResult = {
  id: string;
  content: string;
  score: number;
  metadata?: Record<string, unknown>;
  collection?: string;
};

export async function searchKnowledge(
  query: string,
  collection: string = "knowledge",
  topK: number = 5
): Promise<KnowledgeSearchResult[]> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/knowledge/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, collection, top_k: topK }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  const data = await res.json();
  return data.results || data || [];
}

// --- Ollama Models ---

export async function fetchOllamaModels(): Promise<string[]> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/ollama/models`, {
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.models || [];
}

export async function selectOllamaModel(model: string): Promise<boolean> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/ollama/select`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ model }),
  });
  return res.ok;
}

// --- Skills ---

export async function fetchSkillsList(): Promise<{ name: string; description: string; path: string }[]> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/skills/list`, {
    signal: AbortSignal.timeout(10000),
  });
  if (!res.ok) return [];
  const data = await res.json();
  return data.skills || [];
}

export async function loadSkill(path: string): Promise<{ success: boolean; result?: string }> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/skills/load`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ path }),
  });
  const data = await res.json();
  return data;
}

// --- Knowledge Add ---

export async function addKnowledge(
  text: string,
  collection: string = "knowledge",
  metadata?: Record<string, unknown>
): Promise<{ success: boolean; collection: string; id?: number }> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/knowledge/add`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, collection, metadata }),
  });
  const data = await res.json();
  return data;
}

export async function uploadKnowledgeFile(
  file: File,
  collection: string = "knowledge"
): Promise<{ success: boolean; filename: string; collection: string; chunks: number; total_chars: number }> {
  const url = getFastApiUrl();
  const form = new FormData();
  form.append("file", file);
  form.append("collection", collection);
  const res = await fetch(`${url}/api/knowledge/upload`, {
    method: "POST",
    body: form,
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: "Upload failed" }));
    throw new Error(err.detail || `HTTP ${res.status}`);
  }
  return res.json();
}

// --- Notebook ---

export async function fetchNotebook(date: string): Promise<unknown> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/notebook/${date}`);

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function fetchNotebookStats(): Promise<unknown> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/notebook/stats`);

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

// --- Memory ---

export async function fetchMemoryStats(): Promise<unknown> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/memory/stats`);

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

// --- Security ---

export async function fetchSecurityStats(): Promise<unknown> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/security/stats`);

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

// --- Pipeline / Summarize ---

export async function summarizeDocument(
  text: string,
  source: string = "upload",
  title: string = "Untitled"
): Promise<unknown> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/pipeline/summarize`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, source, title }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

// --- Tools ---

export async function executeToolAction(
  action: Record<string, unknown>
): Promise<unknown> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/tools/action`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ action }),
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

// --- Chat History (REST) ---

export type ServerSession = {
  id: string;
  title: string;
  created_at: number;
  updated_at: number;
  messages?: ServerMessage[];
};

export type ServerMessage = {
  id: string;
  session_id: string;
  role: "user" | "assistant" | "system";
  content: string;
  mode?: string;
  metadata?: Record<string, unknown>;
  timestamp: number;
};

export async function fetchSessions(
  limit = 50,
  offset = 0
): Promise<ServerSession[]> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(
      `${url}/api/chat/sessions?limit=${limit}&offset=${offset}`,
      { signal: AbortSignal.timeout(5000) }
    );
    if (res.ok) {
      const data = await res.json();
      return data.sessions || [];
    }
    return [];
  } catch {
    return [];
  }
}

export async function fetchSession(
  sessionId: string
): Promise<ServerSession | null> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/chat/sessions/${sessionId}`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) return res.json();
    return null;
  } catch {
    return null;
  }
}

export async function createSession(
  title = "New Conversation",
  firstMessage?: string
): Promise<ServerSession | null> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/chat/sessions`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title, first_message: firstMessage }),
    });
    if (res.ok) return res.json();
    return null;
  } catch {
    return null;
  }
}

export async function updateSessionTitle(
  sessionId: string,
  title: string
): Promise<boolean> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/chat/sessions/${sessionId}`, {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ title }),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function deleteSessionOnServer(
  sessionId: string
): Promise<boolean> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/chat/sessions/${sessionId}`, {
      method: "DELETE",
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function addMessageToSession(
  sessionId: string,
  role: string,
  content: string,
  mode?: string,
  metadata?: Record<string, unknown>
): Promise<ServerMessage | null> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/chat/sessions/${sessionId}/messages`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ role, content, mode, metadata }),
    });
    if (res.ok) return res.json();
    return null;
  } catch {
    return null;
  }
}

export async function syncSessionMessages(
  sessionId: string,
  messages: { role: string; content: string; mode?: string; metadata?: Record<string, unknown> }[]
): Promise<boolean> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/chat/sessions/${sessionId}/sync`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(messages),
    });
    return res.ok;
  } catch {
    return false;
  }
}

export async function searchChatHistory(
  query: string,
  limit = 20
): Promise<{ results: Record<string, unknown>[]; count: number }> {
  const url = getFastApiUrl();
  const res = await fetch(`${url}/api/chat/search`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ query, limit }),
  });
  if (!res.ok) return { results: [], count: 0 };
  return res.json();
}

export async function uploadFile(
  file: File
): Promise<{ filename: string; original_name: string; url: string; content_type: string; size: number } | null> {
  const url = getFastApiUrl();
  const form = new FormData();
  form.append("file", file);
  try {
    const res = await fetch(`${url}/api/chat/upload`, {
      method: "POST",
      body: form,
    });
    if (!res.ok) return null;
    return res.json();
  } catch {
    return null;
  }
}

// --- Voice ---

export type VoiceChatResponse = {
  text: string;
  audioUrl?: string;
  duration_ms: number;
};

export async function sendAudio(
  audioBlob: Blob,
  sessionId?: string
): Promise<VoiceChatResponse> {
  const url = getFastApiUrl();
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");
  if (sessionId) formData.append("session_id", sessionId);

  const res = await fetch(`${url}/api/voice/chat`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  return res.json();
}

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const url = getFastApiUrl();
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");

  const res = await fetch(`${url}/api/voice/transcribe`, {
    method: "POST",
    body: formData,
  });

  if (!res.ok) {
    const errData = await res.json().catch(() => ({ error: "Unknown error" }));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }

  const data = await res.json();
  return data.text || "";
}

// --- Ollama (direct) ---

export async function checkOllamaHealth(
  ollamaUrl: string
): Promise<{ connected: boolean; models: string[] }> {
  try {
    const res = await fetch(`${ollamaUrl}/api/tags`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      const models = (data.models || []).map((m: { name: string }) => m.name);
      return { connected: true, models };
    }
    return { connected: false, models: [] };
  } catch {
    return { connected: false, models: [] };
  }
}

// --- System Health ---

export async function fetchSystemHealth(): Promise<SystemHealth | null> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/engine/health`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) return res.json();
    return null;
  } catch {
    return null;
  }
}

// --- Pipeline Log ---

export async function fetchPipelineLog(limit = 50): Promise<ProcessingStep[]> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/engine/pipeline-log?limit=${limit}`, {
      signal: AbortSignal.timeout(5000),
    });
    if (res.ok) {
      const data = await res.json();
      return data.steps || [];
    }
    return [];
  } catch {
    return [];
  }
}

// --- SSE Stream Hook ---

export function useEngineStream() {
  const { addProcessingStep, clearProcessingSteps } = useAppStore();

  React.useEffect(() => {
    const url = getFastApiUrl();
    const eventSource = new EventSource(`${url}/api/engine/stream`);

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        if (data.type === "keepalive") return;
        addProcessingStep(data as ProcessingStep);
      } catch {
        // ignore
      }
    };

    eventSource.onerror = () => {
      // Will auto-reconnect
    };

    return () => {
      eventSource.close();
      clearProcessingSteps();
    };
  }, [addProcessingStep, clearProcessingSteps]);
}

// --- Diagnostics API ---

export async function fetchDiagnostics(): Promise<any> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/engine/diagnostics`, {
      signal: AbortSignal.timeout(8000),
    });
    if (res.ok) return res.json();
    return null;
  } catch {
    return null;
  }
}

export async function triggerHeal(): Promise<any> {
  try {
    const res = await fetch(`${getFastApiUrl()}/api/engine/heal`, {
      signal: AbortSignal.timeout(10000),
    });
    if (res.ok) return res.json();
    return null;
  } catch {
    return null;
  }
}

export async function respondPermission(approve: boolean, level?: string): Promise<any> {
  const res = await fetch(`${getFastApiUrl()}/api/permissions/respond`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ approve, level: level || "once" }),
  });
  return res.json();
}

// --- Channels ---

export type ChannelInfo = {
  name: string;
  running: boolean;
  webhook: boolean;
  requires?: string[];
};

export async function fetchChannels(): Promise<Record<string, ChannelInfo>> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/channels`, { signal: AbortSignal.timeout(5000) });
    if (res.ok) {
      const data = await res.json();
      return data.channels || {};
    }
  } catch { /* ignore */ }
  return {};
}

export async function fetchChannelStatus(name: string): Promise<ChannelInfo | null> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/channels/${name}`, { signal: AbortSignal.timeout(5000) });
    if (res.ok) return res.json();
  } catch { /* ignore */ }
  return null;
}

export async function toggleChannel(name: string, enable: boolean): Promise<boolean> {
  const url = getFastApiUrl();
  try {
    const res = await fetch(`${url}/api/channels/${name}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ enabled: enable }),
    });
    return res.ok;
  } catch { return false; }
}

export function useApiHealthCheck() {
  const { setApiConnected, setOllamaConnected, setOllamaModels, settings, setSystemHealth, setIssueCount, diagnosticsOpen } =
    useAppStore();

  React.useEffect(() => {
    let interval: ReturnType<typeof setInterval>;

    const check = async () => {
      // Check FastAPI
      const apiResult = await checkApiHealth();
      setApiConnected(apiResult.connected);

      // Check Ollama
      const ollamaResult = await checkOllamaHealth(settings.ollamaUrl);
      setOllamaConnected(ollamaResult.connected);
      if (ollamaResult.models.length > 0) {
        setOllamaModels(ollamaResult.models);
      }

      // System health
      const health = await fetchSystemHealth();
      if (health) setSystemHealth(health);

      // Auto-diagnostics + auto-heal كل 60 ثانية (لو المودال مش مفتوح)
      if (!diagnosticsOpen) {
        const diag = await fetchDiagnostics();
        if (diag?.summary?.failed > 0) {
          setIssueCount(diag.summary.failed);
          // Auto-heal للمشاكل
          await triggerHeal();
        } else {
          setIssueCount(0);
        }
      }
    };

    check();
    interval = setInterval(check, 15000);

    return () => clearInterval(interval);
  }, [settings.ollamaUrl, settings.fastApiUrl, setApiConnected, setOllamaConnected, setOllamaModels, setSystemHealth, setIssueCount, diagnosticsOpen]);
}

export function getWebSocketUrl(): string {
  const httpUrl = getFastApiUrl();
  return httpUrl.replace(/^http/, "ws") + "/ws/chat";
}

type WsCallbacks = {
  onMessage: (data: Record<string, unknown>) => void;
  onError?: (err: Event) => void;
  onDisconnect?: () => void;
};

export function useChatWebSocket(callbacks: WsCallbacks) {
  const wsRef = React.useRef<WebSocket | null>(null);
  const reconnectTimerRef = React.useRef<ReturnType<typeof setTimeout> | null>(null);
  const cbRef = React.useRef(callbacks);
  cbRef.current = callbacks;
  const [connected, setConnected] = React.useState(false);

  const connect = React.useCallback(() => {
    if (wsRef.current?.readyState === WebSocket.OPEN) return;
    try {
      const ws = new WebSocket(getWebSocketUrl());
      ws.onopen = () => setConnected(true);
      ws.onclose = () => {
        setConnected(false);
        cbRef.current.onDisconnect?.();
        reconnectTimerRef.current = setTimeout(connect, 3000);
      };
      ws.onerror = (e) => cbRef.current.onError?.(e);
      ws.onmessage = (e) => {
        try {
          const data = JSON.parse(e.data);
          cbRef.current.onMessage(data);
        } catch { /* ignore invalid JSON */ }
      };
      wsRef.current = ws;
    } catch { /* ignore */ }
  }, []);

  const disconnect = React.useCallback(() => {
    if (reconnectTimerRef.current) clearTimeout(reconnectTimerRef.current);
    wsRef.current?.close();
    wsRef.current = null;
    setConnected(false);
  }, []);

  const send = React.useCallback((message: string) => {
    if (wsRef.current?.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ message, voice: true }));
      return true;
    }
    return false;
  }, []);

  React.useEffect(() => {
    connect();
    return () => disconnect();
  }, [connect, disconnect]);

  return { connected, connect, disconnect, send };
}
