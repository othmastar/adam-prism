/**
 * Adam Prism — Enhanced API Client
 * =================================
 * يستبدل lib/api.ts الموجود عندك.
 *
 * التحسينات:
 * 1. File upload موثوق + error handling واضح
 * 2. LTM (Vector Memory) endpoints
 * 3. MCP server management
 * 4. Enhanced browser (multi-tab)
 * 5. Integration health & stats
 * 6. Retry مع exponential backoff
 * 7. SSE streaming حقيقي
 * 8. Type safety كامل
 *
 * الاستخدام:
 *   import { api, sendChatMessage, uploadFile } from "@/lib/api-enhanced";
 */

import type {
  ChatResponse,
  KnowledgeSearchResult,
} from "./store";

// ============================================================
// Config
// ============================================================

const NEXT_PUBLIC_API_URL = process.env.NEXT_PUBLIC_API_URL;
const FASTAPI_DEFAULT = NEXT_PUBLIC_API_URL || "";

export function getFastApiUrl(): string {
  if (typeof window === "undefined") return "";
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

// ============================================================
// HTTP helpers
// ============================================================

class ApiError extends Error {
  constructor(
    public status: number,
    message: string,
    public detail?: unknown,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T = any>(
  path: string,
  options: RequestInit = {},
  retries = 2,
): Promise<T> {
  const url = `${getFastApiUrl()}${path}`;
  const opts: RequestInit = {
    ...options,
    headers: {
      ...(options.body instanceof FormData
        ? {}
        : { "Content-Type": "application/json" }),
      ...(options.headers || {}),
    },
  };

  let lastErr: Error | null = null;
  for (let attempt = 0; attempt <= retries; attempt++) {
    try {
      const res = await fetch(url, opts);
      if (!res.ok) {
        const errData = await res.json().catch(() => ({} as any));
        throw new ApiError(
          res.status,
          errData?.detail || errData?.error || `HTTP ${res.status}`,
          errData,
        );
      }
      return (await res.json()) as T;
    } catch (e) {
      lastErr = e as Error;
      // retry only on network errors, not 4xx
      if (e instanceof ApiError && e.status >= 400 && e.status < 500) break;
      if (attempt < retries) {
        await new Promise((r) => setTimeout(r, 500 * Math.pow(2, attempt)));
        continue;
      }
    }
  }
  throw lastErr || new Error("Request failed");
}

// ============================================================
// Health & Status
// ============================================================

export async function checkApiHealth(): Promise<{
  connected: boolean;
  status?: string;
  error?: string;
}> {
  try {
    const data = await request<{ status: string }>("/api/status", {
      signal: AbortSignal.timeout(5000),
    });
    return { connected: true, status: JSON.stringify(data) };
  } catch (err) {
    return {
      connected: false,
      error: err instanceof Error ? err.message : "Connection failed",
    };
  }
}

export async function getEngineHealth() {
  return request<any>("/api/engine/health");
}

export async function getDiagnostics() {
  return request<any>("/api/engine/diagnostics");
}

export async function getMetrics(): Promise<string> {
  const url = `${getFastApiUrl()}/metrics`;
  const res = await fetch(url);
  return res.text();
}

// ============================================================
// Chat — REST only (no WebSocket)
// ============================================================

export type ChatContext = {
  history?: Array<{ role: string; content: string }>;
  attachments?: Array<{
    type: "file" | "image" | "audio";
    name: string;
    content?: string;
    url?: string;
  }>;
  memory?: string[];
};

export async function sendChatMessage(
  message: string,
  context: ChatContext = {},
  sessionId?: string,
): Promise<ChatResponse> {
  return request<ChatResponse>("/api/chat", {
    method: "POST",
    body: JSON.stringify({
      message,
      session_id: sessionId,
      context,
      voice: false,
    }),
  });
}

/**
 * Streaming chat عبر SSE (Server-Sent Events)
 * يرجع async iterator من chunks
 */
export async function* streamChatMessage(
  message: string,
  context: ChatContext = {},
  sessionId?: string,
): AsyncGenerator<{ type: string; content?: string; done?: boolean }> {
  const url = `${getFastApiUrl()}/api/chat/stream`;
  const res = await fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      message,
      session_id: sessionId,
      context,
    }),
  });

  if (!res.ok || !res.body) {
    throw new Error(`Stream failed: HTTP ${res.status}`);
  }

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });
    const lines = buffer.split("\n\n");
    buffer = lines.pop() || "";
    for (const line of lines) {
      if (line.startsWith("data: ")) {
        try {
          const data = JSON.parse(line.slice(6));
          yield data;
        } catch {
          // skip malformed
        }
      }
    }
  }
}

