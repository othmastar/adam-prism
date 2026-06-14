/**
 * [PHASE3] Adam Prism Mobile — API client
 * React Native/Expo compatible HTTP client.
 */
import * as SecureStore from "expo-secure-store"
import Constants from "expo-constants"

const API_URL = (Constants.expoConfig?.extra as any)?.apiUrl || "http://localhost:8000"

export interface ChatMessage {
  role: "user" | "assistant" | "system"
  content: string
  mode?: string
}

export interface ChatResponse {
  response: string
  mode: string
  intent?: any
  knowledge_used: number
  tool_calls_made: number
  tools_used: string[]
  tool_records: any[]
  errors: string[]
  cycle: number
  duration_ms?: number
  audio_url?: string
}

export interface AuthTokens {
  access_token: string
  refresh_token: string
  user_id: string
  email?: string
}

class AdamPrismAPI {
  private baseURL: string
  private accessToken: string | null = null

  constructor(baseURL: string = API_URL) {
    this.baseURL = baseURL
    this.loadToken()
  }

  private async loadToken() {
    try {
      this.accessToken = await SecureStore.getItemAsync("adam_access_token")
    } catch {
      // SecureStore not available (e.g., web)
    }
  }

  async setTokens(tokens: AuthTokens) {
    this.accessToken = tokens.access_token
    try {
      await SecureStore.setItemAsync("adam_access_token", tokens.access_token)
      await SecureStore.setItemAsync("adam_refresh_token", tokens.refresh_token)
    } catch {
      // ignore
    }
  }

  async clearTokens() {
    this.accessToken = null
    try {
      await SecureStore.deleteItemAsync("adam_access_token")
      await SecureStore.deleteItemAsync("adam_refresh_token")
    } catch {
      // ignore
    }
  }

  private async request<T>(path: string, options: RequestInit = {}): Promise<T> {
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    }
    if (this.accessToken) {
      headers["Authorization"] = `Bearer ${this.accessToken}`
    }
    const url = `${this.baseURL}${path}`
    const res = await fetch(url, { ...options, headers })
    if (!res.ok) {
      const body = await res.text()
      throw new Error(`HTTP ${res.status}: ${body}`)
    }
    return res.json() as Promise<T>
  }

  // ── Health ──
  async health() {
    return this.request<{ status: string }>("/healthz/live")
  }

  // ── Auth ──
  async login(usernameOrEmail: string, password: string): Promise<AuthTokens> {
    const data = await this.request<AuthTokens>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify({ username_or_email: usernameOrEmail, password }),
    })
    await this.setTokens(data)
    return data
  }

  async register(email: string, username: string, password: string): Promise<AuthTokens> {
    const data = await this.request<AuthTokens>("/api/auth/register", {
      method: "POST",
      body: JSON.stringify({ email, username, password }),
    })
    await this.setTokens(data)
    return data
  }

  // ── Chat ──
  async chat(message: string, context?: any): Promise<ChatResponse> {
    return this.request<ChatResponse>("/api/chat", {
      method: "POST",
      body: JSON.stringify({ message, context: context ?? {}, voice: false }),
    })
  }

  // ── Sessions ──
  async listSessions() {
    return this.request<{ sessions: any[]; total: number }>("/api/chat/sessions")
  }

  async createSession(title: string) {
    return this.request<{ id: string; title: string }>("/api/chat/sessions", {
      method: "POST",
      body: JSON.stringify({ title }),
    })
  }

  // ── Knowledge ──
  async searchKnowledge(query: string, topK = 5) {
    return this.request<{ results: any[]; count: number }>("/api/knowledge/search", {
      method: "POST",
      body: JSON.stringify({ query, top_k: topK }),
    })
  }
}

export const api = new AdamPrismAPI()
export default api