// ============================================================
// File Upload — موثوق + error handling واضح
// ============================================================

export type UploadResult = {
  filename: string;
  original_name: string;
  url: string;
  content_type: string;
  size: number;
  text_content: string;
  type?: "text" | "image" | "binary" | "error";
  error?: string;
};

export async function uploadFile(file: File): Promise<UploadResult | null> {
  const url = `${getFastApiUrl()}/api/chat/upload`;
  const form = new FormData();
  form.append("file", file);

  try {
    const res = await fetch(url, { method: "POST", body: form });
    if (!res.ok) {
      const errData = await res.json().catch(() => ({} as any));
      console.error("Upload failed:", res.status, errData);
      return null;
    }
    return (await res.json()) as UploadResult;
  } catch (e) {
    console.error("Upload error:", e);
    return null;
  }
}

/**
 * رفع عدة ملفات دفعة واحدة
 */
export async function uploadFiles(
  files: File[],
): Promise<{ successes: UploadResult[]; failures: { file: string; error: string }[] }> {
  const successes: UploadResult[] = [];
  const failures: { file: string; error: string }[] = [];

  const results = await Promise.allSettled(files.map((f) => uploadFile(f)));
  results.forEach((r, i) => {
    if (r.status === "fulfilled" && r.value) {
      successes.push(r.value);
    } else {
      failures.push({
        file: files[i].name,
        error: r.status === "rejected" ? String(r.reason) : "Upload returned null",
      });
    }
  });

  return { successes, failures };
}

/**
 * يبني payload message مع ملف مرفق
 * يستخدم في chat-interface.tsx
 */
export function buildMessageWithFile(
  userMessage: string,
  fileName: string,
  fileContent: string,
): string {
  if (!fileContent) return userMessage;
  const header = userMessage.trim()
    ? `${userMessage}\n\n`
    : `Analyze this file (${fileName}):\n`;
  return `${header}--- FILE: ${fileName} ---\n${fileContent}\n--- END FILE ---`;
}

// ============================================================
// Sessions
// ============================================================

export type Session = {
  session_id: string;
  title: string | null;
  model: string | null;
  created_at: string;
  last_active_at: string;
};

export type SessionMessage = {
  role: string;
  content: string;
  timestamp: string;
};

export async function fetchSessions(limit = 50): Promise<Session[]> {
  const data = await request<{ sessions: Session[] }>(
    `/api/chat/sessions?limit=${limit}`,
  );
  return data.sessions || [];
}

export async function fetchSession(sessionId: string): Promise<{
  messages: SessionMessage[];
  session: Session;
}> {
  return request(`/api/chat/sessions/${sessionId}`);
}

export async function createSession(title?: string): Promise<string> {
  // إنشاء session عبر إرسال أول رسالة (الـ backend بينشئها تلقائياً)
  // أو نستخدم endpoint مباشر لو موجود
  try {
    const data = await request<{ session_id: string }>("/api/chat/sessions", {
      method: "POST",
      body: JSON.stringify({ title: title || "محادثة جديدة" }),
    });
    return data.session_id;
  } catch {
    // fallback: الـ backend بينشئها عند أول chat
    return "";
  }
}

export async function deleteSessionOnServer(sessionId: string): Promise<boolean> {
  try {
    await request(`/api/chat/sessions/${sessionId}`, { method: "DELETE" });
    return true;
  } catch {
    return false;
  }
}

export async function syncSessionMessages(
  sessionId: string,
  messages: Array<{ role: string; content: string }>,
): Promise<number> {
  const data = await request<{ synced: number }>(
    `/api/chat/sessions/${sessionId}/sync`,
    {
      method: "POST",
      body: JSON.stringify(messages),
    },
  );
  return data.synced || 0;
}

export async function addMessageToSession(
  sessionId: string,
  role: string,
  content: string,
): Promise<number | null> {
  const data = await request<{ id: number }>(
    `/api/chat/sessions/${sessionId}/messages`,
    {
      method: "POST",
      body: JSON.stringify({ role, content }),
    },
  );
  return data.id ?? null;
}

// ============================================================
// Memory — Short-term (الـ store الموجود)
// ============================================================

export async function storeMemory(
  content: string,
  priority = 3,
  tags = "",
): Promise<{ success: boolean; id?: number }> {
  return request("/api/memory/store", {
    method: "POST",
    body: JSON.stringify({ content, priority, tags }),
  });
}

export async function recallMemory(
  query: string,
  limit = 10,
): Promise<{ results: any[]; total: number }> {
  return request(
    `/api/memory/recall?query=${encodeURIComponent(query)}&limit=${limit}`,
  );
}

export async function getMemoryStats(): Promise<any> {
  return request("/api/memory/stats");
}

// ============================================================
// LTM — Long-Term Memory (Vector embeddings)
// ============================================================

export type LTMResult = {
  id: number;
  content: string;
  type: string;
  priority: number;
  tags: string[];
  score: number;
  bm25_score: number;
  vector_score: number;
  access_count: number;
  created_at: string;
};

export async function storeLTM(
  content: string,
  type = "semantic",
  priority = 3,
  tags: string[] = [],
): Promise<{ success: boolean; id?: number }> {
  return request("/api/ltm/store", {
    method: "POST",
    body: JSON.stringify({ content, type, priority, tags }),
  });
}

export async function searchLTM(
  query: string,
  topK = 5,
  type?: string,
): Promise<{ results: LTMResult[]; total: number }> {
  const params = new URLSearchParams({
    query,
    top_k: String(topK),
  });
  if (type) params.set("type", type);
  return request(`/api/ltm/search?${params}`);
}

export async function recallLTMContext(
  query: string,
  maxMemories = 5,
): Promise<{ context: string; length: number }> {
  return request(
    `/api/ltm/recall?query=${encodeURIComponent(query)}&max_memories=${maxMemories}`,
  );
}

export async function getLTMStats(): Promise<any> {
  return request("/api/ltm/stats");
}

export async function getLTMHealth(): Promise<any> {
  return request("/api/ltm/health");
}

export async function deleteLTM(memoryId: number): Promise<{ deleted: boolean }> {
  return request(`/api/ltm/memories/${memoryId}`, { method: "DELETE" });
}

// ============================================================
// Knowledge
// ============================================================

export async function searchKnowledge(
  query: string,
  collection = "knowledge",
  topK = 5,
): Promise<KnowledgeSearchResult[]> {
  const data = await request<{ results: KnowledgeSearchResult[] }>(
    "/api/knowledge/search",
    {
      method: "POST",
      body: JSON.stringify({ query, collection, top_k: topK }),
    },
  );
  return data.results || [];
}

export async function addKnowledge(
  texts: string[],
  collection = "knowledge",
  metadata: Record<string, unknown> = {},
): Promise<any> {
  return request("/api/knowledge/add", {
    method: "POST",
    body: JSON.stringify({ texts, collection, metadata }),
  });
}

export async function uploadToKnowledge(
  file: File,
  collection = "knowledge",
): Promise<any> {
  const url = `${getFastApiUrl()}/api/knowledge/upload?collection=${collection}`;
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(url, { method: "POST", body: form });
  if (!res.ok) throw new Error(`Upload failed: HTTP ${res.status}`);
  return res.json();
}

export async function getKnowledgeCollections(): Promise<any[]> {
  const data = await request<{ collections: any[] }>(
    "/api/knowledge/collections",
  );
  return data.collections || [];
}

export async function getRecentKnowledge(limit = 10): Promise<any[]> {
  const data = await request<{ recent: any[] }>(
    `/api/knowledge/recent?limit=${limit}`,
  );
  return data.recent || [];
}

// ============================================================
// Tools
// ============================================================

export type ToolInfo = {
  name: string;
  description: string;
  parameters: Record<string, any>;
  required?: string[];
};

export async function getToolsManifest(): Promise<{
  total: number;
  tools: Record<string, ToolInfo>;
}> {
  return request("/api/tools/manifest");
}

export async function executeTool(
  name: string,
  arguments_: Record<string, unknown>,
): Promise<{
  success: boolean;
  result: unknown;
  error: string | null;
  latency_ms: number;
}> {
  return request("/api/tools/action", {
    method: "POST",
    body: JSON.stringify({ name, arguments: arguments_ }),
  });
}

// ============================================================
// Browser (Enhanced multi-tab Playwright)
// ============================================================

export type BrowserPage = {
  id: string;
  url: string;
  title: string;
  age_seconds?: number;
};

export async function browserOpen(
  url: string,
): Promise<{ success: boolean; page_id?: string; error?: string }> {
  return request("/api/browser/open", {
    method: "POST",
    body: JSON.stringify({ url }),
  });
}

export async function browserListPages(): Promise<{
  pages: BrowserPage[];
  total: number;
}> {
  return request("/api/browser/pages");
}

export async function browserRead(
  pageId: string,
  selector?: string,
): Promise<{ success: boolean; text?: string; error?: string }> {
  const params = new URLSearchParams();
  if (selector) params.set("selector", selector);
  return request(`/api/browser/${pageId}/read?${params}`);
}

export async function browserClick(
  pageId: string,
  selector: string,
): Promise<{ success: boolean; error?: string }> {
  return request(`/api/browser/${pageId}/click`, {
    method: "POST",
    body: JSON.stringify({ selector }),
  });
}

export async function browserType(
  pageId: string,
  selector: string,
  text: string,
): Promise<{ success: boolean; error?: string }> {
  return request(`/api/browser/${pageId}/type`, {
    method: "POST",
    body: JSON.stringify({ selector, text }),
  });
}

export async function browserScreenshot(
  pageId: string,
  fullPage = false,
): Promise<{ success: boolean; base64?: string; size_bytes?: number; error?: string }> {
  return request(`/api/browser/${pageId}/screenshot`, {
    method: "POST",
    body: JSON.stringify({ full_page: fullPage }),
  });
}

export async function browserScroll(
  pageId: string,
  x = 0,
  y = 500,
): Promise<{ success: boolean; error?: string }> {
  return request(`/api/browser/${pageId}/scroll`, {
    method: "POST",
    body: JSON.stringify({ x, y }),
  });
}

export async function browserExecute(
  pageId: string,
  script: string,
): Promise<{ success: boolean; result?: unknown; error?: string }> {
  return request(`/api/browser/${pageId}/execute`, {
    method: "POST",
    body: JSON.stringify({ script }),
  });
}

export async function browserClose(pageId: string): Promise<{ closed: boolean }> {
  return request(`/api/browser/${pageId}`, { method: "DELETE" });
}

export async function browserStats(): Promise<any> {
  return request("/api/browser/stats");
}

// ============================================================
// MCP — Model Context Protocol
// ============================================================

export type MCPServer = {
  name: string;
  command: string;
  args: string[];
  connected: boolean;
  tools_count: number;
  tools: string[];
};

export type MCPToolInfo = {
  name: string;
  short_name: string;
  description: string;
  input_schema: Record<string, any>;
  server: string;
};

export async function addMCPServer(
  name: string,
  command: string,
  args: string[],
  env?: Record<string, string>,
): Promise<{ success: boolean; name: string }> {
  return request("/api/mcp/add-server-enhanced", {
    method: "POST",
    body: JSON.stringify({ name, command, args, env }),
  });
}

export async function listMCPServers(): Promise<{ servers: MCPServer[] }> {
  return request("/api/mcp/servers-enhanced");
}

export async function listMCPTools(): Promise<{ tools: MCPToolInfo[] }> {
  return request("/api/mcp/tools-enhanced");
}

export async function removeMCPServer(
  name: string,
): Promise<{ success: boolean; name: string }> {
  return request(`/api/mcp/servers-enhanced/${name}`, { method: "DELETE" });
}

// ============================================================
// Integration Layer (health & stats)
// ============================================================

export async function getIntegrationHealth(): Promise<{
  compressor: boolean;
  vector_memory: { db_connected: boolean; embedding_available: boolean };
  browser: boolean;
  mcp: { available: boolean; servers_count: number; tools_count: number };
}> {
  return request("/api/integration/health");
}

export async function getIntegrationStats(): Promise<{
  vector_memory: any;
  browser: any;
  mcp: any;
}> {
  return request("/api/integration/stats");
}

// ============================================================
// Ollama
// ============================================================

export async function getOllamaModels(): Promise<string[]> {
  const data = await request<{ models: Array<{ name: string }>; total: number }>(
    "/api/ollama/models",
  );
  return (data.models || []).map((m) => m.name);
}

export async function selectOllamaModel(model: string): Promise<boolean> {
  const data = await request<{ success: boolean }>(
    "/api/ollama/select",
    {
      method: "POST",
      body: JSON.stringify({ model }),
    },
  );
  return data.success || false;
}

// ============================================================
// Settings
// ============================================================

export async function updateSettings(
  settings: Record<string, unknown>,
): Promise<{ success: boolean }> {
  return request("/api/settings/update", {
    method: "POST",
    body: JSON.stringify({ settings }),
  });
}

// ============================================================
// Auth
// ============================================================

export async function verifyAuth(
  token?: string,
  apiKey?: string,
): Promise<{ valid: boolean; user?: string }> {
  return request("/api/auth/verify", {
    method: "POST",
    body: JSON.stringify({ token, api_key: apiKey }),
  });
}

// ============================================================
// Voice
// ============================================================

export async function sendAudio(
  audioBlob: Blob,
  sessionId?: string,
): Promise<{ text: string; audioUrl?: string; duration_ms: number }> {
  const url = `${getFastApiUrl()}/api/voice/chat`;
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");
  if (sessionId) formData.append("session_id", sessionId);

  const res = await fetch(url, { method: "POST", body: formData });
  if (!res.ok) {
    const errData = await res.json().catch(() => ({} as any));
    throw new Error(errData.error || `HTTP ${res.status}`);
  }
  return res.json();
}

export async function transcribeAudio(audioBlob: Blob): Promise<string> {
  const url = `${getFastApiUrl()}/api/voice/transcribe`;
  const formData = new FormData();
  formData.append("audio", audioBlob, "recording.webm");

  const res = await fetch(url, { method: "POST", body: formData });
  if (!res.ok) {
    throw new Error(`HTTP ${res.status}`);
  }
  const data = await res.json();
  return data.transcript || "";
}

// ============================================================
// Engine pipeline & heal
// ============================================================

export async function triggerHeal(): Promise<any> {
  return request("/api/engine/heal", { method: "POST" });
}

export async function getPipelineLog(limit = 50): Promise<any> {
  return request(`/api/engine/pipeline-log?limit=${limit}`);
}

// ============================================================
// Subagents
// ============================================================

export async function listSubagents(): Promise<any[]> {
  const data = await request<{ subagents: any[] }>("/api/subagents");
  return data.subagents || [];
}

export async function spawnSubagent(
  name: string,
  config: Record<string, unknown> = {},
): Promise<any> {
  return request("/api/subagents/spawn", {
    method: "POST",
    body: JSON.stringify({ name, ...config }),
  });
}

// ============================================================
// Skills & Plugins
// ============================================================

export async function listSkills(): Promise<any[]> {
  const data = await request<{ skills: any[] }>("/api/skills/list");
  return data.skills || [];
}

export async function loadSkill(skillName: string): Promise<any> {
  return request("/api/skills/load", {
    method: "POST",
    body: JSON.stringify({ skill_name: skillName }),
  });
}

export async function listPlugins(): Promise<any[]> {
  const data = await request<{ plugins: any[] }>("/api/plugins");
  return data.plugins || [];
}

// ============================================================
// Notebook
// ============================================================

export async function getNotebookEntry(date: string): Promise<any> {
  return request(`/api/notebook/${date}`);
}

export async function getNotebookStats(): Promise<any> {
  return request("/api/notebook/stats");
}

// ============================================================
// Scheduler
// ============================================================

export async function listSchedulerJobs(): Promise<any[]> {
  const data = await request<{ jobs: any[] }>("/api/scheduler/jobs");
  return data.jobs || [];
}

export async function addCronJob(
  id: string,
  schedule: string,
  action: string,
  params: Record<string, unknown> = {},
): Promise<any> {
  return request("/api/scheduler/cron", {
    method: "POST",
    body: JSON.stringify({ id, schedule, action, params }),
  });
}

// ============================================================
// Security
// ============================================================

export async function getSecurityStats(): Promise<any> {
  return request("/api/security/stats");
}

// ============================================================
// Export default api object (للـ backward compat)
// ============================================================

export const api = {
  // Chat
  sendMessage: sendChatMessage,
  streamMessage: streamChatMessage,
  uploadFile,
  uploadFiles,
  buildMessageWithFile,

  // Sessions
  fetchSessions,
  fetchSession,
  createSession,
  deleteSession: deleteSessionOnServer,
  syncMessages: syncSessionMessages,
  addMessage: addMessageToSession,

  // Memory
  storeMemory,
  recallMemory,
  getMemoryStats,

  // LTM
  storeLTM,
  searchLTM,
  recallLTMContext,
  getLTMStats,
  getLTMHealth,
  deleteLTM,

  // Knowledge
  searchKnowledge,
  addKnowledge,
  uploadToKnowledge,
  getKnowledgeCollections,
  getRecentKnowledge,

  // Tools
  getToolsManifest,
  executeTool,

  // Browser
  browserOpen,
  browserListPages,
  browserRead,
  browserClick,
  browserType,
  browserScreenshot,
  browserScroll,
  browserExecute,
  browserClose,
  browserStats,

  // MCP
  addMCPServer,
  listMCPServers,
  listMCPTools,
  removeMCPServer,

  // Integration
  getIntegrationHealth,
  getIntegrationStats,

  // Ollama
  getOllamaModels,
  selectOllamaModel,

  // Settings
  updateSettings,

  // Auth
  verifyAuth,

  // Voice
  sendAudio,
  transcribeAudio,

  // Engine
  checkHealth: checkApiHealth,
  getEngineHealth,
  getDiagnostics,
  getMetrics,
  triggerHeal,
  getPipelineLog,

  // Subagents
  listSubagents,
  spawnSubagent,

  // Skills & Plugins
  listSkills,
  loadSkill,
  listPlugins,

  // Notebook
  getNotebookEntry,
  getNotebookStats,

  // Scheduler
  listSchedulerJobs,
  addCronJob,

  // Security
  getSecurityStats,
};

export default api;
